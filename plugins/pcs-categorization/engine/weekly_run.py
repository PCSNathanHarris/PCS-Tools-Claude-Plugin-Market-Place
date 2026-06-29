"""
Weekly run — STEP 1 (read-only): for one store, refresh the category tree, detect newly-added
categories vs the last run, and gather all eligible `New Item V2` non-kit products for Claude to
classify. Writes nothing to Shopify. Outputs to the persistent data dir.

  python weekly_run.py --store the-milwaukee-store [--max-items N]

Outputs (data_dir/runs/<week>/<slug>/):
  tree-diff.md     new categories since last run
  candidates.json  eligible products (vendor/title/description) + category vocabulary + anchors

Then Claude (the SKILL) classifies -> writes decisions.json -> apply_run.py builds the tag batches.
"""

import argparse
import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from config import data_dir, get_store_credentials
from shopify_read_client import ShopifyReadClient

try:
    from build_category_map import STORE_SLUG
except Exception:
    STORE_SLUG = {}

HERE = Path(__file__).resolve().parent
PROJECT = data_dir()

# store-specific "skip categorization" tags (e.g. JTB's box-with-tools bundles)
STORE_SKIP = {"knaack-store": {"remove"}}

# store-specific "skip categorization" by product VENDOR (lowercased). weather-guard-store rebranded
# to Spyder Supply and is Spyder-only front-facing — legacy Weatherguard / truck-box items don't need
# categorizing and are skipped entirely (not even sent to review), like JTB's box-with-tools bundles.
STORE_SKIP_VENDORS = {"weather-guard-store": {"weatherguard"}}

# Stores with BOTH a "Shop by Category" AND a "Shop by Brand" tree. These are TWO SEPARATE tagging
# structures: a product gets its Shop-by-Category tags AND its Shop-by-Brand tags. For these stores
# the brand tree is emitted as its own selectable vocabulary and brand tags are NOT stripped (they are
# intended). MTS is the only known full dual-tree store. NOTE: knaack-store (JTB) has branded *sections*
# but not a full Shop-by-Brand tree — it is NOT dual-tree here; its brand-kind nodes are folded into the
# ordinary category vocabulary as additional targets, not a separate brand pick.
DUAL_TREE_STORES = {"toolup-my-tool-store"}

# Operational / workflow tags that some collections are built on but are NOT merchandising categories.
# They are stripped from every node closure + the vocabulary + a product's anchors, and any collection
# whose tags are ONLY operational is dropped as a target. (New Item V2 = input marker; CL-categorized =
# our output marker; VA Categorization Review = the human review queue; Categorized = legacy marker.)
OPERATIONAL_TAGS = {"new item v2", "cl-categorized", "va categorization review", "categorized"}

# Promo / sale-eligibility collection tags that are NOT merchandising categories (many are mislabeled
# kind=category in the map). Excluded from closures, vocabulary, and anchors — like operational tags.
PROMO_RE = re.compile(
    r"(eligible|buy more save more|\bbmsm\b|reg-sku-swap|sku swap|below[- ]map|"
    r"shopmil|shoptup|\bpromotions?\b|shop\w*\d{2}|\d{2}\s*off|%\s*off)", re.I)

def is_excluded_tag(t):
    return (t or "").lower() in OPERATIONAL_TAGS or bool(PROMO_RE.search(t or ""))

# Battery-platform tree (Shop-by-Battery-Platform). A product on a platform gets that platform's collection
# tags IN ADDITION to its category + brand tags (NON-EXCLUSIVE — category + brand + platform can all apply).
# Canonical platform collection tags (lowercased):
PLATFORM_TAGS = {"m12", "m18", "m18 tools", "m12 tools", "m18 fuel", "mx fuel",
                 "20v max", "flexvolt", "12v max", "lxt", "xgt", "cxt"}
# map a tag to its canonical platform name (so M18/M18 Tools/M18 Fuel all collapse to "M18", etc.)
_PLAT_CANON = {"m18": "M18", "m18 tools": "M18", "m18 fuel": "M18", "m12": "M12", "m12 tools": "M12",
               "mx fuel": "MX FUEL", "20v max": "20V MAX", "flexvolt": "FLEXVOLT", "12v max": "12V MAX",
               "lxt": "LXT", "xgt": "XGT", "cxt": "CXT"}
