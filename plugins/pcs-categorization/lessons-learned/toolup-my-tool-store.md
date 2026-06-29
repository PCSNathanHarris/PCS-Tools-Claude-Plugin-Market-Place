# toolup-my-tool-store (MTS) — categorization lessons

_Read at the start of each run; appended at the end. Established heuristics float to the top._

## Store shape
- **MTS ("My Tool Store")** — a **multi-brand** store (266 vendors per the Phase-3 build → `multi_brand` = true).
  Brand exclusion applies: **brand = vendor and is stripped from category tags** (category-only). NOTE: this is a
  **separate store from the excluded `toolupstore` (TUP)** — MTS **is** in scope despite the "toolup" prefix.
- **This is the ONE backlog store that genuinely needs categorizing.** Unlike Pro Work Supply (wood-shop-outlet,
  3M-only) and Total Fastening (fasteners-store, Simpson-only) — which were mostly **categorized at launch** — and
  the-jet-store (on hold for a duplicate-creation error), MTS's `New Item V2` items (~2,987 as of 2026-06-26) are
  **real categorization work**. **Prioritize MTS** for the backlog drain.
- An inaugural sample write already ran here (27 of 30 newest categorized, `New Item V2` removed, 0 errors) —
  see `runs/2026-W26/mts/RUN-SUMMARY.md`. See [[project-automated-categorization]].

## 2026-W27 (2026-06-29) — supervised batch 1, LIVE (v1.2.3)
- 250 of the 2,737 NIV2 backlog tagged. 250 confident / 0 review / 0 errors. ~206 net-new tags (most items already partly categorized).
- Dual-tree + battery-platform both exercised: 16 platform picks (M18x6, LXTx4, M12x3, FLEXVOLTx2, XGTx1).
- Add-only confirmed live: only `New Item V2` removed; `New Item`, promos, NMFC, catalog tags all preserved. `CL-categorized` added x250.
- Mechanics: 44 product-disjoint add-rounds + chunked CL/NIV2 (apply_run emits 250-pair remove/cl files; chunk to <=30 at call time).
- Remaining MTS backlog ~2,487 — continue supervised.
