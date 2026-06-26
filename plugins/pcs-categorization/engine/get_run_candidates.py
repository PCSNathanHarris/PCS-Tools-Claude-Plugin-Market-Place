"""
Read-only: assemble the run sample + per-product anchor analysis for Claude to classify.

  python get_run_candidates.py --store toolup-my-tool-store --newest 30 --per-vendor-cap 10

Sample selection: newest `New Item V2` (non-kit, store skip-tags removed), de-duplicated by
title, with no single vendor exceeding the cap.

Vocabulary: ONLY the connected category tree — nodes reachable from the active nav via trusted
edges (nav/linklist/metafield). Standalone promo/operational/brand collections are excluded as
targets. Brand tags (== a product's vendor) are not treated as category anchors.

Output → runs/<week>/<slug>/candidates.{json,md} + category_vocabulary.md
"""

import argparse
import datetime
import html
import json
import re
from collections import defaultdict, deque
from pathlib import Path

from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)
SKIP_TAGS = {"knaack-store": {"remove"}}

Q = """
query($q:String!, $n:Int!){
  products(first:$n, query:$q, sortKey:CREATED_AT, reverse:true){
    nodes{
      id title handle vendor productType createdAt tags descriptionHtml
      kit: metafield(namespace:"custom", key:"is_kit_item"){ value }
    }
  }
}
"""


def strip_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def week_label():
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w:02d}"


def connected_category_nodes(mp):
    """BFS from nav roots over trusted child edges → the real category tree."""
    nodes = mp["nodes"]
    children = defaultdict(list)
    for e in mp["edges"]:
        if set(e["sources"]) & {"nav", "linklist", "metafield"}:
            children[e["parent"]].append(e["child"])
    roots = [g for g, n in nodes.items() if n["in_active_nav"]]
    seen, dq = set(roots), deque(roots)
    while dq:
        g = dq.popleft()
        for c in children.get(g, []):
            if c not in seen:
                seen.add(c)
                dq.append(c)
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="toolup-my-tool-store")
    ap.add_argument("--slug", default="mts")
    ap.add_argument("--tag", default="New Item V2")
    ap.add_argument("--newest", type=int, default=30)
    ap.add_argument("--per-vendor-cap", type=int, default=10)
    ap.add_argument("--fetch", type=int, default=250)
    args = ap.parse_args()

    mp = json.load(open(PROJECT / "maps" / args.slug / f"{args.slug}-category-tree.json", encoding="utf-8"))
    nodes = mp["nodes"]
    cat_nodes = connected_category_nodes(mp)

    # tag -> representative PURE category node within the connected tree
    cat_pure = {}
    for g in cat_nodes:
        n = nodes[g]
        if len(n["category_tags"]) != 1:
            continue
        t = n["category_tags"][0]
        cur = cat_pure.get(t)
        if cur is None or len(n["ancestors"]) > len(nodes[cur]["ancestors"]):
            cat_pure[t] = g
    category_tags = set(cat_pure)

    d, c, s = get_store_credentials(args.store)
    cl = ShopifyReadClient(d, c, s)
    skip = SKIP_TAGS.get(args.store, set())

    raw = cl.graphql_read(Q, {"q": f"tag:'{args.tag}'", "n": args.fetch})["products"]["nodes"]

    # eligible + dedupe by title + per-vendor cap, newest first
    seen_titles, vendor_count, rows = set(), defaultdict(int), []
    for p in raw:
        ptags = set(p["tags"])
        if (p.get("kit") or {}).get("value") == "true" or (ptags & skip):
            continue
        key = re.sub(r"\s+", " ", (p["title"] or "").strip().lower())
        if key in seen_titles:
            continue
        v = p["vendor"] or "?"
        if vendor_count[v] >= args.per_vendor_cap:
            continue
        seen_titles.add(key)
        vendor_count[v] += 1

        vendor_l = v.lower()
        anchors = sorted(t for t in ptags if t in category_tags and t.lower() != vendor_l)
        deepest = max(anchors, key=lambda t: len(nodes[cat_pure[t]]["ancestors"]), default=None)
        target = set()
        for t in anchors:
            target |= {x for x in nodes[cat_pure[t]]["inherited_tag_closure"] if x in category_tags}
        missing = sorted(t for t in target if t not in ptags)
        rows.append({
            "product_id": p["id"].rsplit("/", 1)[-1], "gid": p["id"], "title": p["title"],
            "vendor": v, "type": p["productType"], "created_at": p["createdAt"],
            "anchors": anchors, "deepest_anchor": deepest, "missing_ancestors": missing,
            "no_anchor": not anchors,
            "description": strip_html(p["descriptionHtml"])[:500],
            "noncat_tags": sorted(t for t in ptags if t not in category_tags),
        })
        if len(rows) >= args.newest:
            break

    out = PROJECT / "runs" / week_label() / args.slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidates.json").write_text(json.dumps({
        "store": args.store, "slug": args.slug, "week": week_label(),
        "vocabulary_size": len(category_tags), "count": len(rows), "candidates": rows,
    }, indent=2), encoding="utf-8")

    # category vocabulary reference (top-level categories → direct children)
    parent_of = defaultdict(set)
    child_of = defaultdict(set)
    for e in mp["edges"]:
        if set(e["sources"]) & {"nav", "linklist", "metafield"} and e["parent"] in cat_nodes and e["child"] in cat_nodes:
            parent_of[e["child"]].add(e["parent"])
            child_of[e["parent"]].add(e["child"])
    tops = sorted((g for g in cat_nodes if not parent_of[g] and nodes[g]["category_tags"]),
                  key=lambda g: nodes[g]["title"] or "")
    V = [f"# {args.store} — connected category vocabulary ({len(category_tags)} category tags)", ""]
    for g in tops:
        n = nodes[g]
        V.append(f"- **{n['title']}** (`{n['category_tags'][0] if n['category_tags'] else '—'}`)")
        for cgid in sorted(child_of[g], key=lambda x: nodes[x]["title"] or ""):
            cn = nodes[cgid]
            V.append(f"    - {cn['title']} (`{cn['category_tags'][0] if cn['category_tags'] else '—'}`)")
    (out / "category_vocabulary.md").write_text("\n".join(V), encoding="utf-8")

    anchored = sum(1 for r in rows if not r["no_anchor"])
    print(f"week {week_label()} | sample: {len(rows)} | anchored: {anchored} | no-anchor: {len(rows)-anchored}")
    print(f"  vendors: {dict(vendor_count)}")
    print(f"  connected category vocabulary: {len(category_tags)} tags (of {len(nodes)} total nodes)")
    print(f"  {out/'candidates.json'}")
    print(f"  {out/'category_vocabulary.md'}")


if __name__ == "__main__":
    main()
