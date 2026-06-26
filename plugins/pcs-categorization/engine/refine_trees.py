"""
Refine + audit every built category tree using all available signals (offline; no API calls,
no writes to Shopify). For each maps/<slug>/<slug>-category-tree.json:

  - tighten promo detection: a collection is promo only if it matches the promo pattern AND is
    NOT connected to the category tree (so real connected categories are never dropped);
  - connect orphan categories to a parent via (a) tag-subset (brand-stripped, unambiguous) or
    (b) tag naming-prefix (`A_B` / `A - B` / `A B` -> parent tag `A`), marked source "inferred";
  - label no_tag reasons (vendor_rule / inventory_only / manual);
  - write the refined JSON back + a per-store `tree-quality.md`;
  - roll everything up into synthesis/tree-quality-rollup.md.

  python refine_trees.py
"""

import glob
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

from build_category_map import is_promo

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)


def brand_tag_set(nodes):
    bt = set()
    for n in nodes.values():
        rs = n.get("rule_set") or {}
        for r in rs.get("rules", []):
            if r.get("column") == "VENDOR":
                bt.add(r["condition"])
        if any("brand" in p.lower() for p in n["nav_paths"]):
            bt.update(n["category_tags"])
    return bt


def connected_set(nodes, edges, extra=()):
    ch = defaultdict(set)
    for e in edges:
        if set(e["sources"]) & {"nav", "metafield", "linklist", "template", "inferred"}:
            ch[e["parent"]].add(e["child"])
    for p, c in extra:
        ch[p].add(c)
    roots = [g for g, n in nodes.items() if n["in_active_nav"]]
    seen, dq = set(roots), deque(roots)
    while dq:
        g = dq.popleft()
        for c in ch[g]:
            if c in nodes and c not in seen:
                seen.add(c); dq.append(c)
    return seen


