"""
Build the-klein-store's category structure from collections only (no nav — menus are blocked).
Applies the Claude-authored curated hierarchy in klein_hierarchy.py. Read-only; writes the
standard map shape so refine_trees.py + coverage work on it.

  python build_klein.py
"""

import datetime
import json
from pathlib import Path

import klein_hierarchy as KH
from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)
STORE, SLUG = "the-klein-store", "the-klein-store"

Q = """
query($after:String){
  collections(first:200, after:$after){
    pageInfo{ hasNextPage endCursor }
    nodes{ id title handle productsCount{count}
      ruleSet{ appliedDisjunctively rules{ column relation condition } } }
  }
}
"""


def tag_conditions(rs):
    return [r["condition"] for r in (rs or {}).get("rules", []) if r.get("column") == "TAG"]


def main():
    d, c, s = get_store_credentials(STORE)
    cl = ShopifyReadClient(d, c, s)
    theme = next((t.get("name") for t in cl.rest_get("themes.json").get("themes", []) if t.get("role") == "main"), "?")

    cols, after = [], None
    while True:
        data = cl.graphql_read(Q, {"after": after})["collections"]
        cols += data["nodes"]
        if not data["pageInfo"]["hasNextPage"]:
            break
        after = data["pageInfo"]["endCursor"]

    catset = KH.category_tags()
    parent_of = KH.parent_of_tag()
    tops = set(KH.HIERARCHY) | set(KH.STANDALONE)

    # tag -> best node gid (prefer the collection whose only tag IS that tag; max products on ties)
    tag2gid = {}
    for col in cols:
        cts = tag_conditions(col.get("ruleSet"))
        if len(cts) == 1:
            t = cts[0]
            cur = tag2gid.get(t)
            if cur is None or (col["productsCount"]["count"] > next(
                    cc["productsCount"]["count"] for cc in cols if cc["id"] == cur)):
                tag2gid[t] = col["id"]

    nodes = {}
    for col in cols:
        gid = col["id"]
        cts = tag_conditions(col.get("ruleSet"))
        tag = cts[0] if cts else None
        excluded = col["title"] in KH.EXCLUDE_TITLES or (tag in KH.EXCLUDE_TAGS)
        is_cat = (not excluded) and (tag in catset)
        is_top = is_cat and tag in tops
        parent_tag = parent_of.get(tag) if is_cat else None
        nodes[gid] = {
            "gid": gid, "numeric_id": gid.rsplit("/", 1)[-1],
            "title": col["title"], "handle": col["handle"],
            "template_suffix": None, "products_count": col["productsCount"]["count"],
            "rule_set": ({"applied_disjunctively": col["ruleSet"]["appliedDisjunctively"],
                          "rules": col["ruleSet"]["rules"]} if col.get("ruleSet") else None),
            "category_tags": cts,
            "parents": [], "children": [], "ancestors": [],
            "inherited_tag_closure": [], "inherited_tag_closure_with_template": [],
            "template_extra_tags": [],
            "in_active_nav": is_top,   # curated tops act as roots for connectivity
            "nav_paths": ([col["title"]] if is_top else
                          ([f"{parent_tag} > {col['title']}"] if parent_tag else [])),
            "hierarchy_sources": [], "source": "inferred" if is_cat else "excluded",
            "kind": "category" if is_cat else "excluded",
            "is_promo": False, "connected": is_cat,
            "in_category_tree": is_cat,
            "flags": ([] if cts else ["no_tag_rule"]),
            "_parent_tag": parent_tag,
        }

    # inferred parent -> child edges
    edges = []
    for parent, kids in KH.HIERARCHY.items():
        pg = tag2gid.get(parent)
        if not pg:
            continue
        for kt in kids:
            cg = tag2gid.get(kt)
            if cg and cg != pg:
                edges.append({"parent": pg, "child": cg, "sources": ["inferred"]})

    title = {g: n["title"] for g, n in nodes.items()}
    for e in edges:
        p, c = e["parent"], e["child"]
        nodes[c]["parents"].append({"gid": p, "title": title.get(p), "sources": ["inferred"]})
        nodes[p]["children"].append({"gid": c, "title": title.get(c), "sources": ["inferred"]})
        nodes[c]["ancestors"] = [p]
    for g, n in nodes.items():
        own = set(n["category_tags"])
        anc = {nodes[a]["category_tags"][0] for a in n["ancestors"] if nodes[a]["category_tags"]}
        n["inherited_tag_closure"] = sorted(own | anc)

    # synthetic nav_tree from the curated hierarchy
    def node_entry(gid):
        n = nodes[gid]
        return {"title": n["title"], "type": "COLLECTION", "gid": gid, "handle": n["handle"],
                "children": [node_entry(ch["gid"]) for ch in n["children"]]}
    nav_tree = []
    for parent in list(KH.HIERARCHY) + KH.STANDALONE:
        pg = tag2gid.get(parent)
        if pg:
            nav_tree.append(node_entry(pg))

    cat = [n for n in nodes.values() if n["in_category_tree"]]
    lessons = {
        "store": STORE, "slug": SLUG, "theme": theme, "active_menu": None,
        "menu_source": "none (nav blocked — inferred from collections)", "menu_fallback": False,
        "collections_total": len(nodes), "category_tree_size": len(cat),
        "vendors": None, "multi_brand": None,
        "brand_nodes": 0, "promo_excluded": sum(1 for n in nodes.values() if n["kind"] == "excluded"),
        "in_nav": 0, "primary_subcollection_source": "inferred (curated)",
        "hierarchy_edges": {"inferred": len(edges)},
        "no_tag_rule": sum(1 for n in cat if "no_tag_rule" in n["flags"]),
        "multi_tag": 0, "max_nav_depth": 2, "inferred": True,
    }
    for n in nodes.values():
        n.pop("_parent_tag", None)

    payload = {"store": STORE, "slug": SLUG,
               "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
               "active_menu": {"nav_less": True, "theme_name": theme, "note": "menus not readable; structure inferred"},
               "lessons": lessons, "brand_names": [], "edges": edges, "nav_tree": nav_tree, "nodes": nodes}

    out = PROJECT / "maps" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{SLUG}-category-tree.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # markdown
    L = [f"# {STORE} — Category Map (INFERRED, no live nav)", "",
         f"- Theme: {theme}", f"- **Structure is Claude-inferred** from {len(cols)} collections "
         f"(Klein's `menus` field is access-denied) — grouped by category name/domain, not live nav.",
         f"- Category collections: **{len(cat)}** · excluded (operational/test/promo): "
         f"{lessons['promo_excluded']}", "", "## Category tree (inferred)", ""]

    def render(entry, depth):
        n = nodes[entry["gid"]]
        tag = n["category_tags"][0] if n["category_tags"] else "—"
        L.append(f"{'  ' * depth}- **{n['title']}** (`{tag}`) — {n['products_count']} products")
        for ch in entry["children"]:
            render(ch, depth + 1)
    for top in nav_tree:
        render(top, 0)

    excluded = [n for n in nodes.values() if n["kind"] == "excluded"]
    L += ["", "## Excluded (operational / test / promo — not categories)", ""]
    L += [f"- {n['title']} (`{n['category_tags'][0] if n['category_tags'] else '—'}`)"
          for n in sorted(excluded, key=lambda x: x["title"])]
    (out / f"{SLUG}-category-tree.md").write_text("\n".join(L), encoding="utf-8")

    print(f"Klein built: {len(nodes)} collections | category={len(cat)} | excluded={lessons['promo_excluded']} | edges={len(edges)}")
    print(f"  {out / (SLUG + '-category-tree.json')}")


if __name__ == "__main__":
    main()
