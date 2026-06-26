"""
Read-only Phase-2 dry-run preview: for every `New Item V2` + non-kit product, check whether it
already carries a JTB category tag (an ANCHOR we can inherit ancestors from) or whether it would
need classification/inference.

  python analyze_anchor.py --store knaack-store

No writes. Loads the existing category map for the tag→node closure.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)

Q = """
query($q:String!, $n:Int!, $after:String){
  products(first:$n, query:$q, after:$after){
    pageInfo{ hasNextPage endCursor }
    nodes{ id title tags
      kit: metafield(namespace:"custom", key:"is_kit_item"){ value } }
  }
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="knaack-store")
    ap.add_argument("--slug", default="jtb")
    ap.add_argument("--tag", default="New Item V2")
    args = ap.parse_args()

    mp = json.load(open(PROJECT / "maps" / args.slug / f"{args.slug}-category-tree.json", encoding="utf-8"))
    nodes = mp["nodes"]
    # tag -> closure (own + trusted ancestors); a category tag can map to >1 node, union closures
    tag_to_closure = {}
    for n in nodes.values():
        for t in n["category_tags"]:
            tag_to_closure.setdefault(t, set()).update(n["inherited_tag_closure"])
    all_cat_tags = set(tag_to_closure)

    d, c, s = get_store_credentials(args.store)
    cl = ShopifyReadClient(d, c, s)

    anchored, needs_inference, kits_skipped = [], [], 0
    missing_counter = Counter()
    after = None
    while True:
        data = cl.graphql_read(Q, {"q": f"tag:'{args.tag}'", "n": 100, "after": after})["products"]
        for p in data["nodes"]:
            if (p.get("kit") or {}).get("value") == "true":
                kits_skipped += 1
                continue
            ptags = set(p["tags"])
            anchors = ptags & all_cat_tags
            if not anchors:
                needs_inference.append(p["title"])
                continue
            target = set()
            for t in anchors:
                target |= tag_to_closure[t]
            missing = target - ptags
            anchored.append((p["title"], sorted(anchors), sorted(missing)))
            for m in missing:
                missing_counter[m] += 1
        if not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]

    total = len(anchored) + len(needs_inference)
    print(f"New Item V2 (non-kit): {total}   |   kits skipped: {kits_skipped}\n")
    print(f"ANCHORED (have >=1 JTB category tag): {len(anchored)}")
    print(f"NEEDS CLASSIFICATION (no JTB category tag): {len(needs_inference)}\n")

    print("Sample ANCHORED (anchor -> missing ancestor tags it would gain):")
    for title, anchors, missing in anchored[:10]:
        print(f"  - {title[:55]!r}\n      anchors={anchors}  missing={missing}")
    print("\nSample NEEDS CLASSIFICATION:")
    for t in needs_inference[:10]:
        print(f"  - {t[:65]!r}")
    print("\nMost common missing ancestor tags (anchored set):", missing_counter.most_common(12))


if __name__ == "__main__":
    main()
