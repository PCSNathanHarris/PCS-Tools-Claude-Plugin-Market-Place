"""
Phase 2 — DRY RUN classifier (read-only, writes nothing to Shopify).

For every `New Item V2` + non-kit product on a store, use vendor + title + DESCRIPTION to find
the bottom-most category leaf in the store's category map, then propose the exact collection-
criteria tags it should gain (leaf + ancestors, brand tags excluded). Proposes New Item V2
removal only when the leaf→root chain would be complete and confidence is not low.

  python classify_new_items.py --store knaack-store

Outputs (../proposals/<slug>/):
  new-item-v2-proposals.csv   one row per product (machine-readable, for the write step)
  new-item-v2-proposals.md    human-readable review report

Only tags that are EXACT collection-criteria tags in the map are ever proposed (so the product
actually lands in the front-end collection). Nothing is written — review the report, then the
write step applies approved tags through the audited shopify_* MCP tools.
"""

import argparse
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path

from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)
CATEGORY_ROOTS = ("Jobsite Storage", "Personal Storage", "Truck Storage")
BRAND_ROOT = "Shop by Brand"

SCAN_Q = """
query($q:String!, $n:Int!, $after:String){
  products(first:$n, query:$q, after:$after){
    pageInfo{ hasNextPage endCursor }
    nodes{
      id title handle vendor productType tags descriptionHtml
      kit: metafield(namespace:"custom", key:"is_kit_item"){ value }
    }
  }
}
"""


def norm(s: str) -> str:
    """Lowercase; non-alphanumerics → single spaces; padded so we can match whole tokens."""
    return " " + re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip() + " "


def strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", s or ""))


def load_map(slug):
    return json.load(open(PROJECT / "maps" / slug / f"{slug}-category-tree.json", encoding="utf-8"))


def node_depth(n):
    if n["nav_paths"]:
        return max(len(p.split(" > ")) for p in n["nav_paths"])
    return 1 + len(n.get("ancestors", []))


def reaches_category_root(n):
    return any(p.split(" > ")[0] in CATEGORY_ROOTS for p in n["nav_paths"])


def build_index(mp):
    nodes = mp["nodes"]
    # pure-brand nodes: only ever appear directly under "Shop by Brand" (e.g. Knaack, DeWalt)
    pure_brand = {
        g for g, n in nodes.items()
        if n["nav_paths"] and all(
            p.startswith(BRAND_ROOT + " > ") and len(p.split(" > ")) == 2 for p in n["nav_paths"]
        )
    }
    brand_tags = {t for g in pure_brand for t in nodes[g]["category_tags"]}

    # keyword -> list of (gid, keyword_text). Keywords come from each non-pure-brand node's
    # EXACT criteria tags (lowercased), plus a despaced variant (toughsystem ~ "tough system").
    kw_index = {}
    for g, n in nodes.items():
        if g in pure_brand:
            continue
        for tag in n["category_tags"]:
            if tag in brand_tags:
                continue
            base = norm(tag).strip()
            if len(base) < 3:
                continue
            for variant in {base, base.replace(" ", "")}:
                kw_index.setdefault(variant, []).append((g, tag))
    return nodes, pure_brand, brand_tags, kw_index


