"""
Build a store's category map / tree from its LIVE navigation + smart-collection rules,
combining THREE hierarchy sources (each edge is tagged with where it came from):

  1. nav       — the live active main menu (parent > child nesting)
  2. metafield  — the collection `custom.subcollections_list` metafield (when present)
  3. template   — `collection-list` sections inside each collection's theme template
                  (block.settings.collection -> child handle). Backup source for stores
                  where the metafield is missing (e.g. JTB).

  python build_category_map.py --store knaack-store
  python build_category_map.py --store knaack-store --menu-handle updated-navigation

Outputs under ../maps/<slug>/: <slug>-category-tree.json + .md
Strictly read-only. Category tags come only from TAG rule-conditions (VENDOR ignored).
"""

import argparse
import datetime
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

from config import get_store_credentials
from shopify_read_client import ShopifyReadClient

# Promotion / sales / operational collections to EXCLUDE from the category tree.
PROMO_RE = re.compile(
    r"(sale|deal|clearance|promo|blowout|closeout|liquidation|rebate|bogo|bmsm|"
    r"\bfree\b|free-|-free|\bnlp\b|bfcm|black.?friday|cyber|holiday|christmas|halloween|"
    r"father|mother|memorial|labor.?day|prime.?day|red.?hot|price.?cut|price.?slash|"
    r"top.?pick|top.?bundle|deal.?days|add.?on|savings|special-|markdown|discount|"
    r"\bq[1-4]\b|20\d\d|\d{1,2}[.\-]\d{1,2}[.\-]\d{2,4})",
    re.I,
)


def is_promo(handle, title):
    return bool(PROMO_RE.search(handle or "") or PROMO_RE.search(title or ""))

HERE = Path(__file__).resolve().parent
PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)
STORE_SLUG = {"knaack-store": "jtb", "toolup-my-tool-store": "mts"}

HEADER_GROUP_ASSET = "sections/header-group.json"
SUBCOLL_NAMESPACE = "custom"
SUBCOLL_KEY = "subcollections_list"

_ITEM = "id title type url resourceId"
MENUS_QUERY = f"""
query Menus($after: String) {{
  menus(first: 50, after: $after) {{
    pageInfo {{ hasNextPage endCursor }}
    nodes {{ id title handle
      items {{ {_ITEM}
        items {{ {_ITEM}
          items {{ {_ITEM}
            items {{ {_ITEM} }} }} }} }} }}
  }}
}}
"""

COLLECTION_FIELDS = """
  id title handle updatedAt templateSuffix
  productsCount { count }
  ruleSet { appliedDisjunctively rules { column relation condition } }
  subcoll: metafield(namespace: "%s", key: "%s") { value type }
""" % (SUBCOLL_NAMESPACE, SUBCOLL_KEY)

NODES_QUERY = "query($ids:[ID!]!){ nodes(ids:$ids){ __typename ... on Collection {%s} } }" % COLLECTION_FIELDS
BY_HANDLE_QUERY = "query($q:String!){ collections(first:1, query:$q){ nodes {%s} } }" % COLLECTION_FIELDS


# ── Active-menu resolution ──────────────────────────────────────────────────
_MENU_KEYS = ("navigation_menu", "menu", "main_menu", "main_linklist", "menu_main", "desktop_menu")


def _menu_from_settings(st):
    if not isinstance(st, dict):
        return None
    return next((st[k] for k in _MENU_KEYS if isinstance(st.get(k), str) and st.get(k)), None)


def _header_settings(sections):
    if not isinstance(sections, dict):
        return {}
    hdr = sections.get("header") or next(
        (v for v in sections.values() if isinstance(v, dict) and "header" in str(v.get("type", "")).lower()), {})
    return hdr.get("settings", {}) if isinstance(hdr, dict) else {}


def _read_asset_json(client, theme_id, key):
    try:
        v = client.rest_get(f"themes/{theme_id}/assets.json", {"asset[key]": key}).get("asset", {}).get("value")
        return json.loads(v or "{}")
    except Exception:
        return {}


