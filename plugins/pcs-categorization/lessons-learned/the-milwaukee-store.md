# the-milwaukee-store (RTS) — lessons

## 2026-06-30 — parallel category structures must ALL be tagged (rule 8c)
RTS runs three parallel structures, each with its own tag namespace; a product belongs in every one that
applies:
1. **Power Tools** tree — `Power Tools > Cutting > Saws` → tag `Saws` (+ `Power Tool Cutting`, `Power Tools`).
2. **Shop By Trade** tree — typed leaves with `SBTW …` (Woodworking) / `SBTM …` (Metal) / `SBTA …`
   (Automotive) tags, e.g. `SBTW Circular Saws`. These hang under grouping pages like **"Milwaukee Saws"**
   and "Milwaukee Carpentry Tools".
3. **Battery Platform** tree — M18 / M12 / MX FUEL.

**What went wrong (dry-run W27):** an M18 FUEL circular saw was tagged `SBTW Circular Saws` + `M18` only —
the Power-Tools `Saws` closure was missed because the "Milwaukee Saws" → "Milwaukee Circular Saws" link is a
template `collection-list` edge, which the build had treated as untrusted.

**Fixes (2026-06-30):**
- Build now **trusts a template edge whose parent is an in-nav node** ("Milwaukee Saws" is the nav Power-Tools
  "Saws" node), so the leaf inherits `Power Tool Cutting, Power Tools, Saws`. The off-nav "Milwaukee Carpentry
  Tools" stays untrusted, so its `carpentry-tools` handle tag is correctly NOT applied.
- Result: "Milwaukee Circular Saws" closure = `Power Tool Cutting, Power Tools, Saws, SBTW Circular Saws`;
  picking that node + the `M18` platform root tags the saw `M18, Power Tool Cutting, Power Tools, Saws,
  SBTW Circular Saws`. 28 RTS leaves (saw types, batteries/chargers) gained their structure closures.
- Where a structure is a genuinely separate node, use `category_gids` (list) to pick one node per structure.

**Heuristic:** RTS tag prefixes — `SBTW`/`SBTM`/`SBTA` = Shop-By-Trade (Woodworking/Metal/Automotive),
`SBT Automotive` = trade root. Plain product-type tags (`Saws`, `Grinders`, `Drills`) = Power Tools tree.
M18/M12/MX FUEL = platform. Confirm the closure in `tags_to_apply` spans every applicable namespace.

## 2026-07-07 (2026-W28) — 5 classified / 5 NIV2 removed / 0 review
Small batch, all placed confidently. New heuristics/confirmations:
- **Rechargeable/USB-C personal task lights** (facet `Task Lights`, built-in battery, NOT on M12/M18/MX) →
  `Power Tools > System Enhancement > Lighting` (`189687686`, closure `Lighting, Power Tools, System Enhancement`).
  Reserve `Milwaukee Site Lights` / `Tower Lights` for large jobsite/tower units, not handheld task lights.
- **Torpedo/box levels** → dedicated floating `Milwaukee Levels` node (`271707832404`, tag `Levels`), even when
  `facets_product_type` mislabels them (this one read `Plumbing Tools Test and Measurement`). Trust the title.
- **M18 FORCE LOGIC utility/lineman crimpers** (utility/overhead cable crimping) → `Trades > Electrician Tools >
  Crimpers` (`267413094484`, closure `Electrician's Tools, M12, M18, Power Tools, SBTE Crimpers, trades`) — the
  powered electrician-trade home, not the manual `Hand Tools > Crimpers`.
- **M12/M18 FORCE LOGIC press tools** (plumbing/HVAC press, facet `Cordless Press Tools`) → `Trades > Plumbing
  Tools > Press Tools` (`267412635732`, closure `M12, Plumbing Tools, Power Tools, SBTP Press Tools, trades`).
  These trade nodes already carry the platform tag; a separate `platform_gid` is redundant-but-harmless.
- **Controller/cord extensions** (accessory extension cords, misleading facet `Extension Cords`) → `Milwaukee
  Extensions` (`60320514132`, tag `Extensions`); confirmed existing `Accessories/Tool Accessories/Extensions`.
- Tree diff flagged **154 "new" categories** — this is a vocabulary/tree rebuild artifact (full nav+floating
  set now surfaced), NOT 154 genuinely new collections. Logged; no collections created (read-only).

## 2026-07-13 (2026-W29) — 0 classified / 0 NIV2 removed / 0 review
Clean no-op: `weekly_run` reported eligible=0 (no `New Item V2` non-kit items outstanding). RTS backlog is
fully drained as of this run. Tree diff again flagged 153 "new" categories — same vocabulary-rebuild artifact
as W28 (154); no genuine new collections, none created (read-only). No decisions/report/tag-writes this run.

