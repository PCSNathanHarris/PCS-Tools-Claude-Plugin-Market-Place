# Universal categorization rules (all stores)

These apply on **every** store. Store-specific exceptions live in `store-quirks.md` (read both).

## 1. Read the tags the product already has — first
Most `New Item V2` items are already partially/fully categorized. Read `current_category_tags`,
`current_brand_tags`, and `all_tags`, find the node(s) whose closure matches, **verify against the product**,
and finalize. Correct an anchor only when the product clearly contradicts it (e.g. a box titled "Lo-Side" with
a stale "Saddle Boxes" tag → trust the title).

## 2. Use every data point
When anchors are thin, weigh `title`, `vendor`, `type`, `description`, `facets_product_type`, and **every**
`metafields` entry (structured *and* unstructured). `facets_product_type` and the description are usually most
decisive.

## 3. Verify the FULL ancestor closure of the node you pick  ⚠ critical
A node's `tags_to_apply` is **leaf + every ancestor**. A collection can be **nav-nested under the wrong
department**, so a sensible-sounding leaf may drag a wrong top-level tag:
- "Specialty Tools" (`80695591012` on MTS) closure = `[Power Tools, Specialty Tools]` → picking it for a
  **manual** tool wrongly tags it **Power Tools**.
- "Apparel" (`80668098660` on MTS) closure = `[Apparel, Cordless Tools]` → picking it for a plain shirt wrongly
  tags it **Cordless Tools**.

**Rule:** before choosing a node, read its whole closure and confirm **every** tag fits the product. Never apply
a department tag (Power Tools, Cordless Tools, Hand Tools, Plumbing Tools, …) the product doesn't belong to. If
the only fitting leaf carries a wrong department in its closure, pick a cleaner node (often a higher-level
general category like `Hand Tools` / `Fasteners`) or go **brand-only**.

## 4. Powered apparel vs. plain apparel
Apparel collections nested under Cordless/Power Tools exist for **powered apparel** — **heated gear (battery)**
and **cooling gear (fan/battery)**. Those legitimately get the Cordless Tools ancestor.
- Product has a **battery or fan** (heated jacket/hoodie, fan-cooled vest) → the powered-apparel node is correct.
- **Plain/non-powered** apparel (shirts, evaporative cooling rags, hats) → do **not** use that node (it would
  add Cordless Tools); use **brand-only** (e.g. Milwaukee Shirts) or a non-powered apparel/PPE home.
- Always check for battery/fan in the product before using a powered-apparel section.

## 5. Storage vs. tool (organizer rule)
An organizer/case/rail/bag that **includes tools** (sockets, wrenches, ratchets, bits) → the **tool** category.
An organizer with **no tools included** → the **storage** category (Jobsite Storage, Tool Belts & Bags, etc.).

## 6. Datacom / VDV
Voice-data-video tools (punchdown tools, VDV crimper frames, coax connectors) stay in the **Telecom** /
wire-termination categories — **not** the main electrical Crimping Tools / Cable Termination categories.

## 7. No product gets zero tags — fallback ladder
There is always a home. Walk this ladder, stop at the first that fits:
1. **Specific category** (+ brand node on dual-tree stores).
2. **General high-level category** — `category_roots` in candidates.json, or a catch-all like **Fasteners**,
   **Accessories**, **Replacement Parts**, **Specialty Tools** (mind rule 3 — check its closure).
3. **Trade collection** (if the store has one that fits).
4. **Top-level brand collection** — each candidate's `fallback_brand_gid`; the engine applies this as a
   last-resort safety net, but place it yourself when you can.

Consumables/parts/blades with no specific home → **Replacement Parts** / **Accessories** (category) and/or the
matching brand accessories node. `review: true` is **only** for genuine ambiguity a human must resolve — never
for "no home found."

## 8. Dual-tree stores (Shop by Category + Shop by Brand)
When `dual_tree: true`, return a `category_gid` **and** a `brand_gid`; the product gets both closures.
Pick the brand node by vendor + battery platform/line + product type. On non-dual stores, brand = vendor and is
stripped (single `category_gid`). See `store-quirks.md` for which stores are dual-tree.

## 8b. Battery-platform tree (a THIRD, non-exclusive pick)
Many brands run a Shop-by-Battery-Platform tree (Milwaukee M12 / M18 / MX FUEL; DeWalt 12V MAX / 20V MAX /
FLEXVOLT; Makita LXT / XGT / CXT; …). A product on a platform gets that platform's collection tags **in
addition to** its category and brand tags — category + brand + platform can **all** apply (non-exclusive).
- candidates.json gives `platforms` (platform-tagged nodes), each candidate's detected `battery_platform` +
  `platform_tags`, and `platform_roots` (the clean `[brand, platform]` root per platform). Return `platform_gid`.
- **Pick a platform node whose TYPE matches the product's category** (e.g. an M18 plumbing tool → "Milwaukee
  M18 Plumbing Tools"). If no typed platform node matches, use the clean **platform root** (adds only e.g.
  `[Milwaukee, M18]` — never a wrong type). Apply rule 3 here too: never let the platform pick add a wrong
  type (a trimmer must not get "Rotary Hammers" just to get FLEXVOLT — use the FLEXVOLT Outdoor/root instead).
- A brand pick that is itself platform-specific (e.g. "Milwaukee M18 Plumbing Tools") already carries the
  platform tag — a separate `platform_gid` is then redundant but harmless (closures are unioned/deduped).
- **Err toward over-categorizing**: if a product is clearly on a platform, give it the platform pick. Only
  skip when the brand has no platform tree (e.g. Ridgid 18V) or the product isn't actually on a platform
  (a bare accessory bundled with a platform tool is not itself "on" the platform).

## 9. Never apply promo/operational tags
Sale/eligibility collections (Buy More Save More, NN% off, `shopmil##`, `*-bmsm-*`, Promotions, below-map) and
workflow tags (New Item V2, CL-categorized, VA Categorization Review, Categorized) are **never** category
targets. The engine strips them, but never choose one as a pick.

## 10. Categorization is add-only — the only tag ever removed is `New Item V2`
On every store, never change, rewrite, normalize, or delete a tag a product already carries. The pipeline
only **adds** category/brand/platform tags (+ `CL-categorized`); the single sanctioned removal is `New Item V2`
once the item is fully categorized. The engine's write surface (`add_batch_*` / `add_cl_categorized` /
`remove_niv2`) enforces this — keep it that way.