def resolve_active_menu(client: ShopifyReadClient) -> dict:
    """Resolve the live theme's main menu handle across theme families."""
    themes = client.rest_get("themes.json").get("themes", [])
    main = next((t for t in themes if t.get("role") == "main"), None)
    if not main:
        raise RuntimeError("No live (role=main) theme found.")
    tid = main["id"]
    handle, source = None, None

    grp = _read_asset_json(client, tid, HEADER_GROUP_ASSET)            # OS 2.0 header group
    handle = _menu_from_settings(_header_settings(grp.get("sections", {})))
    if handle:
        source = "header-group.json"
    if not handle:                                                     # vintage: settings_data.json
        sd = _read_asset_json(client, tid, "config/settings_data.json")
        cur = sd.get("current") if isinstance(sd.get("current"), dict) else {}
        handle = _menu_from_settings(_header_settings(cur.get("sections", {}))) or _menu_from_settings(cur)
        if handle:
            source = "settings_data.json"

    return {
        "theme_id": tid, "theme_name": main.get("name"),
        "menu_handle": handle, "menu_source": source, "resolved": bool(handle),
    }


# ── Menu walking ────────────────────────────────────────────────────────────
def handle_from_url(url):
    if url and "/collections/" in url:
        return url.rstrip("/").split("/collections/", 1)[1].split("/")[0]
    return None


def walk_menu(menu):
    nav_meta, nav_edges = {}, set()

    def visit(items, coll_ancestor, path):
        tree = []
        for it in items or []:
            is_coll = it.get("type") == "COLLECTION" and it.get("resourceId")
            gid = it.get("resourceId") if is_coll else None
            node = {"title": it.get("title"), "type": it.get("type"), "gid": gid,
                    "handle": handle_from_url(it.get("url")), "children": []}
            cur = path + [it.get("title")]
            if is_coll:
                m = nav_meta.setdefault(gid, {"nav_paths": []})
                m["nav_paths"].append(" > ".join(cur))
                if coll_ancestor:
                    nav_edges.add((coll_ancestor, gid))
                nxt = gid
            else:
                nxt = coll_ancestor
            node["children"] = visit(it.get("items"), nxt, cur)
            tree.append(node)
        return tree

    return nav_meta, nav_edges, visit(menu.get("items"), None, [])


def fetch_all_menus(client):
    """All menus (paginated) + a handle->menu index. Empire stores sub-collections as
    per-collection linklists (a menu whose handle == the collection handle)."""
    menus, after = [], None
    while True:
        d = client.graphql_read(MENUS_QUERY, {"after": after})["menus"]
        menus += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            break
        after = d["pageInfo"]["endCursor"]
    return menus, {m["handle"]: m for m in menus}


def fetch_vendors(client, cap=10000):
    """Distinct product vendors = the authoritative brand list. Vendors saturate early, so a
    cap on products scanned is fine."""
    q = "query($n:Int!,$after:String){ products(first:$n, after:$after){ pageInfo{hasNextPage endCursor} nodes{ vendor } } }"
    vendors, after, got = set(), None, 0
    while got < cap:
        d = client.graphql_read(q, {"n": 250, "after": after})["products"]
        for p in d["nodes"]:
            if p.get("vendor"):
                vendors.add(p["vendor"])
        got += len(d["nodes"])
        if not d["pageInfo"]["hasNextPage"]:
            break
        after = d["pageInfo"]["endCursor"]
    return vendors


def linklist_child_edges(menu, root_gid, resolve_gid):
    """Walk a per-handle linklist; yield (parent_gid, child_gid) following its nesting,
    rooted at the owning collection. Structural (non-collection) items keep the parent."""
    edges = []

    def visit(items, parent):
        for it in items or []:
            if it.get("type") == "COLLECTION" and it.get("resourceId"):
                cg = resolve_gid(it["resourceId"])
                if cg:
                    edges.append((parent, cg))
                    visit(it.get("items"), cg)
            else:
                visit(it.get("items"), parent)

    visit(menu.get("items"), root_gid)
    return edges


# ── Collection reads ────────────────────────────────────────────────────────
def parse_subcoll_value(mf):
    if not mf or not mf.get("value"):
        return []
    try:
        parsed = json.loads(mf["value"])
    except (ValueError, TypeError):
        parsed = mf["value"]
    if isinstance(parsed, str):
        return [parsed] if parsed.startswith("gid://") else []
    if isinstance(parsed, list):
        return [g for g in parsed if isinstance(g, str) and g.startswith("gid://")]
    return []


