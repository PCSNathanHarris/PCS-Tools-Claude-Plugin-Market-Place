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

## 2026-07-13 (2026-W29) — batch (250) WRITTEN, LIVE — 0 errors
- 250 tagged (217 anchor-confirmed via full-closure subset match + 33 manual-by-type; 0 review, 0 brand-only).
  ~90 net-new category/brand tags applied (most items already partly categorized); CL-categorized x250;
  New Item V2 removed x250 (all applied, none pre-absent). Add-only held; NO forbidden/promo tags in any of
  the 44 add batches (verified pre-write). 2 platform picks (M18, LXT).
- Remaining MTS NIV2 backlog **~1,487** (was ~1,737). Continue supervised.
- **Southwire wire-pulling equipment (recurring vendor):** Maxis cable pullers (M6K, XD10) → `Cable Pulling
  Machines 80672555108`; Maxis Cable Feeder (MCF-01) → `Cable Feeder 80672424036`; Maxis Grips pulling heads
  (GPxxx) → `Grips 80672718948`; SLIDEit wire protector → `Cable Puller Accessories 80672522340`; Coilpak/wire
  cart (CK-01) → `Wire Carts 80672194660`; Pro-Jax reel axle → `Reel Jack Stands 80672161892`; MSP stud punch
  → `Stud Punches 80671965284`; MAX PUNCH draw stud → `Knockouts 80671113316` (generic; no Southwire-specific
  draw-stud node); QWIKrope 12-strand UHMWPE pulling rope → `Single Braided Rope 80672915556`. All under
  Electrician's Tools > Pulling closure.
- **Rothenberger:** RoCut ratchet-type PVC/PE/PEX cutters → `Plastic Pipe Cutters 80691658852`; replacement
  copper cutting wheels → `Replacement Parts 80711876708`.
- **Reed:** cutter-wheel ball-detent/wheel pins → `Replacement Parts 80711876708`; DEB1 plastic-pipe deburring
  tool → `Pipe/Tube Cutting & Preparation 80691429476`.
- **Klein:** power driver bit sets & double-sided combo replacement bits → `Bit Tips 80709812324` (there is NO
  "Driver Bits"/"Screwdriver Bits" category — driving bits live under Bit Tips).
- **Bosch:** router plunge/palm-router base → `Router Bases 80711942244`.
- **Jet:** parallel clamps (woodworking) → `Bar Clamps 80676061284` (a parallel clamp is a bar clamp; no
  Woodworking-Clamps node exists — existing Woodworking/Clamps tags preserved by add-only).
- **Werner:** ladder accessories (rope pulley kit, plastic top repel kit) → `Ladder Accessories 80683171940`;
  D-Rung **extension** ladders AND **podium** ladders → `Ladders 80683106404` (no dedicated Extension/Podium
  Ladder nodes; only Telescoping Extension Ladders which is a different product).
- **Safewaze/Fall Safe:** galvanized steel cable for a horizontal lifeline system → `Lifeline Systems
  80703881316`; Safelink "form link anchor" → `Anchor Points 80703586404` (trust title; the stale `Anchors`
  fastener tag is misleading — confirms the W28 parapet-anchor lesson).
- **Ridgid:** MegaPress kit (facet MegaPress Tools) → `Mega Press 80693166180`.
- **Method confirmed:** deepest node whose FULL closure ⊆ product's current category tags = safe add-only
  confirm; brand node additionally gated on vendor-token-in-path. 33 items had a brand anchor but no clean
  category subset (empty/partial cur_cat) → placed manually by title+description.