## 2026-07-20 (2026-W30) — 12 classified / 12 NIV2 removed / 0 review
12 fresh NIV2 items, all untagged from scratch (empty current_category_tags/current_brand_tags — classified
purely from title/facet/description). None on a battery platform. All placed confidently; nothing to review.
Tree diff flagged 153 "new" categories again — same vocabulary-rebuild artifact (W28=154, W29=153); no genuine
new collections, none created. New heuristics/confirmations this run:
- **Combination/T-squares** (facet `T-Squares`) → `Hand Tools > More Hand Tools > Layout Tools` (`189328070`,
  `[Hand Tools, Layout Tools]`). A combination square is a layout tool.
- **Pliers Wrench** (Milwaukee 48-22-6907, plier-style adjustable wrench) → `Hand Tools > Fastening > Wrenches`
  (`189329350`, clean `[Fastening, Hand Tools, Wrenches]`). **Avoid the `Milwaukee Pliers` node (`189328390`)** —
  its closure is contaminated `[Hand Tools, M12, Pliers, Power Tools, trades]` (nested under Lineman Tools), which
  would wrongly tag a manual tool M12/Power Tools/trades (universal rule 3). Route pliers-family manual gripping/
  turning tools to Wrenches when the Pliers node's closure doesn't fit.
- **Rechargeable flat flashlight w/ green laser** (facet `Jobsite Flashlights`, built-in battery, not on M12/M18)
  → `Power Tools > System Enhancement > Lighting` (`189687686`, `[Lighting, Power Tools, System Enhancement]`) —
  same convention as W28 handheld task lights. Reserve `Milwaukee Site Lights` (`271363473492`) for large units.
- **PACKOUT modular attachments** (magnetic bin attachment, belt-clip rack — facet `Modular Storage Systems`, no
  tools included) → `Accessories > Storage and Equipment > PACKOUT Shop Storage` (`263747305556`,
  `[Accessories, Storage and Equipment, packout-shop-storage]`). Storage-vs-tool rule: no tools included → storage.
- **SAWZALL recip blades** (facet `Reciprocating Saw Blades`) → `Accessories > Tool Accessories > Saw Blades`
  (`189288454`). **Mechanical-pencil replacement lead** (facet `Tool Replacement Parts`) → `Accessories > Other
  Accessories > Replacement Parts` (`189288262`).
- **Hex bit socket set** (facet `Bit Socket Sets`, includes tools) → `Hand Tools > Fastening > Sockets`
  (`73574154324`).
- **Gaps in RTS vocabulary** (placed at safe generics, confidence 48–58): no plain **Shirts** node — a women's
  long-sleeve hybrid tee (facet `T-Shirts`, non-powered) went to top-level `Apparel` (`190201798`, `[Apparel]`),
  NOT Base Layers (not truly a base layer). No **drinkware/hydration** node — PACKOUT insulated bottles (facet
  `Drinks/Hydration`) went to top-level `Accessories` (`89441042516`, `[Accessories]`). If a Shirts or Drinkware
  collection appears later, re-home these. Not review-worthy — a safe generic beats review here.

## 2026-07-28 (2026-W31) — 4 classified / 4 NIV2 removed / 0 review
4 fresh NIV2 items, all untagged from scratch except one socket (pre-tagged `Accessories`/`Sockets and
Adapters`). None on a battery platform. All placed confidently. Tree diff flagged 153 "new" categories again —
same vocabulary-rebuild artifact (W28=154, W29/W30=153); none created (read-only). New heuristics/confirmations:
- **Pliers Wrench Set** (48-22-6930, 2-pc) → `Hand Tools > Fastening > Wrenches` (`189329350`) — confirms the
  W30 48-22-6907 call; the whole pliers-wrench family routes to Wrenches, never the contaminated Pliers node.
- **FORCE LOGIC press RINGS/jaws** (ZoomLock MAX / B MaxiPro press ring, e.g. 49-16-2657ZX — an *accessory*
  compatible with M18/M12 press tools, not itself a tool and not on-platform) → `Accessories > Other
  Accessories > Plumbing Tool Accessories` (`293499207764`, `[Accessories, Plumbing Tool Accessories]`). Keep
  the press-ring accessory distinct from the press TOOL itself (W28: press tools → Trades > Plumbing > Press
  Tools). No `platform_gid` — a bare press-ring accessory is not "on" the platform (universal rule 8b).
- **Surface-grinding dust shroud** (49-40-6200, facet `Grinder Guards`, `for_use_with Angle Grinder`, connects
  to Milwaukee dust extractors for OSHA silica control) → `Accessories > Other Accessories > Dust Collection`
  (`189287878`, `[Accessories, Dust Collection]`). Trust the dust-extraction purpose over the "guard" label.
- **SHOCKWAVE impact socket** (single, facet `Impact Sockets`, `socket_type Impact`) → `Accessories > Tool
  Accessories > Impact Sockets` (`189288006`, `[Accessories, Impact Sockets, Tool Accessories]`) — the impact
  accessory node, not the hand-tool `Sockets` node (which is for socket sets under Fastening).

