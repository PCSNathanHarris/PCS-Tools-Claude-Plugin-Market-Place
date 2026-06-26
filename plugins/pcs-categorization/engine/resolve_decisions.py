"""
Resolve Claude's classifications to exact category tags + prep MCP write batches.
Read-only against Shopify (writes only local files). Run, verify the printed resolution,
THEN apply the batch files via shopify_bulk_apply_tags.
"""

import json
from collections import defaultdict, deque
from pathlib import Path

PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)
SLUG, WEEK = "mts", "2026-W26"

GENERIC = {
    "Air Tools", "Cordless Tools", "Electrician's Tools", "Hand Tools", "Jobsite Equipment",
    "Lasers", "Lawn and Garden", "Material Handling", "Paint and Chemicals", "Plumbing Tools",
    "Safety Equipment", "Test and Measurement", "Tool Belts and Bags", "Truck and Van Equipment",
}

# Claude's classifications: product_id -> (generic root, leaf title or None for top-level)
DECISIONS = {
    "9327913468157": ("Plumbing Tools", "Pipe and Tube Cutters"),
    "9327913173245": ("Paint and Chemicals", "Lubricants"),
    "9327912812797": ("Hand Tools", "Wrenches"),
    "9327912583421": ("Plumbing Tools", "Drilling and Tapping"),
    "9327912288509": ("Plumbing Tools", "Pipe and Tube Cutters"),
    "9327912059133": ("Plumbing Tools", "Pipe and Tube Cutters"),
    "9327911829757": ("Plumbing Tools", "Pipe Vises"),
    "9327911600381": ("Plumbing Tools", "Pipe Vises"),
    "9327911305469": ("Hand Tools", "Wrenches"),
    "9327911010557": ("Plumbing Tools", "Pipe Vises"),
    "9317151113469": ("Lawn and Garden", "String Trimmers"),
    "8206523138301": ("Air Tools", "Nailers"),
    "8206517043453": ("Jobsite Equipment", "Jobsite Storage"),
    "8206516912381": ("Jobsite Equipment", "Jobsite Storage"),
    "8206515011837": ("Lawn and Garden", "String Trimmers"),
    "8206514913533": ("Lawn and Garden", "Mowers"),
    "8206509048061": ("Cordless Tools", "Batteries and Chargers"),
    "8206503280893": ("Jobsite Equipment", "Ladders"),
    "8206502691069": ("Safety Equipment", "Fall Protection"),
    "8206492860669": ("Test and Measurement", None),
    "8206490075389": ("Jobsite Equipment", "Locks and Security"),
    "8206485422333": ("Hand Tools", "Wrenches"),
    "8206485291261": ("Plumbing Tools", "Drain Cleaning"),
    "8206472446205": ("Plumbing Tools", "Pressing Technology"),
    "8206457864445": ("Plumbing Tools", "Drain Cleaning"),
    "8206449705213": ("Electrician's Tools", "Cable Cutters"),
    "8206448165117": ("Plumbing Tools", "Inspection Tools"),
}
REVIEW = {"9303096656125", "8206503674109", "8206503510269"}

mp = json.load(open(PROJECT / "maps" / SLUG / f"{SLUG}-category-tree.json", encoding="utf-8"))
nodes = mp["nodes"]
title_of = {g: n["title"] for g, n in nodes.items()}

children, parent_of = defaultdict(set), defaultdict(set)
for e in mp["edges"]:
    if set(e["sources"]) & {"nav", "linklist", "metafield"}:
        children[e["parent"]].add(e["child"]); parent_of[e["child"]].add(e["parent"])
roots = [g for g, n in nodes.items() if n["in_active_nav"]]
seen, dq = set(roots), deque(roots)
while dq:
    g = dq.popleft()
    for c in children[g]:
        if c not in seen:
            seen.add(c); dq.append(c)
