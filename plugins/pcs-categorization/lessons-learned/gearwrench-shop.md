# gearwrench-shop — lessons

## 2026-07-07 (2026-W28) — 1 classified / 1 NIV2 removed / 0 review
- Adjustable wrench SET w/ EVA foam tray -> `Wrenches > Wrench Sets 393232023797` (`[Wrench Sets, Wrenches]`). Organizer rule 5: a foam tray that INCLUDES the tools stays in the tool category, not Storage. No dedicated "Adjustable Wrenches" node; Wrench Sets is the deepest fit for a set.

## 2026-07-13 (2026-W29) — 3 classified / 3 NIV2 removed / 0 review
- **Utility carts with NO tools included** (GWPSCM plastic, GWMSC steel, GWPSCS — 2-shelf rolling carts,
  locking casters) → `Equipment > Storage 394025402613` (`['Jobsite Storage','Shop Equipment']`). Organizer
  rule 5: cart with no tools = storage. There is no dedicated "Carts"/"Utility Carts" node — Equipment > Storage
  is the storage home on this store.
- Tree-diff +14 rebuild artifact.

## 2026-07-20 (2026-W30) — 5 classified / 5 NIV2 removed / 0 review
- **Bolt Biter Nut Extractors & Drivers** (86187, 86184 — bi-directional damaged-fastener removal sockets) →
  `Specialty > Extraction Tools` (`394019832053`, `[Extraction Tools, Specialty]`). The GearWrench "Bolt Biter"
  removal line lives under Specialty > Extraction Tools, not Sockets.
- **Bolt Biter extraction SCREWDRIVER** (86092) → `Hand Tools > Screwdrivers` (`394021077237`) — it's a
  screwdriver form factor (Extraction Tools would also be defensible for the Bolt Biter family; chose the physical
  category so screwdriver shoppers find it).
- **Flex-head ratcheting combination wrench** (86717, already anchored Hand Tools/Ratcheting Wrenches/Wrenches) →
  `Wrenches > Ratcheting Wrenches` (`396306874613`) — confirmed existing anchors.
- **Mini toolbox, no tools included** (GWBXMINIS, facet `Tool Boxes`) → `Equipment > Storage` (`394025402613`) —
  same storage home as the W29 carts (no dedicated Tool Boxes node). Tree-diff +14 rebuild artifact.

## 2026-07-28 (2026-W31) — 1 classified / 1 NIV2 removed / 0 review
- **Single soft-face / dead-blow hammer** (GWHST16 16oz soft-face w/ steel handle) → `Hand Tools > Striking
  Tools` (`394025337077`, closure `[Hammers and Striking Tools, Hand Tools]`). Use the individual **Striking
  Tools** node for a single hammer; reserve the floating **"Hammers and Striking Tool Sets"** node for SETS only.
  Tree-diff +14 rebuild artifact.

## 2026-08-03 (2026-W32) — 1 classified / 1 NIV2 removed / 0 review
One untagged item. Tree diff +14 (vocabulary-build expansion); nothing created.
- **Diagnostic / TPMS / scan-tool sets** (GWSMARTMOD — scan tool + TPMS programmer + borescope + tablet +
  diagnostic cart) → `Specialty > Diagnostic Scan Tools` (`457774694645`, `[Specialty, scan-tools]`)
  **plus** `Tool Sets > Specialty Tool Sets` (`399336997109`, `[Specialty, Tool Sets]`). GearWrench runs
  parallel `Specialty`, `Tool Sets`, `Equipment`, `Sockets`, `Wrenches`, `Torque` structures — a multi-piece
  specialty set belongs in both its type node and the Tool Sets tree.
- **Non-dual store, so the `brand_gid` slot is free** to hold a second category node (the `brands` list is
  empty and `apply_run` resolves any gid). Used it for the Tool Sets pick. Same trick as RTS this week.
- **Do NOT use `MEGAMOD Master Sets` (`428026134773`) as a category** — it is a product-line collection
  (tag `megamod`), not a category, even though GWSMARTMOD looks like a MOD-family SKU.
- Store shape worth remembering: `Equipment` covers carts/jacks/shop supplies/storage; `Specialty` covers
  scan tools, testers, engine/body-brake-wheel, extraction. A diagnostic **cart sold as part of a set** does
  not pull the item into `Equipment > Storage`.
