"""
Read-only inspector for verifying the category map.

  python inspect_collection.py --store knaack-store --collection 352281657497 --products 5
  python inspect_collection.py --store knaack-store --collection jobsite-chests

Prints a collection's rule set, ALL its metafields (to confirm subcollections_list), and
optionally a sample of member products with their tags (to validate rule-tag ↔ product-tag).
"""

import argparse
import json

from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

BY_ID = """
query($id: ID!, $n: Int!) {
  collection(id: $id) {
    id title handle productsCount { count }
    ruleSet { appliedDisjunctively rules { column relation condition } }
    metafields(first: 50) { nodes { namespace key type value } }
    products(first: $n) { nodes { title vendor tags } }
  }
}
"""

BY_HANDLE = """
query($q: String!, $n: Int!) {
  collections(first: 1, query: $q) {
    nodes {
      id title handle productsCount { count }
      ruleSet { appliedDisjunctively rules { column relation condition } }
      metafields(first: 50) { nodes { namespace key type value } }
      products(first: $n) { nodes { title vendor tags } }
    }
  }
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="knaack-store")
    ap.add_argument("--collection", required=True, help="numeric id, GID, or handle")
    ap.add_argument("--products", type=int, default=0)
    args = ap.parse_args()

    domain, cid, secret = get_store_credentials(args.store)
    client = ShopifyReadClient(domain, cid, secret)

    val = args.collection
    if val.isdigit():
        data = client.graphql_read(BY_ID, {"id": f"gid://shopify/Collection/{val}", "n": args.products})
        col = data.get("collection")
    elif val.startswith("gid://"):
        data = client.graphql_read(BY_ID, {"id": val, "n": args.products})
        col = data.get("collection")
    else:
        data = client.graphql_read(BY_HANDLE, {"q": f"handle:{val}", "n": args.products})
        nodes = data.get("collections", {}).get("nodes", [])
        col = nodes[0] if nodes else None

    if not col:
        raise SystemExit(f"Collection '{val}' not found.")

    print(f"# {col['title']}  ({col['handle']})  id={col['id'].rsplit('/',1)[-1]}  products={col['productsCount']['count']}")
    rs = col.get("ruleSet")
    if rs:
        conj = "OR" if rs["appliedDisjunctively"] else "AND"
        print(f"  ruleSet ({conj}):")
        for r in rs["rules"]:
            print(f"    - {r['column']} {r['relation']} {r['condition']!r}")
    else:
        print("  ruleSet: (manual collection)")
    mfs = col.get("metafields", {}).get("nodes", [])
    print(f"  metafields ({len(mfs)}):")
    for mf in mfs:
        v = mf["value"]
        v = (v[:120] + "...") if isinstance(v, str) and len(v) > 120 else v
        print(f"    - {mf['namespace']}.{mf['key']} [{mf['type']}] = {v}")
    prods = col.get("products", {}).get("nodes", [])
    if prods:
        print(f"  sample products ({len(prods)}):")
        for p in prods:
            print(f"    - {p['title'][:60]!r}  vendor={p['vendor']}  tags={p['tags']}")


if __name__ == "__main__":
    main()