generic_root_gids = {g for g in seen if title_of[g] in GENERIC and not parent_of[g]}
target_gids = {g for g in seen if (set(nodes[g]["ancestors"]) | {g}) & generic_root_gids}
target_tags = {t for g in target_gids for t in nodes[g]["category_tags"]}
# Brand tags = ONLY the names of brand-root trees (top-level connected non-generic nodes),
# e.g. Reed/DeWalt/Milwaukee. NOT the category tags under them (Wrenches/Drills co-occur with
# brands but are legitimate categories).
brand_tags = {t for g in seen if (g not in target_gids and not parent_of[g]) for t in nodes[g]["category_tags"]}
target_tags -= brand_tags


def find_node(root, leaf):
    root_gid = next((g for g in generic_root_gids if title_of[g] == root), None)
    if root_gid is None:
        return None
    if leaf is None:
        return root_gid
    cands = [g for g in target_gids if (title_of[g] == leaf) and (root_gid in (set(nodes[g]["ancestors"]) | {g}))]
    return cands[0] if cands else None


cand = {c["product_id"]: c for c in json.load(open(PROJECT / "runs" / WEEK / SLUG / "candidates.json", encoding="utf-8"))["candidates"]}

resolved = []
problems = []
for pid, (root, leaf) in DECISIONS.items():
    g = find_node(root, leaf)
    if g is None:
        problems.append((pid, root, leaf))
        continue
    tags = [t for t in nodes[g]["inherited_tag_closure"] if t in target_tags]
    resolved.append({"product_id": pid, "title": cand.get(pid, {}).get("title", "?"),
                     "vendor": cand.get(pid, {}).get("vendor", "?"),
                     "target": f"{root} > {leaf}" if leaf else root,
                     "tags_to_apply": sorted(tags), "remove_new_item_v2": True})

print("RESOLUTION (verify before writing):")
for r in resolved:
    print(f"  {r['product_id']}  {r['title'][:46]:48} -> {r['target']:40} {r['tags_to_apply']}")
if problems:
    print("\n!! UNRESOLVED (category not found in map):")
    for pid, root, leaf in problems:
        print(f"  {pid} -> {root} > {leaf}")

# write batches: one tag per product per call, <=30 pairs/call
writes = PROJECT / "runs" / WEEK / SLUG / "writes"
writes.mkdir(parents=True, exist_ok=True)
maxk = max((len(r["tags_to_apply"]) for r in resolved), default=0)
batches = []
for rank in range(maxk):
    batch = [{"product_id": r["product_id"], "tag": r["tags_to_apply"][rank]}
             for r in resolved if len(r["tags_to_apply"]) > rank]
    for i in range(0, len(batch), 30):
        chunk = batch[i:i + 30]
        fn = writes / f"add_batch_{len(batches)+1}.json"
        fn.write_text(json.dumps(chunk, indent=2), encoding="utf-8")
        batches.append(str(fn))
remove_file = writes / "remove_niv2.json"
remove_file.write_text(json.dumps(
    [{"product_id": r["product_id"], "tag": "New Item V2"} for r in resolved if r["remove_new_item_v2"]],
    indent=2), encoding="utf-8")

# Completion marker: after removing New Item V2, tag fully-categorized products `CL-categorized`
# (tracks what Claude categorized). Same product set as the NIV2 removal.
cl_file = writes / "add_cl_categorized.json"
cl_file.write_text(json.dumps(
    [{"product_id": r["product_id"], "tag": "CL-categorized"} for r in resolved if r["remove_new_item_v2"]],
    indent=2), encoding="utf-8")

(PROJECT / "runs" / WEEK / SLUG / "decisions_final.json").write_text(json.dumps({
    "slug": SLUG, "week": WEEK, "classified": resolved,
    "review": sorted(REVIEW), "unresolved": problems,
    "add_batches": batches, "remove_file": str(remove_file), "cl_file": str(cl_file),
}, indent=2), encoding="utf-8")

total_pairs = sum(len(r["tags_to_apply"]) for r in resolved)
print(f"\nclassified={len(resolved)} review={len(REVIEW)} unresolved={len(problems)} "
      f"| add pairs={total_pairs} in {len(batches)} batches | remove NIV2={len(resolved)}")
for b in batches:
    print("  add batch:", b)
print("  remove file:", remove_file)
