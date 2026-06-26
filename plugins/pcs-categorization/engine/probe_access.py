"""
Read-only probe: which stores expose the API fields the tree-builder needs (menus, collections)?
Surfaces per-store scope gaps (e.g. read_online_store_navigation) before the sweep.

  python probe_access.py
"""

import json
from config import get_store_credentials, load_store_config
from shopify_read_client import ShopifyReadClient

EXCLUDE = {"toolupstore"}  # Toolup / TUP excluded


def probe(cl, query):
    try:
        cl.graphql_read(query)
        return "ok"
    except Exception as e:
        msg = str(e)
        if "ACCESS_DENIED" in msg or "Access denied" in msg:
            return "DENIED"
        return f"ERR:{msg[:40]}"


def main():
    stores = [s for s in load_store_config().keys() if s not in EXCLUDE]
    print(f"{'store':26} {'theme(role=main)':34} {'menus':8} {'collections':12}")
    for s in stores:
        d, c, sec = get_store_credentials(s)
        cl = ShopifyReadClient(d, c, sec)
        try:
            themes = cl.rest_get("themes.json").get("themes", [])
            theme = next((t.get("name") for t in themes if t.get("role") == "main"), "?")
        except Exception as e:
            theme = f"ERR:{str(e)[:20]}"
        menus = probe(cl, "query{menus(first:1){nodes{handle}}}")
        cols = probe(cl, "query{collections(first:1){nodes{handle}}}")
        print(f"{s:26} {str(theme)[:34]:34} {menus:8} {cols:12}")


if __name__ == "__main__":
    main()