# substrings in facets.battery_platform -> canonical platform (checked longest-first)
_PLAT_FROM_FACET = [("mx fuel", "MX FUEL"), ("flexvolt", "FLEXVOLT"), ("20v max", "20V MAX"),
                    ("12v max", "12V MAX"), ("m18", "M18"), ("m12", "M12"), ("xgt", "XGT"),
                    ("cxt", "CXT"), ("lxt", "LXT")]
_PLAT_TITLE_RE = re.compile(r"\b(M12|M18|MX\s*FUEL|20V\s*MAX|FLEXVOLT|12V\s*MAX|LXT|XGT|CXT)\b", re.I)

def detect_platforms(tags, facet_bp, title):
    """canonical platform(s) a product is on, from facets.battery_platform + existing tags + title."""
    found = set()
    fb = (facet_bp or "").lower()
    for sub, canon in _PLAT_FROM_FACET:
        if sub in fb:
            found.add(canon)
            break
    for t in tags:
        c = _PLAT_CANON.get(t.lower())
        if c:
            found.add(c)
    for m in _PLAT_TITLE_RE.findall(title or ""):
        found.add(re.sub(r"\s+", " ", m).upper().replace("MXFUEL", "MX FUEL"))
    return sorted(found)

# "All product card info" = title + vendor + description + ALL metafields (structured AND unstructured),
# with custom.facets / facets.product_type as a strong placement signal. The gather surfaces all of it.
ELIGIBLE_Q = """
query($q:String!, $n:Int!, $after:String){
  products(first:$n, after:$after, query:$q, sortKey:CREATED_AT, reverse:true){
    pageInfo{ hasNextPage endCursor }
    nodes{ id title handle vendor productType createdAt tags descriptionHtml
      kit: metafield(namespace:"custom", key:"is_kit_item"){ value }
      facet: metafield(namespace:"facets", key:"product_type"){ value }
      metafields(first:40){ nodes{ namespace key value type } } }
  }
}
"""


def week_label():
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w:02d}"