def fetch_by_ids(client, gids):
    out = {}
    for i in range(0, len(gids), 200):
        data = client.graphql_read(NODES_QUERY, {"ids": gids[i:i + 200]})
        for n in data.get("nodes", []):
            if n and n.get("__typename") == "Collection":
                out[n["id"]] = n
    return out


def fetch_by_handle(client, handle):
    nodes = client.graphql_read(BY_HANDLE_QUERY, {"q": f"handle:{handle}"}).get("collections", {}).get("nodes", [])
    return nodes[0] if nodes else None


def all_collection_gids(client):
    """Every collection on the store (so the tree is a complete categorization vocabulary)."""
    q = "query($n:Int!,$after:String){ collections(first:$n, after:$after){ pageInfo{hasNextPage endCursor} nodes{ id } } }"
    gids, after = [], None
    while True:
        d = client.graphql_read(q, {"n": 250, "after": after})["collections"]
        gids += [n["id"] for n in d["nodes"]]
        if not d["pageInfo"]["hasNextPage"]:
            break
        after = d["pageInfo"]["endCursor"]
    return gids


def template_child_refs(client, theme_id, suffix, cache):
    """Return ordered child collection refs (handle or gid) from a template's collection-list sections."""
    if not suffix:
        return []
    if suffix in cache:
        return cache[suffix]
    key = f"templates/collection.{suffix}.json"
    refs = []
    try:
        asset = client.rest_get(f"themes/{theme_id}/assets.json", {"asset[key]": key}).get("asset", {})
        tpl = json.loads(asset.get("value") or "{}")
        for sec in tpl.get("sections", {}).values():
            if sec.get("type") != "collection-list":
                continue
            blocks = sec.get("blocks", {})
            for bid in (sec.get("block_order") or list(blocks)):
                b = blocks.get(bid, {})
                if b.get("type") != "collection":
                    continue
                ref = (b.get("settings") or {}).get("collection")
                if ref:
                    refs.append(ref)
    except Exception:
        refs = []
    cache[suffix] = refs
    return refs


def build_closure(client, theme_id, seed_gids, menu_by_handle):
    """
    Walk nav + metafield + template + per-handle-linklist references to their transitive closure.
    Returns (collections, metafield_edges, template_edges, linklist_edges).
    """
    collections, handle2gid = {}, {}
    metafield_edges, template_edges, linklist_edges = set(), set(), set()
    tpl_cache = {}
    queue = deque()

    def add(col):
        gid = col["id"]
        if gid not in collections:
            collections[gid] = col
            if col.get("handle"):
                handle2gid[col["handle"]] = gid
            queue.append(gid)
        return gid

    def resolve_gid(gid):
        if gid in collections:
            return gid
        for _, c in fetch_by_ids(client, [gid]).items():
            add(c)
        return gid if gid in collections else None

    def resolve_handle(h):
        if h in handle2gid:
            return handle2gid[h]
        col = fetch_by_handle(client, h)
        return add(col) if col else None

    for _, c in fetch_by_ids(client, sorted(seed_gids)).items():
        add(c)

    while queue:
        gid = queue.popleft()
        col = collections[gid]
        for child_gid in parse_subcoll_value(col.get("subcoll")):
            rg = resolve_gid(child_gid)
            if rg:
                metafield_edges.add((gid, rg))
        for ref in template_child_refs(client, theme_id, col.get("templateSuffix"), tpl_cache):
            if ref.startswith("gid://"):
                cgid = resolve_gid(ref)
            else:
                h = ref.split("shopify://collections/")[-1].split("/")[-1]
                cgid = resolve_handle(h)
            if cgid:
                template_edges.add((gid, cgid))
        # Empire: a menu whose handle == this collection's handle lists its sub-collections.
        submenu = menu_by_handle.get(col.get("handle"))
        if submenu:
            for (p, c2) in linklist_child_edges(submenu, gid, resolve_gid):
                linklist_edges.add((p, c2))

    return collections, metafield_edges, template_edges, linklist_edges


# ── Graph + tags ────────────────────────────────────────────────────────────
def tag_conditions(col):
    rs = col.get("ruleSet") or {}
    return [r["condition"] for r in rs.get("rules", []) if r.get("column") == "TAG"]


def ancestors_of(gid, parents):
    seen, cycle, stack = set(), False, list(parents.get(gid, ()))
    while stack:
        p = stack.pop()
        if p == gid:
            cycle = True
            continue
        if p in seen:
            continue
        seen.add(p)
        stack.extend(parents.get(p, ()))
    return seen, cycle


