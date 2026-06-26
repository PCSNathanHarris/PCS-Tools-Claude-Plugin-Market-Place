"""
Weekly run — STEP 3 (no Shopify writes here): turn Claude's classification decisions into exact
tag-write batches + a review queue. The SKILL then applies the batches via the shopify_* MCP tag
tools and uploads the review queue to Drive (+ local backup).

Decisions file (Claude writes it): JSON {"decisions": [
  {"product_id": "123", "category_tag": "Pliers", "confidence": "high"},   # bottom-most category
  {"product_id": "456", "review": true, "reason": "no clear category"}
]}
A product's full tag set = the chosen leaf tag's inherited closure (category-only, brand stripped).

  python apply_run.py --store the-milwaukee-store --week 2026-W26 --decisions <path-to-decisions.json>

Outputs (data_dir/runs/<week>/<slug>/writes/): add_batch_*.json, remove_niv2.json, add_cl_categorized.json
+ review-queue.json (local backup of low/unplaceable items) + apply-summary.json.
"""

import argparse
import json
from pathlib import Path

from config import data_dir

try:
    from build_category_map import STORE_SLUG
except Exception:
    STORE_SLUG = {}

PROJECT = data_dir()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--week", required=True)
    ap.add_argument("--decisions", required=True)
    a = ap.parse_args()

    slug = a.slug or STORE_SLUG.get(a.store, a.store)
    run_dir = PROJECT / "runs" / a.week / slug
    writes = run_dir / "writes"
    writes.mkdir(parents=True, exist_ok=True)

    mp = json.loads((PROJECT / "maps" / slug / f"{slug}-category-tree.json").read_text(encoding="utf-8"))
    nodes = mp["nodes"]
    brand_lc = {b.lower() for b in mp.get("brand_names", [])}

    def closure_of(x):
        # this node's OWN brand-stripped closure (leaf + trusted ancestors)
        clos = [c for c in x.get("inherited_tag_closure", []) if c.lower() not in brand_lc]
        if not clos:
            clos = [c for c in x.get("category_tags", []) if c.lower() not in brand_lc]
        return sorted(set(clos))

    # resolve a chosen category BY NODE (gid) -> exact tag set; never a cross-node tag union.
    gid_to = {}        # gid -> (title, closure)
    tag_to_gids = {}   # bare leaf tag -> {gids}  (fallback only; used when unambiguous)
    for x in nodes.values():
        if x.get("in_category_tree") and x.get("kind") == "category":
            clos = closure_of(x)
            if not clos:
                continue
            gid_to[x["gid"]] = (x.get("title"), clos)
            for t in x.get("category_tags", []):
                tag_to_gids.setdefault(t, set()).add(x["gid"])

    raw = json.loads(Path(a.decisions).read_text(encoding="utf-8"))
    decisions = raw.get("decisions", raw) if isinstance(raw, dict) else raw

    confident, review = [], []
    for d in decisions:
        pid = str(d.get("product_id"))
        gid = d.get("category_gid")
        tag = d.get("category_tag")
        title = d.get("title")
        if d.get("review") or d.get("confidence") == "low" or (not gid and not tag):
            review.append({"product_id": pid, "title": title,
                           "reason": d.get("reason") or "low confidence / no category chosen"})
        elif gid:  # precise: use exactly this node's closure
            if gid in gid_to:
                confident.append({"product_id": pid, "title": title,
                                  "category": tag or gid_to[gid][0], "tags_to_add": gid_to[gid][1]})
            else:
                review.append({"product_id": pid, "title": title,
                               "reason": f"chosen category node '{gid}' is not in the store's category tree"})
        else:  # bare tag, no gid -> only safe when it maps to exactly one node
            gids = tag_to_gids.get(tag)
            if not gids:
                review.append({"product_id": pid, "title": title,
                               "reason": f"chosen category '{tag}' is not in the store's category tree"})
            elif len(gids) == 1:
                confident.append({"product_id": pid, "title": title, "category": tag,
                                  "tags_to_add": gid_to[next(iter(gids))][1]})
            else:
                review.append({"product_id": pid, "title": title,
                               "reason": f"category '{tag}' is ambiguous ({len(gids)} nodes) — provide category_gid"})

    # add batches: one tag per product per call, <=30 pairs/call
    maxk = max((len(c["tags_to_add"]) for c in confident), default=0)
    batches = []
    for rank in range(maxk):
        batch = [{"product_id": c["product_id"], "tag": c["tags_to_add"][rank]}
                 for c in confident if len(c["tags_to_add"]) > rank]
        for i in range(0, len(batch), 30):
            fn = writes / f"add_batch_{len(batches) + 1}.json"
            fn.write_text(json.dumps(batch[i:i + 30], indent=2), encoding="utf-8")
            batches.append(str(fn))
    (writes / "remove_niv2.json").write_text(json.dumps(
        [{"product_id": c["product_id"], "tag": "New Item V2"} for c in confident], indent=2), encoding="utf-8")
    (writes / "add_cl_categorized.json").write_text(json.dumps(
        [{"product_id": c["product_id"], "tag": "CL-categorized"} for c in confident], indent=2), encoding="utf-8")
    (run_dir / "review-queue.json").write_text(json.dumps(
        {"store": a.store, "slug": slug, "week": a.week, "count": len(review), "items": review}, indent=2), encoding="utf-8")
    (run_dir / "apply-summary.json").write_text(json.dumps({
        "store": a.store, "slug": slug, "week": a.week,
        "confident": len(confident), "review": len(review),
        "add_batches": batches, "remove_file": str(writes / "remove_niv2.json"),
        "cl_file": str(writes / "add_cl_categorized.json"), "review_file": str(run_dir / "review-queue.json"),
    }, indent=2), encoding="utf-8")

    print(f"apply-prep {slug} {a.week}: confident={len(confident)} review={len(review)} add_batches={len(batches)}")
    for b in batches:
        print("  add:    ", b)
    print("  remove: ", writes / "remove_niv2.json")
    print("  cl:     ", writes / "add_cl_categorized.json")
    print("  review: ", run_dir / "review-queue.json")


if __name__ == "__main__":
    main()