## 2026-08-03 (2026-W32) — 13 classified / 13 NIV2 removed / 0 review
13 fresh NIV2 items — a **reconditioned + OPE (outdoor power equipment) wave**. All classified from scratch
(only the SHOCKWAVE socket carried anchors). All placed confidently; nothing to review. Tree diff flagged 153
"new" categories again — the same vocabulary-rebuild artifact (W28=154, W29/W30/W31=153); none created (read-only).
New heuristics/confirmations:
- **`category_gids` (list) is NOT supported by the installed `apply_run.py`** — only `category_gid` / `brand_gid`
  / `platform_gid`. On a **non-dual-tree** store (RTS) the `brand_gid` slot resolves any node **by gid**, so it
  works as a **second category slot** for RTS's parallel structures (Power Tools / Shop-By-Trade / floating).
  Used it this run to add `Recip Blades`, `SBTA Impact Wrenches`, `quik-lok`, `packout accessories`.
- **⚠ `Power Tools > Drilling & Fastening > Impact Wrenches` (`189687558`) closure is CONTAMINATED** —
  `[Drilling and Driving, Impact Wrenches, M12, Power Tools, SBT Automotive, trades]`. It injects **M12** into
  every pick, so it is wrong for an **M18** tool (universal rule 3). Use the clean platform node
  **`M18 > Drilling & Fastening > Impact Wrenches` (`189693318`, `[Impact Wrenches, M18, M18 Drilling and Driving]`)**
  and add the trade structure via **`Milwaukee Impact Wrenches` (`267413323860`, `[SBTA Impact Wrenches]`)**.
- **QUIK-LOK attachments** (articulating hedge trimmer `49-16-2719R`, bristle brush `49-16-2741R`, pole-saw kit
  `3016-21PS`): tag the **attachment's own type** where a leaf exists (hedge trimmer →
  `Power Tools > Outdoor Tools > Hedge Trimmers` `271717957716`), else the generic
  `Power Tools > Outdoor Tools` (`263741472852`, `[Power Tools, ope]`), **plus** the floating
  **`Milwaukee QUIK-LOK Outdoor System` (`268855378004`, `[quik-lok]`)**, **plus** platform
  `M18 > Outdoor Tools` (`264203993172`, `[M18, ope]`). The bristle brush and pole saw have **no type leaf**
  (no Brush/Sweeper node, no Pole Saws node) — generic Outdoor Tools, conf 60-62.
- **Do NOT file a pole saw under `Chainsaws`** — RTS keeps chainsaws (`271709667412`) for chainsaws only; a
  pole saw is a distinct type with no leaf. Generic Outdoor Tools instead. A real **M18 16" chainsaw** (`2727-80`)
  does get `Chainsaws` + platform `M18 > Outdoor Tools > Chainsaws` (`272597450836`).
- **Chain saw CHAIN** (facet `Chain Saw Chains`, 49-16-2819) → `Accessories > Tool Accessories > Saw Blades`
  (`189288454`) — the chain is the saw's cutting element, same family as a blade. No Chain/Bar node exists.
  No `platform_gid` (a bare accessory is not "on" the platform, rule 8b).
- **OPE replacement blades that are not saw blades** (8" edger blade 50 PK, facet `Replacement Blades`) →
  `Accessories > Other Accessories > Replacement Parts` (`189288262`). Reserve `Saw Blades` for saw-family
  cutting media. **SAWZALL recip blade** → `Saw Blades` (`189288454`) **+ floating `Recip Blades`
  (`173509836884`, `[Recip Blades, Saw Blades_Recip Blades]`)** — add the typed recip node, W30/W31 only used
  the generic Saw Blades node.
- **PACKOUT drinkware accessories** (sip lid for insulated bottles, facet `Drinks/Hydration`) → top-level
  `Accessories` (`89441042516`) **+ floating `PACKOUT Accessories` (`271297151060`, `[packout accessories]`)`.
  Still no drinkware/hydration node (W30 gap persists) — the PACKOUT Accessories node is the better half of the
  pair; re-home if a Drinkware collection appears.
- **Manual wire strippers have NO node on RTS** (MT702, facet `Wire Strippers & Cutters`) → safe generic
  `Hand Tools > Cutting` (`271769501780`, `[Cutting Hand Tools, Hand Tools]`), conf 55. **Avoid
  `Trades > Electrician Tools > Cable Strippers` (`267413127252`)** — closure carries `M12, M18, Power Tools`
  and would wrongly power-tag a manual tool (rule 3). `Milwaukee Cable Cutters` (`292331651156`) is for hand
  **cable** cutters, not an 8-20 AWG wire stripper. **Vocabulary gap: no Wire Strippers leaf.**
- **Multi-function utility knife w/ prybar** (facet `Utility Knives`) → `Hand Tools > Cutting > Knives`
  (`189327878`) — the prybar/nail-puller extras don't move it out of Knives.
