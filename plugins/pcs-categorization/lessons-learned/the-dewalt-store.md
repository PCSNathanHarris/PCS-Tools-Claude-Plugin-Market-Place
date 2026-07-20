# the-dewalt-store (ATO) — lessons

## 2026-07-07 (2026-W28) — 0 eligible (no-op)
No New Item V2 non-kit items eligible. Backlog is drained. Tree-diff +73 = vocabulary-build expansion, not new
merchant collections (see PROJECT-LESSONS). No writes.

## 2026-07-13 (2026-W29) — 0 eligible (no-op)
Backlog still drained; no New Item V2 non-kit items. Tree-diff again +73 = same vocabulary-build expansion as
W28, not new merchant collections. No decisions/report/writes.

## 2026-07-20 (2026-W30) — 22 classified / 22 NIV2 removed / 0 review
New DeWalt cordless-tool wave (q3-2026 NLP). 17/22 on a battery platform. All `facets_product_type` were null —
classified from title/description. All placed confidently; nothing to review. Tree-diff +73 again = same
vocabulary-build artifact, no genuine new collections.

**Key structural pattern (like RTS):** ATO has parallel trees — pick a **Power Tools** node for `category_gid`
(gives `Power Tools` + type + `<x> power tools` ancestor) AND the matching **platform** node for `platform_gid`:
- Power Tools > Drilling & Driving > Drills = `251800903`; 20V MAX equivalent = `323493575`; FLEXVOLT Drills = `325405191`.
- Power Tools > Drilling & Driving > Impact Drivers = `251801287`; 20V MAX = `323497671`.
- Power Tools > Cutting > Saws = `251802439`; 20V MAX = `323499207`; FLEXVOLT Saws = `325409991`; 12V = `251777287`.
- Power Tools > Cutting > Grinders = `251801095`; 20V MAX = `323494407`; FLEXVOLT = `325408199`.
- Power Tools > Cutting > Oscillating Multi-Tools = `251801863`; 20V MAX = `323498567`.
- Power Tools > And more > Batteries & Chargers = `251799175`; 20V MAX = `323491399`; 12V = `251774983`; FLEXVOLT = `325400263`.
- Power Tools > And more > Combo Kits = `251799239`; 20V MAX = `323492871`; 12V = `251775751`; FLEXVOLT = `325408967`.
- Clean platform roots: 20V MAX = `325416199`, 12V MAX = `250265031`, FLEXVOLT = `325415751` (all single-tag).

**Heuristics this run:**
- ATO groups **all saw types under one `Saws` leaf** — no separate Circular/Reciprocating/Miter nodes. Miter saws,
  circular saws (incl. 60V worm-drive), recip saws all → Power Tools > Cutting > Saws.
- **Hammer drills → Drills** (no Hammer Drills node). DeWalt DCD799/DCD798 are hammer drills, filed as Drills.
- **Die grinders AND small cut-off tools → Grinders** (Power Tools > Cutting > Grinders). No dedicated Die Grinder
  or compact Cut-Off-Tool node; the `Concrete Tools > Cut-Off Saws` node (`445714399454`) is for LARGE concrete
  cut-off saws, NOT the ATOMIC 3" metalworking cut-off tool — keep those in Grinders.
- **Concrete pencil vibrator → Power Tools > Concrete Tools > Concrete Vibrators** (`445718593758`); no typed
  concrete platform node, so platform_gid = clean 20V MAX root (`325416199`).
- **Cordless ratchet (DCF513 ATOMIC ext-reach)**: no 20V MAX Ratchets node exists (only a 12V one, whose closure
  carries 12V MAX — can't use for a 20V tool). Placed at the **Drilling & Driving parent** (Power Tools
  `440951505118` + 20V MAX `440951832798`) — correct Power Tools/20V/D&D tags without a wrong-platform leaf.
- **60V MAX = FLEXVOLT** but the engine did NOT auto-detect platform on the 60V worm-drive/std circular saws
  (`platform_tags: []`). Added FLEXVOLT platform manually (`325409991`). **Watch this** — "60V MAX" naming isn't
  caught by platform detection; add FLEXVOLT by hand for 60V tools.
- **Diamond core bit → Accessories > Tool Accessories > Drill Bits** (`251786887`). **Workshop hook set / metal
  rail storage (no tools) → Accessories > Storage and Equipment** (`440952062174`).
