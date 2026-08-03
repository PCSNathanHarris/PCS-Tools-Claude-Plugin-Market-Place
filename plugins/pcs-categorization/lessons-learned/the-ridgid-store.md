# the-ridgid-store — lessons

## 2026-07-07 (2026-W28) — 0 eligible (no-op)
No NIV2 non-kit items. No writes.

## 2026-07-13 (2026-W29) — 2 classified / 2 NIV2 removed / 0 review
- **FlexShaft Retrieval Magnets** (80093 small, 80103 large — ferromagnetic-object retrievers for FlexShaft
  drain machines) → `Drain Cleaning > Drain Cleaning Accessories 453635375413` (`['Drain Cleaning','Drain
  Cleaning Accessories']`). No deeper leaf fits a retrieval magnet (leaves are Augers/Cutters, Drum Cables,
  Sectional Cables) — the generic Drain Cleaning Accessories node is the home for FlexShaft accessories.
- Tree-diff +49 = vocabulary rebuild artifact.

## 2026-07-20 (2026-W30) — 2 classified / 2 NIV2 removed / 0 review
- **FlexShaft carbide circular chain / descaling chain** (80888 KM-1004 4" carbide chain for 5/16" cable; facet
  `Drain Cleaning Cables`) → `Drain Cleaning > Drain Cleaning Accessories` (`453635375413`) — same FlexShaft-
  accessory home as the W29 retrieval magnets. The deeper `Augers and Cutters` leaf (`493535101237`) is
  **Sectional** augers/cutters; a FlexShaft chain is NOT sectional, so stay at the parent node.
- **Replacement part for a pipe cutter** (43063 Side Handle for the 238-P Soil Pipe Cutter) → `Ridgid Pipe and
  Tube Accessories` (`453654774069`, `[Pipe and Tube Accessories]`). Tree-diff +49 = vocabulary rebuild artifact.

## 2026-07-28 (2026-W31) — 1 classified / 1 NIV2 removed / 1 review
- **Hydraulic ram/cylinder replacement part for 258/258XL pipe cutters** (59517) → `Ridgid Pipe and Tube
  Accessories` (`453654774069`) — same pattern as the W30 pipe-cutter side handle: a replacement part that
  NAMES its parent pipe-cutter model goes to Pipe and Tube Accessories.
- **REVIEW — generic replacement knob with no parent tool** (92802 Plunger Knob): title/description name no
  parent tool, and Ridgid has NO generic "Replacement Parts" bucket. Its `*-Accessories` nodes are all
  product-line-specific (Drain Cleaning, Pressing, Pipe & Tube, Hand Tool, Knockout, Threading, Vacuum,
  SeeSnake, Water Jetting, Tubing Tool, Inspect & Locate). **Heuristic:** a replacement part is placeable only
  when it names/implies its parent tool or line; a bare "knob/screw/spring/knob"-type part with no parent →
  review (human looks up the MPN). Do not guess a line for a generic small part.

## 2026-08-03 (2026-W32) — 0 classified / 0 NIV2 removed / 1 review
Single eligible item, and it is the **same Ridgid 92802 Plunger Knob** that went to review in W31 — 2nd
consecutive week. Tree diff +49 (vocabulary-build expansion); nothing created.
- **Confirmed: this store has NO generic Replacement Parts bucket.** Every parts/accessory node is
  type-specific: `Ridgid Hand Tool Accessories` (648025440565), `Ridgid Pipe and Tube Accessories`
  (453654774069), `Ridgid Pressing Accessories` (453633966389), `Ridgid Tubing Tool Accessories`
  (648025211189), `Ridgid Knockout Accessories` (652943360309), `Ridgid Inspect & Locate Accessories`
  (453636030773), `Drain Cleaning > Drain Cleaning Accessories` (453635375413), `Pipe Threading > ... >
  Threading Accessories` (453651530037), `SeeSnake Accessories` (493483589941), `Ridgid Vacuum Accessories`
  (189793411), `Ridgid Water Jetting Accessories` (189795331).
  A bare part that names no parent tool cannot be placed in any of them without guessing a tool family, so it
  correctly goes to review (W31 project lesson). **Ask for a generic `Replacement Parts` collection** — it would
  clear this recurring class permanently.
