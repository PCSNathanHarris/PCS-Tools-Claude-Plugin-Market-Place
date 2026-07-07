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

## 2026-06-30 — batch 2 (500) review (Nathan)
- Bare **Hand Tools** node = `80675569764` (closure `['Hand Tools']`) — the safe generic for manual tools.
- **Drywall Tools** = `80676487268` (`[Drywall Tools, Hand Tools]`); branded **Marshalltown Drywall Tools** =
  `80620159076`. Drywall circle cutter -> these (not brand-only).
- Proto inspection mirrors / magnetic retrievers -> Hand Tools generic (no specific mirror/retrieval leaf).
- Powers powder-actuated fastening tool (P3500) -> genuinely no tool category -> brand-only (the rare true case).
- Step Ladders = `80683204708`; Drain video systems (SeeSnake) -> Reels & Cameras `80690380900`; Anchors ->
  Fasteners `80674783332`; socket/ratchet drive accessories -> Sockets and Adapters `464334389501`.

## 2026-06-30 — dual-tree brand guarantee (batch 2)
- 3 items (MasterLock safe, MarshallTown pry bar + barrel jointer) had a category but no brand node ->
  now auto-get their vendor top-level brand collection. All 500 have a Shop-by-Brand placement; only
  the Powers powder-actuated tool lacks a category (no possible category exists).

## 2026-06-30 — batch 2 (500) WRITTEN to MTS (v1.4.2)
- 500 tagged, 0 errors. All 500 in Shop-by-Brand (dual-tree guarantee); 499 in Shop-by-Category.
- New Item V2 removed (496 + 4 already-absent); CL-categorized x500. Add-only held (promos/New Item/Undefined untouched).
- Remaining MTS NIV2 backlog ~1,987 (was 2,487).

## 2026-07-07 (2026-W28) — batch (250) WRITTEN, LIVE — 0 errors
- 250 tagged (175 anchor-confirmed via subset-match + 73 manual-by-type + 2 brand-only fallback). CL-categorized x250; New Item V2 removed (242 + 8 already-absent). Add-only held; NO forbidden tags in any batch (verified pre-write). 3 platform picks (LXT x2, M18 x1).
- Remaining MTS NIV2 backlog **~1,737** (was ~1,987). Continue supervised.
- **Method that worked well:** deepest node whose FULL closure ⊆ product's current tags = safe "confirm existing placement" (adds no wrong department, purely add-only). Brand node additionally required the **vendor token in the node path** — this caught a false positive (a Pacific Laser Systems insert had subset-matched brand node "Fluke Other"); vendor-gated match dropped it and the engine's dual-tree guarantee supplied the correct PLS brand root.
- **New keyword→node placements this run (MTS vocab):**
  - Fall protection: SRL / self-retracting lifeline → `Retractable Lanyards 80703979620`; full-body/welding/tower harness → `Body Harnesses 80703619172`; rope lifeline → `Lifeline Systems 80703881316`; cross-arm strap / rebar chain / parapet-wall anchor → `Anchor Points 80703586404`; snatch block / turnbuckle kit → `Accessories (Fall Protection) 80703553636`. (Parapet anchors carry a stale `Anchors` fastener tag — trust the title, use Anchor Points.)
  - Levels (Stabila/Reed) → `Levels 80678060132`; level **end caps** → `Replacement Parts 80711876708`.
  - Reed pipe tools: valve/curb keys, over-torque clutch, digital counter, counter case → `Valve Tools and Keys 80692576356`; pipe/tubing cutters → `Pipe Cutters 80691527780`; PE-prep / deburring / chamfer / flare / tubing-cutter kits → `Pipe/Tube Cutting & Preparation 80691429476`; plastic-pipe reamers & flange reamer → `Pipe Reamers 80691593316`; ratchet shear (PE/PP/PEX/ABS) → `Plastic Pipe Cutters 80691658852`; extended socket → `Hand Sockets 80680616036`; replacement blades/wheels/shafts → `Replacement Parts 80711876708`; magnetic coupon retainers → `Tool Accessories 80709058660`.
  - Ridgid: EZ-change faucet tool → `Faucet and Sink Installer 80692805732`; KWIK-SPIN+ → `Hand Drain Cleaners 80690675812`; copper tubing cutters → `Pipe Cutters`; cable ratchet cutter → `Hand Cable Cutters 80669573220`; 12V charger → `Batteries & Chargers 80668164196`; RP 241 → `Press Tools 80693297252`.
  - Klein: large cable stripper → `Cable Strippers 80669671524`; CL900 → `Clamp Meters 80708304996`. Southwire Maxis XD1 → `Cable Pulling Machines 80672555108`. Jet drum sander → `Sanders (Power Tools) 80694476900`. SENCO O-ring repair kit → `Replacement Parts 80711876708`.
- **2 brand-only fallback (no category exists):** Reed fiberglass soil probe rod (utility locating) and Southwire ShockShield floor cable protector. NOTE: marking these `review:true` is WRONG on a dual-tree store — the engine's dual-tree guarantee auto-converts a review/no-category decision into a vendor brand-root fallback (per universal rule 7: review is for genuine ambiguity, not "no home"). For category-less items, expect brand-only, not review.