def strip_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def tree_tags(map_path):
    """category-tree tags + node gids from a stored map (empty sets if absent)."""
    if not map_path.exists():
        return set(), set()
    n = json.loads(map_path.read_text(encoding="utf-8")).get("nodes", {})
    tags = {t for x in n.values() if x.get("in_category_tree") for t in x.get("category_tags", [])}
    gids = {g for g, x in n.items() if x.get("in_category_tree")}
    return tags, gids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--week", default=None)
    ap.add_argument("--max-items", type=int, default=0, help="cap eligible items gathered (0 = all)")
    a = ap.parse_args()

    slug = a.slug or STORE_SLUG.get(a.store, a.store)
    week = a.week or week_label()
    run_dir = PROJECT / "runs" / week / slug
    run_dir.mkdir(parents=True, exist_ok=True)
    map_path = PROJECT / "maps" / slug / f"{slug}-category-tree.json"

    # 1) snapshot previous tree
    prev_tags, prev_gids = tree_tags(map_path)

    # 2) refresh the tree (re-scan all sources)
    build = ["build_klein.py"] if a.store == "the-klein-store" else ["build_category_map.py", "--store", a.store]
    print(f"[refresh] building {a.store} ...", flush=True)
    r = subprocess.run([sys.executable] + build, cwd=str(HERE), capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        print("BUILD FAILED:\n" + (r.stdout or "")[-600:] + "\n" + (r.stderr or "")[-1000:])
        sys.exit(1)
    subprocess.run([sys.executable, "refine_trees.py"], cwd=str(HERE), capture_output=True, text=True, timeout=900)

    # 3) load refreshed tree + build the selectable vocabularies
    d = json.loads(map_path.read_text(encoding="utf-8"))
    nodes = d["nodes"]
    brand_names = set(d.get("brand_names", []))
    brand_lc = {b.lower() for b in brand_names}
    dual_tree = a.store in DUAL_TREE_STORES

    # Category-tree vocabulary = ALL non-promo CATEGORY-kind nodes — the nav tree AND the "floating"
    # collections off-nav (Drill Bits, Replacement Parts/Blades, Accessories, Specialty Tools, …) so
    # every real collection is a valid target. Brand names are stripped from category closures.
    cat_nodes = [x for x in nodes.values() if x.get("kind") == "category"]
    # Brand-tree vocabulary (dual-tree stores only) = all BRAND-kind nodes; brand tags are KEPT
    # (the Shop-by-Brand tree is a second, intended tagging structure). Empty for non-dual stores —
    # there brand-kind nodes are added to the category vocabulary instead (partial-brand stores).
    if dual_tree:
        brand_nodes = [x for x in nodes.values() if x.get("kind") == "brand"]
    else:
        cat_nodes += [x for x in nodes.values() if x.get("kind") == "brand"]
        brand_nodes = []

    def node_path(x):
        # readable, disambiguating path for the node (so Claude can tell M12 vs M18, brand A vs B)
        if x.get("nav_paths"):
            return x["nav_paths"][0]
        pts = [p.get("title") for p in x.get("parents", []) if p.get("title")]
        return (" / ".join(pts) + " > " if pts else "") + (x.get("title") or "")

    def node_closure(x, strip_brand):
        # this node's OWN closure (leaf + trusted ancestors); never a cross-node union.
        # operational tags are always dropped; brand names dropped for category-tree nodes.
        def keep(lst):
            return [c for c in lst if not is_excluded_tag(c)
                    and ((not strip_brand) or c.lower() not in brand_lc)]
        clos = keep(x.get("inherited_tag_closure") or [])
        if not clos:
            clos = keep(x.get("category_tags") or [])
        return sorted(set(clos))

    def build_entries(node_list, tree, strip_brand):
        out = []
        for x in node_list:
            clos = node_closure(x, strip_brand)
            if not clos:
                continue
            out.append({"gid": x["gid"], "title": x.get("title"), "tree": tree, "path": node_path(x),
                        "parents": [p.get("title") for p in x.get("parents", [])],
                        "tags_to_apply": clos})
        out.sort(key=lambda c: (c["path"] or "").lower())
        return out

    categories = build_entries(cat_nodes, "category", strip_brand=True)
    brands = build_entries(brand_nodes, "brand", strip_brand=False)

    # Battery-platform vocabulary: every non-promo node carrying a platform tag (M18/M12/MX FUEL/20V MAX/
    # FLEXVOLT/12V MAX/LXT/XGT/CXT). These also live in the brand/category trees; surfaced separately so a
    # platform pick is easy to find. Brand tags kept (e.g. Milwaukee M18 Drills -> [Milwaukee, M18, Drills]).
    plat_nodes = [x for x in nodes.values() if x.get("kind") != "promo"
                  and any(t.lower() in PLATFORM_TAGS for t in (x.get("category_tags") or []))]
    platforms = build_entries(plat_nodes, "platform", strip_brand=False)
    # per-platform CLEAN root = the node whose tags are only brand + platform (no product type), so the
    # over-categorize fallback adds just e.g. [Milwaukee, M18] and never a wrong type. Shallowest wins.
    platform_roots = {}
    for e in sorted(platforms, key=lambda c: len(c["tags_to_apply"])):
        typetags = [t for t in e["tags_to_apply"]
                    if t.lower() not in PLATFORM_TAGS and t.lower() not in brand_lc]
        if typetags:
            continue  # has a product-type tag — not a clean platform root
        for t in e["tags_to_apply"]:
            c = _PLAT_CANON.get(t.lower())
            if c and c not in platform_roots:
                platform_roots[c] = e["gid"]

    def real_tags(node_list):
        return {t for x in node_list for t in x.get("category_tags", []) if not is_excluded_tag(t)}
    tag_title = {t: x.get("title") for x in cat_nodes for t in x.get("category_tags", [])
                 if not is_excluded_tag(t)}
    cat_tag_set = real_tags(cat_nodes)
    brand_tag_set = real_tags(brand_nodes)
    new_tags = set(cat_tag_set)

    # Fallback targets so a product is NEVER left untagged (no-zero-tags rule). Per vendor: its
    # top-level brand collection (the Shop-by-Brand root titled exactly the vendor). Plus the
    # top-level category roots for a general high-level home when no specific category fits.
    vend_lc = {b.lower() for b in brand_names}
    brand_root = {}
    for b in (brands or categories):  # brands on dual-tree; else brand-kind folded into categories
        t = (b["title"] or "").lower()
        if t in vend_lc and t not in brand_root:
            brand_root[t] = b["gid"]
    category_roots = [{"gid": c["gid"], "title": c["title"], "path": c["path"]}
                      for c in categories
                      if (c["path"] or "").startswith("Shop by Category >") and (c["path"] or "").count(">") == 1]

    # 4) diff — new categories since last run
    added = sorted(new_tags - prev_tags)
    diff = [f"# {slug} — category-tree diff ({week})", "",
            f"- previous category tags: {len(prev_tags)}",
            f"- current category tags: {len(new_tags)}",
            f"- **NEW since last run: {len(added)}**", ""]
    if added:
        diff += ["## New category tags (tree updated; no collections created)", ""]
        diff += [f"- `{t}`" + (f" — {tag_title[t]}" if t in tag_title else "") for t in added]
    (run_dir / "tree-diff.md").write_text("\n".join(diff), encoding="utf-8")

    # 5) gather eligible products (with ALL metafields — structured + unstructured)
    cl = ShopifyReadClient(*get_store_credentials(a.store))
    skip = STORE_SKIP.get(a.store, set())
    skip_vendors = {v.lower() for v in STORE_SKIP_VENDORS.get(a.store, set())}
    rows, after = [], None
    while True:
        data = cl.graphql_read(ELIGIBLE_Q, {"q": "tag:'New Item V2'", "n": 50, "after": after})["products"]
        for p in data["nodes"]:
            tags = set(p["tags"])
            vendor_l = (p["vendor"] or "").lower()
            if (p.get("kit") or {}).get("value") == "true" or (tags & skip) or (vendor_l in skip_vendors):
                continue
            anchors = sorted(t for t in tags if t in cat_tag_set and t.lower() != vendor_l)
            brand_anchors = sorted(t for t in tags if t in brand_tag_set)
            mfs, battery_platform = [], None
            for m in ((p.get("metafields") or {}).get("nodes") or []):
                if m.get("namespace") == "custom" and m.get("key") == "is_kit_item":
                    continue
                if m.get("namespace") == "facets" and m.get("key") == "battery_platform":
                    battery_platform = m.get("value")
                val = m.get("value") or ""
                mfs.append({"key": f"{m.get('namespace')}.{m.get('key')}",
                            "value": (val[:300] + "…") if len(val) > 300 else val})
            platform_tags = detect_platforms(tags, battery_platform, p["title"])
            rows.append({
                "product_id": p["id"].rsplit("/", 1)[-1], "gid": p["id"], "title": p["title"],
                "handle": p["handle"], "vendor": p["vendor"], "type": p["productType"],
                "created_at": p["createdAt"], "current_category_tags": anchors,
                "current_brand_tags": brand_anchors,
                "all_tags": sorted(tags), "description": strip_html(p["descriptionHtml"])[:600],
                "facets_product_type": (p.get("facet") or {}).get("value"), "metafields": mfs,
                "fallback_brand_gid": brand_root.get(vendor_l),
                "battery_platform": battery_platform, "platform_tags": platform_tags,
            })
            if a.max_items and len(rows) >= a.max_items:
                break
        if (a.max_items and len(rows) >= a.max_items) or not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]

    (run_dir / "candidates.json").write_text(json.dumps({
        "store": a.store, "slug": slug, "week": week, "dual_tree": dual_tree,
        "map_md": str((PROJECT / "maps" / slug / f"{slug}-category-tree.md")),
        "categories": categories,
        "brands": brands,
        "platforms": platforms,
        "category_roots": category_roots,
        "brand_roots": brand_root,
        "platform_roots": platform_roots,
        "category_vocabulary": sorted(cat_tag_set),
        "brand_vocabulary": sorted(brand_tag_set),
        "brand_names": sorted(brand_names),
        "new_categories_since_last_run": added,
        "count": len(rows), "candidates": rows,
    }, indent=2), encoding="utf-8")

    n_plat = sum(1 for r in rows if r["platform_tags"])
    print(f"[done] {slug} {week}: eligible={len(rows)} | new_categories={len(added)} | dual_tree={dual_tree} | "
          f"category_nodes={len(categories)} brand_nodes={len(brands)} platform_nodes={len(platforms)} | "
          f"cat_vocab={len(cat_tag_set)} brand_vocab={len(brand_tag_set)} | products_on_platform={n_plat}")
    print(f"  tree-diff:   {run_dir / 'tree-diff.md'}")
    print(f"  candidates:  {run_dir / 'candidates.json'}")
    print(f"  category tree (reference for classification): {PROJECT / 'maps' / slug / (slug + '-category-tree.md')}")


if __name__ == "__main__":
    main()
