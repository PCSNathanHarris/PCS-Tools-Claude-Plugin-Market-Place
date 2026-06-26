"""
Classify the run sample into the GENERIC category trees (brand trees excluded) and emit
reviewable decisions. Consumes runs/<week>/<slug>/candidates.json + the map. Writes nothing
to Shopify — produces decisions.{json,md} for review before the write step.

  python classify_run.py --slug mts --week 2026-W26
"""

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)

# Generic (non-brand) category roots — classification targets. Brand roots (DeWalt, Reed, …)
# are excluded; brand is carried by the product Vendor field.
MTS_GENERIC_ROOTS = {
    "Air Tools", "Cordless Tools", "Electrician's Tools", "Hand Tools", "Jobsite Equipment",
    "Lasers", "Lawn and Garden", "Material Handling", "Paint and Chemicals", "Plumbing Tools",
    "Safety Equipment", "Test and Measurement", "Tool Belts and Bags", "Truck and Van Equipment",
}
GENERIC_ROOTS = {"mts": MTS_GENERIC_ROOTS}


def norm(s):
    return " " + re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip() + " "


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="mts")
    ap.add_argument("--week", required=True)
    args = ap.parse_args()

    mp = json.load(open(PROJECT / "maps" / args.slug / f"{args.slug}-category-tree.json", encoding="utf-8"))
    nodes = mp["nodes"]
    run = PROJECT / "runs" / args.week / args.slug
    cand = json.load(open(run / "candidates.json", encoding="utf-8"))["candidates"]

    # connected tree + parent graph (trusted)
    children, parent_of = defaultdict(set), defaultdict(set)
    for e in mp["edges"]:
        if set(e["sources"]) & {"nav", "linklist", "metafield"}:
            children[e["parent"]].add(e["child"])
            parent_of[e["child"]].add(e["parent"])
    roots = [g for g, n in nodes.items() if n["in_active_nav"]]
    seen, dq = set(roots), deque(roots)
    while dq:
        g = dq.popleft()
        for c in children[g]:
            if c not in seen:
                seen.add(c); dq.append(c)

    generic = GENERIC_ROOTS[args.slug]
    generic_root_gids = {g for g in seen if (nodes[g]["title"] in generic) and not parent_of[g]}

    def under_generic(g):
        return bool((set(nodes[g]["ancestors"]) | {g}) & generic_root_gids)

    target_gids = {g for g in seen if under_generic(g)}
    target_tags = {t for g in target_gids for t in nodes[g]["category_tags"]}
    # brand tags = category tags of connected nodes NOT under a generic root (brand trees)
    brand_tags = {t for g in seen if g not in target_gids for t in nodes[g]["category_tags"]}
    target_tags -= brand_tags

    # keyword -> target node (distinctive tag = a target node's category tag that isn't a generic root tag)
    root_tags = {nodes[g]["category_tags"][0] for g in generic_root_gids if nodes[g]["category_tags"]}
    kw_index = defaultdict(list)
    for g in target_gids:
        n = nodes[g]
        depth = len(set(n["ancestors"]) & target_gids)
        for t in n["category_tags"]:
            if t in brand_tags:
                continue
            kw_index[norm(t).strip()].append((g, depth))
        # title words (helps when the distinctive tag differs from product wording)
        for w in norm(n["title"]).split():
            if len(w) >= 4:
                kw_index[w].append((g, depth))

    def closure_tags(g):
        return [t for t in nodes[g]["inherited_tag_closure"] if t in target_tags]

    def reaches_root(g):
        return bool((set(nodes[g]["ancestors"]) | {g}) & generic_root_gids)

    decisions = []
    for r in cand:
        have = set(r.get("all_tags", [])) | set(r.get("noncat_tags", [])) | set(r.get("current_category_tags", []))
        vendor_l = (r["vendor"] or "").lower()
        # 1) anchor: existing target-category tags (excluding brand/vendor)
        anchors = [t for t in have if t in target_tags and t.lower() != vendor_l]
        chosen, method, evidence = None, None, None
        if anchors:
            chosen = max((g for g in target_gids if set(nodes[g]["category_tags"]) & set(anchors)),
                         key=lambda g: len(set(nodes[g]["ancestors"]) & target_gids), default=None)
            method, evidence = "anchor", anchors
        if chosen is None:
            # 2) keyword match on title + description
            hay = norm(f"{r['title']} {r.get('description','')}")
            hay_ns = hay.replace(" ", "")
            hits = []
            for kw, refs in kw_index.items():
                if (f" {kw} " in hay) or (len(kw) >= 5 and kw.replace(" ", "") in hay_ns):
                    for g, depth in refs:
                        hits.append((g, depth, kw))
            if hits:
                hits.sort(key=lambda h: (h[1], len(h[2])), reverse=True)
                chosen, method, evidence = hits[0][0], "keyword", hits[0][2]

        if chosen is None:
            decisions.append({**pick(r), "decision": "NO_MATCH", "tags_to_add": [], "remove_new_item_v2": False})
            continue
        add = [t for t in closure_tags(chosen) if t not in have]
        decisions.append({
            **pick(r),
            "decision": "classify", "method": method, "evidence": evidence,
            "target_category": nodes[chosen]["title"], "target_handle": nodes[chosen]["handle"],
            "tags_to_add": add,
            "remove_new_item_v2": reaches_root(chosen),
        })

    (run / "decisions.json").write_text(json.dumps({"slug": args.slug, "week": args.week,
                                                    "count": len(decisions), "decisions": decisions}, indent=2), encoding="utf-8")
    L = [f"# {args.slug} — proposed decisions ({args.week}) — {len(decisions)} products", "",
         "Targets: GENERIC category trees only (brand trees excluded; brand=vendor). Tags = chosen "
         "collection's criteria + ancestors. Nothing written yet.", ""]
    for d in decisions:
        if d["decision"] == "NO_MATCH":
            L.append(f"- ❓ **{d['title'][:62]}** ({d['vendor']}) — NO MATCH — review")
            continue
        rm = "✅ remove NIV2" if d["remove_new_item_v2"] else "keep NIV2"
        L.append(f"- **{d['title'][:62]}** ({d['vendor']})")
        L.append(f"    → **{d['target_category']}** via {d['method']} ({d['evidence']}); add {d['tags_to_add'] or '—'} · {rm}")
    (run / "decisions.md").write_text("\n".join(L), encoding="utf-8")

    nm = sum(1 for d in decisions if d["decision"] == "NO_MATCH")
    print(f"decisions: {len(decisions)} | classified {len(decisions)-nm} | no-match {nm} | "
          f"target vocab {len(target_tags)} tags under {len(generic_root_gids)} generic roots")
    print(f"  {run/'decisions.md'}")


def pick(r):
    return {"product_id": r["product_id"], "gid": r["gid"], "title": r["title"], "vendor": r["vendor"]}


if __name__ == "__main__":
    main()