def build_nodes(collections, nav_meta, nav_edges, metafield_edges, template_edges, linklist_edges):
    edge_src = {}
    for e in nav_edges:
        edge_src.setdefault(e, set()).add("nav")
    for e in metafield_edges:
        edge_src.setdefault(e, set()).add("metafield")
    for e in linklist_edges:
        edge_src.setdefault(e, set()).add("linklist")
    for e in template_edges:
        edge_src.setdefault(e, set()).add("template")

    # `parents` = every source; `trusted_parents` = nav + metafield + linklist (the real
    # sub-collection structure). Template edges are noisy (copy/paste leftovers in
    # collection-list sections), so they are recorded for review but excluded from the
    # primary closure.
    parents = {g: set() for g in collections}
    trusted_parents = {g: set() for g in collections}
    for (p, c), ss in edge_src.items():
        if p in collections and c in collections:
            parents[c].add(p)
            if ss & {"nav", "metafield", "linklist"}:
                trusted_parents[c].add(p)

    title = {g: c.get("title") for g, c in collections.items()}
    nodes = {}
    for gid, col in collections.items():
        cats = tag_conditions(col)
        rs = col.get("ruleSet") or {}
        disj = rs.get("appliedDisjunctively")
        anc, cycle = ancestors_of(gid, trusted_parents)
        anc_tags = set()
        for a in anc:
            anc_tags.update(tag_conditions(collections[a]))
        anc_all, _ = ancestors_of(gid, parents)
        anc_all_tags = set()
        for a in anc_all:
            anc_all_tags.update(tag_conditions(collections[a]))
        closure = sorted(set(cats) | anc_tags)
        closure_all = sorted(set(cats) | anc_all_tags)
        template_extra = sorted(set(closure_all) - set(closure))
        in_nav = gid in nav_meta
        incoming_sources = sorted({s for (p, c), ss in edge_src.items() if c == gid for s in ss})

        flags = []
        if not cats:
            flags.append("no_tag_rule")
        if cats and set(cats).issubset(anc_tags) and parents[gid]:
            flags.append("brand_leaf_collapse")
        if not in_nav:
            flags.append("not_in_nav")
        if cycle:
            flags.append("cycle_broken")
        if len(parents[gid]) > 1:
            flags.append("multi_parent")
        if len(cats) > 1:
            flags.append("multi_tag_or" if disj else "multi_tag_and")
        if template_extra:
            flags.append("template_adds_tags")

        nodes[gid] = {
            "gid": gid, "numeric_id": gid.rsplit("/", 1)[-1],
            "title": col.get("title"), "handle": col.get("handle"),
            "template_suffix": col.get("templateSuffix") or None,
            "products_count": (col.get("productsCount") or {}).get("count"),
            "rule_set": {"applied_disjunctively": disj, "rules": rs.get("rules", [])} if rs else None,
            "category_tags": cats,
            "parents": [
                {"gid": p, "title": title.get(p), "sources": sorted(edge_src[(p, gid)])}
                for p in sorted(parents[gid])
            ],
            "children": [
                {"gid": c, "title": title.get(c), "sources": sorted(ss)}
                for (p, c), ss in sorted(edge_src.items()) if p == gid and c in collections
            ],
            "ancestors": sorted(anc),
            "inherited_tag_closure": closure,
            "inherited_tag_closure_with_template": closure_all,
            "template_extra_tags": template_extra,
            "in_active_nav": in_nav,
            "nav_paths": sorted(nav_meta.get(gid, {}).get("nav_paths", [])),
            "hierarchy_sources": incoming_sources,
            "source": "nav" if in_nav else "out_of_nav",
            "flags": flags,
        }
    return nodes, edge_src


