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

    # 3) load refreshed tree + category vocabulary
    d = json.loads(map_path.read_text(encoding="utf-8"))
    nodes = d["nodes"]
    brand_names = set(d.get("brand_names", []))
    cat_nodes = [x for x in nodes.values() if x.get("in_category_tree") and x.get("kind") == "category"]
    brand_lc = {b.lower() for b in brand_names}

    def node_path(x):
        # readable, disambiguating path for the node (so Claude can tell M12 vs M18, brand A vs B)
        if x.get("nav_paths"):
            return x["nav_paths"][0]
        pts = [p.get("title") for p in x.get("parents", []) if p.get("title")]
        return (" / ".join(pts) + " > " if pts else "") + (x.get("title") or "")

    def node_closure(x):
        # this node's OWN brand-stripped closure (leaf + trusted ancestors); never a cross-node union
        clos = [c for c in x.get("inherited_tag_closure", []) if c.lower() not in brand_lc]
        if not clos:
            clos = [c for c in x.get("category_tags", []) if c.lower() not in brand_lc]
        return sorted(set(clos))

    # one entry per category NODE — Claude picks by gid (path disambiguates reused leaf names)
    categories, tag_title = [], {}
    for x in cat_nodes:
        clos = node_closure(x)
        if not clos:
            continue
        categories.append({"gid": x["gid"], "title": x.get("title"), "path": node_path(x),
                           "parents": [p.get("title") for p in x.get("parents", [])],
                           "tags_to_apply": clos})
        for t in x.get("category_tags", []):
            tag_title[t] = x.get("title")
    categories.sort(key=lambda c: (c["path"] or "").lower())
    cat_tag_set = {t for x in cat_nodes for t in x.get("category_tags", [])}
    new_tags = set(cat_tag_set)

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
            mfs = []
            for m in ((p.get("metafields") or {}).get("nodes") or []):
                if m.get("namespace") == "custom" and m.get("key") == "is_kit_item":
                    continue
                val = m.get("value") or ""
                mfs.append({"key": f"{m.get('namespace')}.{m.get('key')}",
                            "value": (val[:300] + "…") if len(val) > 300 else val})
            rows.append({
                "product_id": p["id"].rsplit("/", 1)[-1], "gid": p["id"], "title": p["title"],
                "handle": p["handle"], "vendor": p["vendor"], "type": p["productType"],
                "created_at": p["createdAt"], "current_category_tags": anchors,
                "all_tags": sorted(tags), "description": strip_html(p["descriptionHtml"])[:600],
                "facets_product_type": (p.get("facet") or {}).get("value"), "metafields": mfs,
            })
            if a.max_items and len(rows) >= a.max_items:
                break
        if (a.max_items and len(rows) >= a.max_items) or not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]

    (run_dir / "candidates.json").write_text(json.dumps({
        "store": a.store, "slug": slug, "week": week,
        "map_md": str((PROJECT / "maps" / slug / f"{slug}-category-tree.md")),
        "categories": categories,
        "category_vocabulary": sorted(cat_tag_set),
        "brand_names": sorted(brand_names),
        "new_categories_since_last_run": added,
        "count": len(rows), "candidates": rows,
    }, indent=2), encoding="utf-8")

    print(f"[done] {slug} {week}: eligible={len(rows)} | new_categories={len(added)} | "
          f"category_nodes={len(categories)} | vocab={len(cat_tag_set)}")
    print(f"  tree-diff:   {run_dir / 'tree-diff.md'}")
    print(f"  candidates:  {run_dir / 'candidates.json'}")
    print(f"  category tree (reference for classification): {PROJECT / 'maps' / slug / (slug + '-category-tree.md')}")


if __name__ == "__main__":
    main()
