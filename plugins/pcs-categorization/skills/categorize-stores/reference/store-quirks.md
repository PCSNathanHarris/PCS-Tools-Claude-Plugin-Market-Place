# Store-specific quirks

Read alongside `universal-rules.md`. These are per-store exceptions. The growing per-run detail lives in
`<data_dir>/lessons-learned/<store-key>.md` (read that too at run start).

## toolup-my-tool-store (MTS)
- **DUAL-TREE** — has both Shop-by-Category and Shop-by-Brand. Tag in BOTH: `category_gid` + `brand_gid`
  (brand tags are applied, not stripped). 266 vendors; 126 have a top-level brand-root for fallback.
- **BATTERY-PLATFORM tree (third pick)** — Milwaukee **M12 / M18 / MX FUEL**, DeWalt **12V MAX / 20V MAX /
  FLEXVOLT**, Makita **LXT / XGT / CXT**. Add `platform_gid` for any product on one of these (non-exclusive
  with category + brand). Platform nodes live across the brand tree (e.g. "Milwaukee M18 Plumbing Tools") and
  category tree (e.g. "LXT Drills"). Clean roots exist for M12/M18/MX FUEL/12V MAX/20V MAX/LXT/XGT/CXT;
  **FLEXVOLT has NO clean root** (all DeWalt FLEXVOLT collections are typed — use "DeWalt FLEXVOLT Outdoor
  Tools"/Drills/Saws etc. that fits, never a wrong type). **Ridgid 18V has no platform tree** — skip it.
- **"Apparel" node (`80668098660`) is for POWERED apparel only** — its closure is `[Apparel, Cordless Tools]`.
  Heated gear (battery) and cooling gear (fan/battery) belong here. Plain shirts / evaporative cooling /
  hats do NOT — use **brand-only** (e.g. Milwaukee Shirts `421963235581`). (Universal rule 4.)
- **"Specialty Tools" (`80695591012`) sits under Power Tools** — closure `[Power Tools, Specialty Tools]`.
  Do NOT use it for manual/hand tools (it would add Power Tools); odd hand tools → the **bare `Hand Tools` node
  (`80675569764`, closure `['Hand Tools']`)** or a fitting general category. (Universal rule 3.)
- **Generic fallback + branded sub-categories** (rule 7): a manual tool with no specific leaf → `Hand Tools`
  (`80675569764`) — better than a bare brand page. Real **`Drywall Tools`** category exists (`80676487268`,
  `[Drywall Tools, Hand Tools]`) for drywall hand tools. Brands have specific branded nodes — prefer them over
  the top-level brand page, e.g. **`Marshalltown Drywall Tools` (`80620159076`)** over plain "Marshalltown".
- **Fasteners** is a real category (`80674717796`, tag `Fasteners`) for rod hangers, anchors-as-fasteners, etc.
- **VDV / datacom** (Klein VDV line) is filed under Telecom Instruments — keep it there, not main Crimping.
- **Socket-storage** (rails, clips, organizers with no sockets included) → `Sockets and Adapters` (the store's
  convention) + the brand's Sockets & Ratchets/Power-Tool-Parts node.
- **FlexShaft chain knockers** are grouped with the inspection **Reels & Cameras** subtree (store convention),
  not generic Drain Cleaning.
- **WeatherGuard boxes**: trust the **title** for the box type (Lo-Side / Saddle / Cross …) — anchors are
  sometimes stale. Category = the generic Truck & Van box type; brand = Shop-by-Brand > Weather Guard.
- **Most NIV2 items are already tagged** — verify + finalize rather than classify from scratch.

## weather-guard-store (Spyder Supply)
- Rebranded to **Spyder Supply**, Spyder-only front-facing. **Skip the `weatherguard` vendor entirely**
  (`STORE_SKIP_VENDORS`) — legacy Weatherguard/truck-box items are not categorized or reviewed.

## knaack-store (JTB)
- Has branded **sections** but NOT a full Shop-by-Brand tree → **not** dual-tree. Brand-kind nodes are folded
  into the category vocabulary as ordinary targets. Skip products tagged `remove` (boxes that ship with tools).

## wood-shop-outlet (Pro Work Supply) / fasteners-store (Total Fastening)
- Single-OEM superstores (3M / Simpson). Brand = vendor, stripped (category-only). Backlogs were mostly
  categorized at launch — confirm anchors, finalize, remove NIV2 (largely no-ops).

## the-jet-store
- **ON HOLD** — duplicate-creation error inflates the NIV2 count. Don't drain until resolved.

## the-klein-store
- App lacks the navigation scope → structure is **Claude-inferred** (nav-less) from its collections, not from a
  live menu. Tag-defined collections only.
