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
import re
from pathlib import Path

from config import data_dir

try:
    from build_category_map import STORE_SLUG
except Exception:
    STORE_SLUG = {}

PROJECT = data_dir()

# operational/workflow + promo tags that are never real category tags (kept in sync with weekly_run.py)
OPERATIONAL_TAGS = {"new item v2", "cl-categorized", "va categorization review", "categorized"}
PROMO_RE = re.compile(
    r"(eligible|buy more save more|\bbmsm\b|reg-sku-swap|sku swap|below[- ]map|"
    r"shopmil|shoptup|\bpromotions?\b|shop\w*\d{2}|\d{2}\s*off|%\s*off)", re.I)

def is_excluded_tag(t):
    return (t or "").lower() in OPERATIONAL_TAGS or bool(PROMO_RE.search(t or ""))


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
    # clear stale batch files from a previous run so writes/ only ever holds the current run's output
    for old in list(writes.glob("add_batch_*.json")) + list(writes.glob("remove_niv2.json")) \
            + list(writes.glob("add_cl_categorized.json")):
        old.unlink()

    mp = json.loads((PROJECT / "maps" / slug / f"{slug}-category-tree.json").read_text(encoding="utf-8"))
    nodes = mp["nodes"]
    brand_lc = {b.lower() for b in mp.get("brand_names", [])}

    def closure_of(x, strip_brand):
        # this node's OWN closure (leaf + trusted ancestors); never a cross-node union.
        # category nodes: brand names stripped. brand nodes: brand tags kept (intended).
        def keep(lst):
            return [c for c in lst if not is_excluded_tag(c)
                    and ((not strip_brand) or c.lower() not in brand_lc)]
        clos = keep(x.get("inherited_tag_closure") or [])
        if not clos:
            clos = keep(x.get("category_tags") or [])
        return sorted(set(clos))

    # resolve a chosen node BY gid -> exact tag set. ALL non-promo nodes are resolvable: category-kind
    # (nav + floating, brand-stripped) and brand-kind (Shop-by-Brand tree, brand tags kept). A product's
    # add-set = the union of its chosen category_gid closure + optional brand_gid closure.
    gid_to = {}        # gid -> (title, closure)
    tag_to_gids = {}   # bare category leaf tag -> {gids}  (fallback only; used when unambiguous)
    for x in nodes.values():
        kind = x.get("kind")
        if kind == "category":
            clos = closure_of(x, strip_brand=True)
        elif kind == "brand":
            clos = closure_of(x, strip_brand=False)
        else:
            continue  # promo (or unknown) — never a tag target
        if not clos:
            continue
        gid_to[x["gid"]] = (x.get("title"), clos)
        if kind == "category":
            for t in x.get("category_tags", []):
                tag_to_gids.setdefault(t, set()).add(x["gid"])

    # no-zero-tags fallback: product_id -> vendor brand-root gid (from this run's candidates.json).
    # When a decision can't resolve to any real node, the product still gets its top-level brand
    # collection tag rather than zero tags. Truly unplaceable (no brand root) is the only review case.
    fallback_by_pid = {}
    cand_path = run_dir / "candidates.json"
    if cand_path.exists():
        cj = json.loads(cand_path.read_text(encoding="utf-8"))
        for c in cj.get("candidates", []):
            fb = c.get("fallback_brand_gid")
            if fb:
                fallback_by_pid[str(c["product_id"])] = fb

    raw = json.loads(Path(a.decisions).read_text(encoding="utf-8"))
    decisions = raw.get("decisions", raw) if isinstance(raw, dict) else raw

    confident, review, fellback = [], [], []

    def place(pid, title, reason):
        # last-resort: tag with the vendor brand-root so nothing is left untagged; else true review.
        fb = fallback_by_pid.get(pid)
        if fb and fb in gid_to:
            confident.append({"product_id": pid, "title": title, "category": gid_to[fb][0],
                              "tags_to_add": gid_to[fb][1], "fallback": True})
            fellback.append({"product_id": pid, "title": title, "fallback_to": gid_to[fb][0], "reason": reason})
        else:
            review.append({"product_id": pid, "title": title, "reason": reason})

    for d in decisions:
        pid = str(d.get("product_id"))
        # a product may carry up to three NON-EXCLUSIVE picks: category-tree, brand-tree, and
        # battery-platform-tree (M18/M12/MX FUEL, 20V MAX/FLEXVOLT, LXT/XGT, …). Closures are unioned.
        picks = [g for g in (d.get("category_gid"), d.get("brand_gid"), d.get("platform_gid")) if g]
        tag = d.get("category_tag")
        title = d.get("title")
        if d.get("review") or d.get("confidence") == "low" or (not picks and not tag):
            place(pid, title, d.get("reason") or "low confidence / no category chosen")
        elif picks:  # precise: union of each chosen node's own closure
            missing = [g for g in picks if g not in gid_to]
            valid = [g for g in picks if g in gid_to]
            if valid:  # use whatever resolved (don't lose a good pick over a typo'd sibling)
                add = sorted({t for g in valid for t in gid_to[g][1]})
                confident.append({"product_id": pid, "title": title,
                                  "category": tag or gid_to[valid[0]][0], "tags_to_add": add})
            else:
                place(pid, title, f"chosen node(s) not in the store's collections: {missing}")
        else:  # bare tag, no gid -> only safe when it maps to exactly one category node
            gids = tag_to_gids.get(tag)
            if gids and len(gids) == 1:
                confident.append({"product_id": pid, "title": title, "category": tag,
                                  "tags_to_add": gid_to[next(iter(gids))][1]})
            elif gids:
                place(pid, title, f"category '{tag}' is ambiguous ({len(gids)} nodes) — provide category_gid")
            else:
                place(pid, title, f"chosen category '{tag}' is not in the store's collections")

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
    (run_dir / "fallback-tagged.json").write_text(json.dumps(
        {"store": a.store, "slug": slug, "week": a.week, "count": len(fellback),
         "note": "tagged with the vendor brand-root only (no specific category found) — refine later",
         "items": fellback}, indent=2), encoding="utf-8")
    (run_dir / "apply-summary.json").write_text(json.dumps({
        "store": a.store, "slug": slug, "week": a.week,
        "confident": len(confident), "fallback": len(fellback), "review": len(review),
        "add_batches": batches, "remove_file": str(writes / "remove_niv2.json"),
        "cl_file": str(writes / "add_cl_categorized.json"), "review_file": str(run_dir / "review-queue.json"),
    }, indent=2), encoding="utf-8")

    print(f"apply-prep {slug} {a.week}: confident={len(confident)} (incl. fallback={len(fellback)}) "
          f"review={len(review)} add_batches={len(batches)}")
    for b in batches:
        print("  add:    ", b)
    print("  remove: ", writes / "remove_niv2.json")
    print("  cl:     ", writes / "add_cl_categorized.json")
    print("  review: ", run_dir / "review-queue.json")


if __name__ == "__main__":
    main()