# ── Markdown ────────────────────────────────────────────────────────────────
def render_markdown(store, slug, active, nodes, nav_tree, edge_src, generated_at):
    title = {g: n["title"] for g, n in nodes.items()}
    L = [
        f"# {store} — Category Map ({slug})",
        "",
        f"- **Generated:** {generated_at}",
        f"- **Active menu (live):** `{active['menu_handle']}` — theme `{active['theme_id']}` \"{active['theme_name']}\"",
        f"- **Collections in map:** {len(nodes)} "
        f"({sum(n['in_active_nav'] for n in nodes.values())} in nav, "
        f"{sum(not n['in_active_nav'] for n in nodes.values())} out-of-nav)",
        "",
        "Hierarchy draws on three sources, each edge tagged with its origin: **nav** (active "
        "menu), the `custom.subcollections_list` **metafield**, and **template** `collection-list` "
        "sections. The authoritative **`inherited_tag_closure`** (own + ancestor tags a product "
        "should receive) is built from **trusted** sources only (nav + metafield); **template "
        "links are recorded for review, not trusted** — several are copy/paste noise. Nodes whose "
        "template parents would add tags are flagged `template_adds_tags`. Category tags come only "
        "from `TAG` rule-conditions (`VENDOR` ignored).",
        "",
        "## Active navigation tree",
        "",
    ]

    def fmt(gid):
        n = nodes.get(gid)
        if not n:
            return ""
        tags = ", ".join(f"`{t}`" for t in n["category_tags"]) or "—"
        flags = (" ⚠ " + ",".join(n["flags"])) if n["flags"] else ""
        return f"tags: {tags} · {n['products_count']} products{flags}"

    def render(tree, depth):
        for node in tree:
            pad = "  " * depth
            if node["gid"]:
                L.append(f"{pad}- **{node['title']}** ({node['handle'] or '?'}) — {fmt(node['gid'])}")
            else:
                L.append(f"{pad}- _{node['title']}_ [{node['type']}]")
            render(node["children"], depth + 1)

    render(nav_tree, 0)

    # template subcollections per parent
    L += ["", "## Sub-collections declared in collection templates (`collection-list`)", ""]
    tpl_parents = sorted({p for (p, c), ss in edge_src.items() if "template" in ss}, key=lambda g: title.get(g) or "")
    if tpl_parents:
        for p in tpl_parents:
            kids = [(c, ss) for (pp, c), ss in edge_src.items() if pp == p and "template" in ss]
            L.append(f"- **{title.get(p)}** (`{nodes[p]['template_suffix']}`):")
            for c, ss in sorted(kids, key=lambda x: title.get(x[0]) or ""):
                also_nav = " — also in nav" if "nav" in ss else " — **template-only (not in nav under this parent)**"
                L.append(f"    - {title.get(c, c)}{also_nav}")
    else:
        L.append("_No collection templates declare sub-collections._")

    # relationships only found outside the nav
    out_edges = [(p, c, ss) for (p, c), ss in edge_src.items() if "nav" not in ss]
    L += ["", "## Parent→child links found ONLY outside the nav (backup sources)", ""]
    if out_edges:
        for p, c, ss in sorted(out_edges, key=lambda x: (title.get(x[0]) or "", title.get(x[1]) or "")):
            L.append(f"- {title.get(p, p)} → {title.get(c, c)}  _(via {', '.join(sorted(ss))})_")
    else:
        L.append("_None — the nav already covers every metafield/template link._")

    orphans = [n for n in nodes.values() if not n["in_active_nav"]]
    L += ["", "## Collections NOT in the active nav (discovered via metafield/template)", ""]
    L += [f"- **{n['title']}** ({n['handle']}) — via {', '.join(n['hierarchy_sources']) or '—'} — {fmt(n['gid'])}"
          for n in sorted(orphans, key=lambda x: x["title"] or "")] or ["_None._"]

    no_tag = [n for n in nodes.values() if "no_tag_rule" in n["flags"]]
    L += ["", "## Collections with NO category tag (review — vendor-only/manual)", ""]
    if no_tag:
        for n in sorted(no_tag, key=lambda x: x["title"] or ""):
            rules = n["rule_set"]["rules"] if n["rule_set"] else []
            txt = "; ".join(f"{r['column']} {r['relation']} {r['condition']}" for r in rules) or "manual / no rules"
            L.append(f"- **{n['title']}** ({n['handle']}) — {txt}")
    else:
        L.append("_None._")

    L.append("")
    return "\n".join(L)


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="knaack-store")
    ap.add_argument("--menu-handle", default=None)
    args = ap.parse_args()

    slug = STORE_SLUG.get(args.store, args.store)
    raw_dir = PROJECT / "data" / slug / "raw"
    map_dir = PROJECT / "maps" / slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    map_dir.mkdir(parents=True, exist_ok=True)

    domain, cid, secret = get_store_credentials(args.store)
    client = ShopifyReadClient(domain, cid, secret)

    print(f"[1/5] Resolving live active menu for {args.store} ...")
    active = resolve_active_menu(client)
    if args.menu_handle:
        active["menu_handle"], active["overridden"] = args.menu_handle, True
    print(f"      active menu = '{active['menu_handle']}' (theme {active['theme_id']} \"{active['theme_name']}\")")
    (raw_dir / "active_menu.json").write_text(json.dumps(active, indent=2), encoding="utf-8")

    print("[2/5] Pulling menus ...")
    menus, menu_by_handle = fetch_all_menus(client)
    menu = menu_by_handle.get(active["menu_handle"]) if active.get("menu_handle") else None
    if not menu:
        def _count(items):
            return sum(1 + _count(it.get("items") or []) for it in (items or []))
        cand = max(menus, key=lambda m: _count(m.get("items")), default=None)
        if not cand:
            raise SystemExit(f"No menus found for {args.store}.")
        active["menu_handle"], active["menu_fallback"], menu = cand["handle"], True, cand
        print(f"      !! menu unresolved from theme; fell back to largest menu '{cand['handle']}'")
    (raw_dir / "menu.json").write_text(json.dumps(menu, indent=2), encoding="utf-8")
    nav_meta, nav_edges, nav_tree = walk_menu(menu)
    print(f"      {len(menus)} menus; active '{active['menu_handle']}' nav collections: {len(nav_meta)}; nav edges: {len(nav_edges)}")

    print("[3/5] Reading ALL collections (rules + metafield + templates + linklists), expanding closure ...")
    seed = set(nav_meta) | set(all_collection_gids(client))
    print(f"      seeding closure with {len(seed)} collections (nav + all published)")
    collections, metafield_edges, template_edges, linklist_edges = build_closure(
        client, active["theme_id"], seed, menu_by_handle)
    (raw_dir / "collections.json").write_text(json.dumps(collections, indent=2), encoding="utf-8")
    print(f"      collections: {len(collections)}; metafield: {len(metafield_edges)}; "
          f"template: {len(template_edges)}; linklist: {len(linklist_edges)}")
    vendors = fetch_vendors(client)
    print(f"      distinct product vendors (authoritative brand list): {len(vendors)}")

    print("[4/5] Building graph + tag closures ...")
    nodes, edge_src = build_nodes(collections, nav_meta, nav_edges, metafield_edges, template_edges, linklist_edges)

    # annotate connectivity + kind (category / brand / promo) + category-tree membership
    children_trusted = defaultdict(set)
    for (p, c), ss in edge_src.items():
        if ss & {"nav", "metafield", "linklist"} and p in nodes and c in nodes:
            children_trusted[p].add(c)
    conn = {g for g, n in nodes.items() if n["in_active_nav"]}
    dq = deque(conn)
    while dq:
        g = dq.popleft()
        for c in children_trusted[g]:
            if c not in conn:
                conn.add(c); dq.append(c)
    # ── brand detection (multi-brand stores) ──────────────────────────────────
    brand_menu_gids = set()

    def _collect_colls(items, acc):
        for it in items or []:
            if it.get("type") == "COLLECTION" and it.get("resourceId"):
                acc.add(it["resourceId"])
            _collect_colls(it.get("items"), acc)

    for m in menus:  # (A) collections featured under any "brand" menu / nav branch
        if "brand" in (str(m.get("handle", "")) + str(m.get("title", ""))).lower():
            _collect_colls(m.get("items"), brand_menu_gids)
    for g, n in nodes.items():
        if any("brand" in p.lower() for p in n["nav_paths"]):
            brand_menu_gids.add(g)
    brand_menu_gids &= set(nodes)

    vendor_conditions = set()  # (B) VENDOR rule conditions
    for n in nodes.values():
        for r in (n.get("rule_set") or {}).get("rules", []):
            if r.get("column") == "VENDOR":
                vendor_conditions.add(r["condition"])
    # Multi-brand store? (navigates by brand, or carries many vendors). Vendor-name brand
    # exclusion is applied ONLY for multi-brand stores — on a single-OEM store the lone brand
    # tag sits on category collections, so excluding it would wrongly collapse the tree.
    multi_brand = bool(brand_menu_gids) or len(vendors) >= 25
    # brand_names = VENDOR rule conditions + (multi-brand only) authoritative product vendors.
    # NOT brand-menu tags (their leaves carry category tags); brand menu marks gids directly.
    brand_names = vendor_conditions | (vendors if multi_brand else set())
    brand_lc = {b.lower() for b in brand_names}

    for g, n in nodes.items():
        promo = is_promo(n["handle"], n["title"]) and g not in conn
        is_brand = g in brand_menu_gids or any(t.lower() in brand_lc for t in n["category_tags"])
        n["connected"] = g in conn
        n["is_promo"] = promo
        n["kind"] = "promo" if promo else ("brand" if is_brand else "category")
        n["in_category_tree"] = (n["connected"] or n["in_active_nav"]) and n["kind"] == "category"

    cat = [n for n in nodes.values() if n["in_category_tree"]]
    src_primary = max((("nav", len(nav_edges)), ("linklist", len(linklist_edges)),
                       ("metafield", len(metafield_edges)), ("template", len(template_edges))),
                      key=lambda x: x[1])[0]
    lessons = {
        "store": args.store, "slug": slug, "theme": active["theme_name"],
        "active_menu": active.get("menu_handle"), "menu_source": active.get("menu_source"),
        "menu_fallback": active.get("menu_fallback", False),
        "collections_total": len(nodes), "category_tree_size": len(cat),
        "vendors": len(vendors), "multi_brand": multi_brand,
        "brand_nodes": sum(1 for n in nodes.values() if n["kind"] == "brand"),
        "promo_excluded": sum(1 for n in nodes.values() if n["is_promo"]),
        "in_nav": sum(1 for n in nodes.values() if n["in_active_nav"]),
        "primary_subcollection_source": src_primary,
        "hierarchy_edges": {"nav": len(nav_edges), "linklist": len(linklist_edges),
                            "metafield": len(metafield_edges), "template": len(template_edges)},
        "no_tag_rule": sum(1 for n in nodes.values() if "no_tag_rule" in n["flags"]),
        "multi_tag": sum(1 for n in nodes.values() if any(f.startswith("multi_tag") for f in n["flags"])),
        "max_nav_depth": max((len(p.split(" > ")) for n in nodes.values() for p in n["nav_paths"]), default=0),
    }

    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    template_only = sum(1 for (p, c), ss in edge_src.items() if ss == {"template"})
    payload = {
        "store": args.store, "slug": slug, "generated_at": generated_at,
        "active_menu": active,
        "stats": {
            "collections_total": len(nodes),
            "in_nav": sum(n["in_active_nav"] for n in nodes.values()),
            "out_of_nav": sum(not n["in_active_nav"] for n in nodes.values()),
            "nav_edges": len(nav_edges),
            "metafield_edges": len(metafield_edges),
            "linklist_edges": len(linklist_edges),
            "template_edges": len(template_edges),
            "template_only_edges": template_only,
            "no_tag_rule": sum("no_tag_rule" in n["flags"] for n in nodes.values()),
            "multi_parent": sum("multi_parent" in n["flags"] for n in nodes.values()),
            "template_adds_tags": sum("template_adds_tags" in n["flags"] for n in nodes.values()),
        },
        "lessons": lessons,
        "brand_names": sorted(brand_names),
        "edges": [{"parent": p, "child": c, "sources": sorted(ss)} for (p, c), ss in edge_src.items()],
        "nav_tree": nav_tree,
        "nodes": nodes,
    }

    print("[5/5] Writing deliverables ...")
    (map_dir / f"{slug}-category-tree.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (map_dir / "lessons.json").write_text(json.dumps(lessons, indent=2), encoding="utf-8")
    (map_dir / f"{slug}-category-tree.md").write_text(
        render_markdown(args.store, slug, active, nodes, nav_tree, edge_src, generated_at), encoding="utf-8")

    print(f"\nDone. theme={active['theme_name']!r} menu={active.get('menu_handle')!r}"
          f"{' (FALLBACK)' if active.get('menu_fallback') else ''} src={active.get('menu_source')}")
    print(f"  category_tree={lessons['category_tree_size']} brand={lessons['brand_nodes']} "
          f"promo_excluded={lessons['promo_excluded']} total={lessons['collections_total']} "
          f"primary_source={lessons['primary_subcollection_source']} depth={lessons['max_nav_depth']}")
    print(f"  {map_dir / (slug + '-category-tree.json')}")


if __name__ == "__main__":
    main()
