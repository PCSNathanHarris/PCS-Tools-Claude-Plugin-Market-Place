"""
Self-test for the read-only reader.

  python selftest.py --store knaack-store

1. Guard (offline): mutation/subscription strings must be refused; queries must pass.
2. Auth smoke (network): fetch a token and run a trivial shop query.
"""

import argparse
import sys

from config import get_store_credentials
from shopify_read_client import ReadOnlyViolation, ShopifyReadClient


def test_guard() -> bool:
    ok = True
    must_block = [
        "mutation { collectionDelete(input:{id:\"x\"}) { deletedCollectionId } }",
        "mutation Foo { productUpdate(input:{id:\"x\"}) { product { id } } }",
        "subscription { x }",
    ]
    must_pass = [
        "query { shop { name } }",
        "{ shop { name } }",
        "query GetCollections($ids:[ID!]!){ nodes(ids:$ids){ ... on Collection { id } } }",
    ]
    for q in must_block:
        try:
            ShopifyReadClient.assert_read_only(q)
            print(f"  FAIL: not blocked -> {q[:48]}...")
            ok = False
        except ReadOnlyViolation:
            print(f"  ok: blocked    -> {q[:48]}...")
    for q in must_pass:
        try:
            ShopifyReadClient.assert_read_only(q)
            print(f"  ok: allowed    -> {q[:48]}...")
        except ReadOnlyViolation:
            print(f"  FAIL: blocked a query -> {q[:48]}...")
            ok = False
    return ok


def test_auth(store: str) -> bool:
    domain, cid, secret = get_store_credentials(store)
    print(f"  resolved domain: {domain}  client_id: {cid[:6]}...")
    client = ShopifyReadClient(domain, cid, secret)
    data = client.graphql_read("query { shop { name myshopifyDomain currencyCode } }")
    shop = data.get("shop", {})
    print(f"  shop: {shop}")
    return bool(shop.get("name"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="knaack-store")
    ap.add_argument("--skip-auth", action="store_true")
    args = ap.parse_args()

    print("[1] read-only guard")
    guard_ok = test_guard()

    auth_ok = True
    if not args.skip_auth:
        print("[2] auth smoke test")
        try:
            auth_ok = test_auth(args.store)
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL: {type(e).__name__}: {e}")
            auth_ok = False

    print(f"\nGUARD: {'PASS' if guard_ok else 'FAIL'}   AUTH: {'PASS' if auth_ok else 'FAIL'}")
    sys.exit(0 if (guard_ok and auth_ok) else 1)