def refine(slug):
    p = PROJECT / "maps" / slug / f"{slug}-category-tree.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    nodes, edges = d["nodes"], d["edges"]
    # Trust the builder's kind (promo/brand classified with the authoritative vendor list).
    brand_lc = {b.lower() for b in d.get("brand_names", [])}
    conn0 = connected_set(nodes, edges)

    # connect orphan CATEGORY collections via subset / naming-prefix
    tagset = {g: frozenset(t for t in n["category_tags"] if t.lower() not in brand_lc) for g, n in nodes.items()}
    cat_like = {g for g, n in nodes.items() if n["kind"] == "category" and n["category_tags"]}
    tag_to_pure = {}  # exact single-tag node, for prefix matching
    for g in cat_like:
        ct = nodes[g]["category_tags"]
        if len(ct) == 1:
            tag_to_pure.setdefault(ct[0], g)
    inferred = []
    for g in list(nodes):
        n = nodes[g]
        if g in conn0 or n["kind"] != "category" or not n["category_tags"]:
            continue
        tx, parent, how = tagset[g], None, None
        if tx:  # (a) tag-subset
            sup = [y for y in cat_like if y != g and tagset[y] and tagset[y] < tx]
            if sup:
                m = max(len(tagset[y]) for y in sup)
                best = [y for y in sup if len(tagset[y]) == m]
                if len(best) == 1:
                    parent, how = best[0], "subset"
        if not parent:  # (b) naming-prefix
            for t in n["category_tags"]:
                if t.lower() in brand_lc:
                    continue
                for sep in ("_", " - ", " "):
                    if sep in t:
                        ptag = t.rsplit(sep, 1)[0].strip()
                        if ptag in tag_to_pure and tag_to_pure[ptag] != g:
                            parent, how = tag_to_pure[ptag], "prefix"
                            break
                if parent:
                    break
        if parent:
            inferred.append((parent, g, how))
    for p_, c_, _ in inferred:
        edges.append({"parent": p_, "child": c_, "sources": ["inferred"]})

    # recompute connectivity with inferred edges (kind trusted from the builder's vendor-based pass)
    conn = connected_set(nodes, edges, [(p_, c_) for p_, c_, _ in inferred])
    for g, n in nodes.items():
        n["connected"] = g in conn
        n["in_category_tree"] = (n["connected"] or n["in_active_nav"]) and n["kind"] == "category"
        if "no_tag_rule" in n["flags"]:
            cols = [r["column"] for r in (n.get("rule_set") or {}).get("rules", [])]
            n["no_tag_reason"] = "vendor_rule" if "VENDOR" in cols else ("inventory_only" if cols else "manual")

    # 4) quality findings
    cat = [n for n in nodes.values() if n["in_category_tree"]]
    disconnected = [n for n in nodes.values()
                    if n["kind"] == "category" and n["category_tags"] and not n["in_category_tree"]]
    dup = defaultdict(list)
    for g, n in nodes.items():
        if n["kind"] == "category" and tagset[g]:
            dup[tagset[g]].append(n["title"])
    duplicates = {",".join(sorted(k)): v for k, v in dup.items() if len(v) > 1}
    # case/plural tag collisions
    norm = defaultdict(set)
    for n in cat:
        for t in n["category_tags"]:
            norm[t.lower().rstrip("s")].add(t)
    collisions = {k: sorted(v) for k, v in norm.items() if len(v) > 1}

    d["refined"] = True
    d["lessons"]["category_tree_size"] = len(cat)
    d["lessons"]["inferred_connections"] = len(inferred)
    d["lessons"]["disconnected_categories"] = len(disconnected)
    d["lessons"]["duplicate_tagsets"] = len(duplicates)
    d["lessons"]["tag_case_plural_collisions"] = len(collisions)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")

    L = [f"# {slug} — tree quality audit (refined)", "",
         f"- category-tree collections: **{len(cat)}**",
         f"- orphan categories auto-connected (subset/prefix): **{len(inferred)}**",
         f"- still-disconnected categories (review): **{len(disconnected)}**",
         f"- duplicate collections (same tag-set): **{len(duplicates)}**",
         f"- no-tag categories: **{sum(1 for n in cat if 'no_tag_rule' in n['flags'])}**",
         f"- tag case/plural inconsistencies: **{len(collisions)}**", ""]
    if inferred:
        L += ["## Auto-connected orphans", ""]
        for p_, c_, how in sorted(inferred, key=lambda x: nodes[x[1]]["title"] or "")[:60]:
            L.append(f"- {nodes[c_]['title']} → **{nodes[p_]['title']}** _(via {how})_")
    if disconnected:
        L += ["", "## Still disconnected (need nav/subcollection link or a rule)", ""]
        for n in sorted(disconnected, key=lambda x: x["title"] or "")[:60]:
            L.append(f"- {n['title']} (`{','.join(n['category_tags'])}`)")
    if duplicates:
        L += ["", "## Duplicate collections (same criteria, different titles)", ""]
        for k, v in list(duplicates.items())[:40]:
            L.append(f"- `{k}` → {', '.join(sorted(set(v)))}")
    if collisions:
        L += ["", "## Tag case/plural inconsistencies", ""]
        for k, v in list(collisions.items())[:40]:
            L.append(f"- {v}")
    (PROJECT / "maps" / slug / "tree-quality.md").write_text("\n".join(L), encoding="utf-8")

    return {"slug": slug, "category_tree": len(cat), "inferred": len(inferred),
            "disconnected": len(disconnected), "duplicates": len(duplicates),
            "no_tag": sum(1 for n in cat if "no_tag_rule" in n["flags"]),
            "collisions": len(collisions)}


def main():
    summaries = []
    for f in sorted(glob.glob(str(PROJECT / "maps" / "*" / "*-category-tree.json"))):
        slug = Path(f).parent.name
        try:
            summaries.append(refine(slug))
            print(f"  refined {slug}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {slug}: {e}")
    summaries.sort(key=lambda x: -x["category_tree"])
    R = ["# Cross-store tree-quality rollup (refined)", "",
         "| Store | Category tree | Auto-connected | Disconnected | Duplicates | No-tag | Case/plural |",
         "|---|---|---|---|---|---|---|"]
    for s in summaries:
        R.append(f"| {s['slug']} | {s['category_tree']} | {s['inferred']} | {s['disconnected']} | "
                 f"{s['duplicates']} | {s['no_tag']} | {s['collisions']} |")
    R += ["", f"Fleet: category-tree={sum(s['category_tree'] for s in summaries)} · "
          f"auto-connected={sum(s['inferred'] for s in summaries)} · "
          f"still-disconnected={sum(s['disconnected'] for s in summaries)} · "
          f"duplicates={sum(s['duplicates'] for s in summaries)} · "
          f"no-tag={sum(s['no_tag'] for s in summaries)}"]
    (PROJECT / "synthesis" / "tree-quality-rollup.md").write_text("\n".join(R), encoding="utf-8")
    print(f"\nrefined {len(summaries)} stores -> synthesis/tree-quality-rollup.md")


if __name__ == "__main__":
    main()
