# wood-shop-outlet — categorization lessons

_Read at the start of each run; appended at the end. Established heuristics float to the top._

## Store shape
- **Now branded "Pro Work Supply"** — a **3M-only superstore** (single-brand: 3M). Like the other single-OEM
  stores, **brand = vendor (3M)**: there is no brand branch and tagging is **category-only** (never tag "3M").
- **Backlog is mostly PRE-categorized — not net-new work.** The large `New Item V2` count (~9,267 as of
  2026-06-26) is mostly products that were **categorized at launch** and simply still carry the `New Item V2`
  tag. Expect most candidates to already hold correct category anchors. When draining: confirm the existing
  category tags, apply the node closure (largely no-ops), then remove `New Item V2` + add `CL-categorized` to
  finalize — don't treat these as un-categorized. **Low priority** vs. MTS. See [[project-automated-categorization]].

## 2026-07-07 (2026-W28) — 0 eligible (no-op). Backlog stays drained (categorized at launch). Tree-diff +629 = 3M vocab-build, not new collections. No writes.

## 2026-07-13 (2026-W29) — 0 eligible (no-op). Backlog stays drained. Tree-diff +630 = 3M vocab-build, not new collections. No writes.

## 2026-07-20 (2026-W30) — 0 eligible (no-op)
Backlog drained; no New Item V2 non-kit items. Tree-diff +630 = vocabulary rebuild artifact, not new merchant collections. No decisions/report/writes.

## 2026-W31 (2026-07-28) — 0 eligible (no-op)
No `New Item V2` non-kit items outstanding. Backlog drained. Tree-diff +630 = vocabulary-rebuild artifact (full nav+floating vocab surfaced), NOT genuine new merchant collections; none created (read-only). No decisions/report/tag-writes.

## 2026-08-03 (2026-W32) — 0 eligible (no-op)
No `New Item V2` non-kit items; nothing to classify. Tree diff +630; local tree updated, no collections created. No writes.
**Flag:** the tree grew 239 -> 869 category tags (+630), and the new names are all real 3M product
families (tapes, adhesives, filters, wound-care dressings, …) rather than the usual vocabulary-rebuild
noise. Looks like a genuine 3M catalog build-out. No impact this run (eligible=0), but these become
valid targets next run — worth confirming with a human that the full 3M line is meant to be navigable.
