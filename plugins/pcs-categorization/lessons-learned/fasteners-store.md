# fasteners-store — categorization lessons

_Read at the start of each run; appended at the end. Established heuristics float to the top._

## Store shape
- **Now branded "Total Fastening"** — an **everything-Simpson (Simpson Strong-Tie) mega store** (single-brand:
  Simpson). **Brand = vendor (Simpson)**: no brand branch, tagging is **category-only**.
- Hierarchy source: this is the **only** fleet store whose sub-collection structure comes from the
  **`custom.subcollections_list` metafield** (per the Phase-3 build) — trust it as a primary source.
- **Backlog is mostly PRE-categorized — not net-new work.** The large `New Item V2` count (~6,778 as of
  2026-06-26) is mostly products that were **categorized at launch** and still carry the `New Item V2` tag.
  Confirm existing anchors, apply the node closure (largely no-ops), then remove `New Item V2` + add
  `CL-categorized` to finalize. **Low priority** vs. MTS. See [[project-automated-categorization]].

## 2026-07-07 (2026-W28) — 0 eligible (no-op). Backlog stays drained (categorized at launch). No writes.

## 2026-07-13 (2026-W29) — 0 eligible (no-op). Backlog stays drained. Tree-diff +34 rebuild artifact. No writes.

## 2026-07-20 (2026-W30) — 3 classified / 3 NIV2 removed / 0 review
First non-zero run here — 3 net-new Simpson items, all placed confidently. Node closures carry the store's
`primary` NetSuite subcollection marker (expected, part of each node's tag definition). Heuristics:
- **SDWS Strong-Drive exterior timber screw** → `Fasteners > Simpson Construction Screws > Simpson Structural
  Wood Screws` (`634913325423`). SDWS = structural wood/timber screw.
- **WSC collated wood screw for the Quik Drive auto-feed system** → `Simpson Quik Drive Screws > Simpson Quik
  Drive Wood Screws` (`634943045999`). Collated + Quik-Drive-specific → the Quik Drive branch, not generic
  collated screws.
- **Acrylic-Tie mixing nozzle for AT-XP adhesives** → `Simpson Adhesive Anchors > Simpson Adhesive Anchoring
  Accessories` (`634939769199`). Adhesive dispensing/mixing accessories live under Adhesive Anchoring Accessories.
- Tree-diff +34 = vocabulary rebuild artifact.
