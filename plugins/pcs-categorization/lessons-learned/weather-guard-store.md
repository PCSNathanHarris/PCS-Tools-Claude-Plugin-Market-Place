# weather-guard-store — categorization lessons

_Read at the start of each run; appended at the end. Established heuristics float to the top._

## Store shape
- **This store is now Spyder Supply** (rebranded from Weather Guard / "truck box outlet") and is **Spyder-only
  front-facing**. The category tree is the **Spyder hierarchy only** (Drilling and Driving, Sawing, Surface
  Prep, Shop By Series, Shop by Trade). `brand_names` is empty (single-brand tree).
- **SKIP all Weatherguard / truck-box items** — they do **not** need categorizing and must **not** be sent to
  review. The engine enforces this: `STORE_SKIP_VENDORS["weather-guard-store"] = {"weatherguard"}` drops any
  product whose vendor is Weatherguard at gather time (like JTB's box-with-tools `remove` skip). Those items
  keep `New Item V2` and are simply ignored.
- **Trade tags** (Automotive, Carpentry, Electrical, Fabrication, Flooring, HVAC, Landscaping, Plumbing) are
  separate top-level *Shop by Trade* collections — **not ancestors** of the product-type leaves. The closure
  never touches them; leave any existing trade tags as-is.

## Established heuristics (keyword → bottom-most node)
- **Reciprocating saw blades** (bi-metal "wood with nails" / "metal" / "medium/thin metal") → **Spyder Wood
  and Metal Cutting Blades** (the only metal-capable recip leaf). Diamond-grit recip "for tile and masonry"
  → **Spyder Masonry Blades**.
- **Circular saw blades**: composite decking / cellular PVC → **Spyder Decking Blades**. Aluminum or
  aluminum-and-plastic (non-ferrous, TCG) → stay at the **Spyder Circular Saw Blades** parent — the
  **"Steel Blades" leaf is for ferrous steel, NOT aluminum**.
- **Masonry/concrete drilling**: "Multi-Construction Masonry Drill Bit" (tile/wood/concrete/brick, impact
  shank) → **Spyder Masonry Bits**. "Impact Shank / Rotary Hammer / Three-Flat Grip Shank Hammer Drill Bit"
  for concrete & masonry (explicitly non-SDS) → **Spyder Hammer Drill Bits**. Glass/tile carbide bits
  (often tag `Tile`) → **Spyder Glass & Tile Bits**.
- **Jig saw blade sets** → **Spyder Jig Saw Blades**.

## Open edge cases / candidates for new categories
- **Weatherguard truck tool boxes / box parts / truck equipment** → **SKIPPED** (vendor skip above; store is
  Spyder-only now). No longer categorized or sent to review.
- **Installer / bell-hanger bits** (Spyder 17001/17003/17004) → no "Installer Bits" leaf; Wood Drilling
  children (auger/spade/clean-cutting/countersink) don't fit → **review**. Candidate new leaf
  "Installer Bits" under Drilling and Driving.
- **Concrete-anchor flat-shank bit** (950079) placed in **Hammer Drill Bits** (medium confidence) — could
  alternatively be Masonry Bits; watch for a clearer signal.
- "Metal Cutting" bi-metal recip blades placed in **Wood and Metal Cutting Blades** (medium) — revisit if a
  dedicated metal-only recip leaf is ever added.

## Run log
### 2026-W26 (2026-06-26) — first run
- eligible=48, classified=41, NIV2 removed=41, CL-categorized=41, review=7, new categories=0.
- By node: Hammer Drill Bits 16, Wood and Metal Cutting Blades 9, Masonry Bits 6, Glass & Tile Bits 5,
  Circular Saw Blades (parent) 2, Decking Blades 1, Masonry Blades (recip) 1, Jig Saw Blades 1.
- Review (7): 4 Weatherguard truck-box items + 3 Spyder installer bits (see review-queue / Drive).
- ~18 closure tags were already present as anchors (idempotent no-ops) — expected.

### Policy update (2026-06-26)
- Store confirmed as **Spyder Supply**, Spyder-only front-facing. **Weatherguard / truck-box items are now
  skipped** (vendor skip), not reviewed — so the 4 WG items from the W26 run drop out of future candidates
  (only the 3 Spyder installer bits remain for review until an Installer Bits category exists).
- "All product card info" now explicitly includes **`facets_product_type`** + **all product metafields**
  (structured + unstructured); the gather surfaces them in candidates.json for classification.