def classify(product, nodes, brand_tags, kw_index):
    title, vendor = product["title"], product.get("vendor") or ""
    desc = strip_html(product.get("descriptionHtml"))
    hay = norm(f"{title} {vendor} {desc}")
    hay_ns = hay.replace(" ", "")

    hits = []  # (gid, tag, keyword, depth)
    for kw, refs in kw_index.items():
        present = (f" {kw} " in hay) if " " in kw else (f" {kw} " in hay or kw in hay_ns)
        if not present:
            continue
        for gid, tag in refs:
            hits.append((gid, tag, kw, node_depth(nodes[gid])))
    if not hits:
        return None

    # prefer the most specific (deepest) node; tie-break by longer keyword
    hits.sort(key=lambda h: (h[3], len(h[2])), reverse=True)
    best_gid, best_tag, best_kw, best_depth = hits[0]
    alt = sorted({nodes[g]["title"] for g, _, _, d in hits if g != best_gid})

    node = nodes[best_gid]
    closure = [t for t in node["inherited_tag_closure"] if t not in brand_tags]
    have = set(product["tags"])
    to_add = [t for t in closure if t not in have]

    # confidence
    if best_depth >= 3 or " " in best_kw or best_kw == best_tag.lower().replace(" ", ""):
        confidence = "high"
    elif best_depth == 2:
        confidence = "medium"
    else:
        confidence = "low"
    distinct_top = {nodes[g]["title"] for g, _, _, d in hits if d == best_depth}
    if len(distinct_top) > 1:
        confidence = "low"  # ambiguous strongest match

    chain_complete = reaches_category_root(node) and set(closure).issubset(have | set(to_add))
    propose_remove = chain_complete and confidence != "low"

    flags = []
    if not node["in_active_nav"]:
        flags.append("leaf_not_in_nav")
    if len(distinct_top) > 1:
        flags.append("ambiguous")
    if "remove" in have:
        flags.append("has_remove_tag")
    if not reaches_category_root(node):
        flags.append("no_root_chain")

    return {
        "matched_title": node["title"], "matched_handle": node["handle"],
        "matched_tag": best_tag, "evidence_kw": best_kw, "depth": best_depth,
        "alternates": alt, "tags_to_add": to_add, "confidence": confidence,
        "propose_remove_new_item_v2": propose_remove, "flags": flags,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="knaack-store")
    ap.add_argument("--slug", default="jtb")
    ap.add_argument("--tag", default="New Item V2")
    args = ap.parse_args()

    mp = load_map(args.slug)
    nodes, pure_brand, brand_tags, kw_index = build_index(mp)
    print(f"map: {len(nodes)} nodes; {len(pure_brand)} pure-brand excluded; {len(kw_index)} keywords")

    d, c, s = get_store_credentials(args.store)
    cl = ShopifyReadClient(d, c, s)

    rows, after = [], None
    skipped_kit = skipped_remove = 0
    while True:
        data = cl.graphql_read(SCAN_Q, {"q": f"tag:'{args.tag}'", "n": 100, "after": after})["products"]
        for p in data["nodes"]:
            tags = set(p["tags"])
            # Autonomous exclusion rules (no human input):
            #  - kits (is_kit_item=true) are out of scope
            #  - `remove` = a jobsite box that ships WITH tools inside → not true jobsite storage
            if (p.get("kit") or {}).get("value") == "true":
                skipped_kit += 1
                continue
            if "remove" in tags:
                skipped_remove += 1
                continue
            res = classify(p, nodes, brand_tags, kw_index)
            rows.append((p, res))
        if not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]

    matched = [r for r in rows if r[1]]
    unmatched = [r for r in rows if not r[1]]
    removals = [r for r in matched if r[1]["propose_remove_new_item_v2"]]
    conf = Counter(r[1]["confidence"] for r in matched)

    out = PROJECT / "proposals" / args.slug
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "new-item-v2-proposals.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "handle", "title", "vendor", "matched_category", "matched_tag",
                    "evidence_keyword", "confidence", "tags_to_add", "propose_remove_new_item_v2",
                    "flags", "current_tags"])
        for p, res in rows:
            if res:
                w.writerow([p["id"].rsplit("/", 1)[-1], p["handle"], p["title"], p.get("vendor"),
                            res["matched_title"], res["matched_tag"], res["evidence_kw"],
                            res["confidence"], "|".join(res["tags_to_add"]),
                            "yes" if res["propose_remove_new_item_v2"] else "no",
                            ",".join(res["flags"]), "|".join(p["tags"])])
            else:
                w.writerow([p["id"].rsplit("/", 1)[-1], p["handle"], p["title"], p.get("vendor"),
                            "NO MATCH", "", "", "none", "", "no", "needs_manual", "|".join(p["tags"])])

    L = [
        f"# {args.store} — New Item V2 categorization proposals (DRY RUN)",
        "",
        f"- Eligible (New Item V2, non-kit, no `remove` tag): **{len(rows)}**",
        f"- Skipped — `remove` tag (box ships with tools): **{skipped_remove}**  ·  kits: **{skipped_kit}**",
        f"- Auto-classified: **{len(matched)}**  (high={conf['high']}, medium={conf['medium']}, low={conf['low']})",
        f"- No match → manual: **{len(unmatched)}**",
        f"- Would have New Item V2 removed (chain complete + confident): **{len(removals)}**",
        "",
        "> Nothing has been written. Only exact collection-criteria tags are proposed. Review,"
        " then the write step applies approved tags via the audited shopify_* MCP tools.",
        "",
        "## Classified products",
        "",
    ]
    for p, res in sorted(matched, key=lambda r: (r[1]["confidence"] != "high", r[1]["matched_title"])):
        add = ", ".join(f"`{t}`" for t in res["tags_to_add"]) or "_(already has all)_"
        fl = (" ⚠ " + ",".join(res["flags"])) if res["flags"] else ""
        rm = "✅ remove New Item V2" if res["propose_remove_new_item_v2"] else "keep New Item V2"
        alt = f"  (alt: {', '.join(res['alternates'])})" if res["alternates"] else ""
        L.append(f"- **{p['title'][:70]}** — _{p.get('vendor')}_")
        L.append(f"    → **{res['matched_title']}** (`{res['matched_tag']}`, via \"{res['evidence_kw']}\", {res['confidence']}){alt}")
        L.append(f"    add: {add} · {rm}{fl}")
    L += ["", "## No match — need manual categorization", ""]
    for p, _ in unmatched:
        L.append(f"- **{p['title'][:75]}** — _{p.get('vendor')}_ — tags: {p['tags']}")
    L.append("")

    (out / "new-item-v2-proposals.md").write_text("\n".join(L), encoding="utf-8")

    print(f"\neligible {len(rows)} | skipped(remove={skipped_remove}, kit={skipped_kit}) | "
          f"classified {len(matched)} (high={conf['high']} med={conf['medium']} low={conf['low']}) "
          f"| no-match {len(unmatched)} | proposed removals {len(removals)}")
    print(f"  {out / 'new-item-v2-proposals.csv'}")
    print(f"  {out / 'new-item-v2-proposals.md'}")


if __name__ == "__main__":
    main()
