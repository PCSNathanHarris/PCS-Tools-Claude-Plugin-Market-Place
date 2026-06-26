"""
Read-only discovery for Phase 2 planning.

  python discover_new_items.py --store knaack-store --tag "New Item V2"

Confirms the trigger tag exists, finds the "Is Kit Item?" metafield (namespace.key + value),
and shows what category tags new items already carry (the anchor for tag inheritance).
"""

import argparse
from collections import Counter

from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

Q = """
query($q:String!, $n:Int!, $after:String){
  products(first:$n, query:$q, after:$after){
    pageInfo{ hasNextPage endCursor }
    nodes{ id title vendor productType tags
      metafields(first:60){ nodes{ namespace key type value } } }
  }
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="knaack-store")
    ap.add_argument("--tag", default="New Item V2")
    ap.add_argument("--sample", type=int, default=12)
    ap.add_argument("--count-all", action="store_true")
    a = ap.parse_args()

    d, c, s = get_store_credentials(a.store)
    cl = ShopifyReadClient(d, c, s)
    qstr = f"tag:'{a.tag}'"

    data = cl.graphql_read(Q, {"q": qstr, "n": a.sample, "after": None})["products"]
    nodes = data["nodes"]
    print(f"Query {qstr!r}: showing {len(nodes)} sample (hasNextPage={data['pageInfo']['hasNextPage']})\n")

    kit_keys = Counter()
    for p in nodes:
        mfs = p["metafields"]["nodes"]
        kit = [m for m in mfs if "kit" in m["key"].lower()]
        for m in kit:
            kit_keys[f"{m['namespace']}.{m['key']} [{m['type']}]"] += 1
        print(f"- {p['title'][:60]!r}  vendor={p['vendor']}  type={p['productType']!r}")
        print(f"    tags={p['tags']}")
        if kit:
            print("    KIT: " + "; ".join(f"{m['namespace']}.{m['key']}={m['value']!r}" for m in kit))
    print("\nkit-like metafield keys seen:", dict(kit_keys))

    if a.count_all:
        total = len(nodes)
        pi = data["pageInfo"]
        while pi["hasNextPage"]:
            data = cl.graphql_read(Q, {"q": qstr, "n": 100, "after": pi["endCursor"]})["products"]
            total += len(data["nodes"])
            pi = data["pageInfo"]
        print(f"\nTOTAL products with tag {a.tag!r}: {total}")


if __name__ == "__main__":
    main()
