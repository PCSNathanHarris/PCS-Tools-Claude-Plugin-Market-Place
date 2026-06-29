# Tagging rules

## The goal
Tag each eligible product into the deepest collection(s) it belongs to. On most stores that means one
**Shop-by-Category** placement (leaf + ancestors). On **dual-tree stores** (below) it means TWO placements —
one in the Shop-by-Category tree **and** one in the Shop-by-Brand tree — and the product gets the tags from
both.

## Step 0 — read the tags the product ALREADY has, first
Most `New Item V2` products are **already partially or fully categorized** (they kept `New Item V2` by
oversight). Before anything else, read `current_category_tags`, `current_brand_tags`, and `all_tags`:
- These existing anchors are the **strongest signal** to the right node(s). Find the category node (and, on
  dual-tree stores, the brand node) whose `tags_to_apply` matches the anchors, **verify it against the product
  info**, and finalize. If the item is already fully tagged, the chain is just confirm → remove `New Item V2`.
- Fill any gaps (anchors that imply a deeper leaf the product doesn't yet carry). Don't blindly trust an
  anchor that contradicts the product info — verify, then correct.

## Use EVERY data point on the product card
When the anchors are missing or ambiguous, weigh **every** field: `title`, `vendor`, `type`,
`description`, `facets_product_type`, and **every** `metafields` entry — structured *and* unstructured. No
single field decides it; read them together. `facets_product_type` and the description are usually most
decisive.

## Dual-tree stores: Shop by Category + Shop by Brand
Some stores run **two independent tagging trees** and a product gets tags from BOTH:
- **`candidates.json` tells you**: `dual_tree: true`, and provides a `categories` list (Shop-by-Category) and
  a separate `brands` list (Shop-by-Brand). **MTS (`toolup-my-tool-store`) is the dual-tree store.**
- For a dual-tree store, return **`category_gid`** (best node from `categories`) **and** **`brand_gid`** (best
  node from `brands`). The engine unions both nodes' closures. Pick the brand node by `vendor` + the product's
  battery platform / line (e.g. Milwaukee M18, DeWalt 20V MAX) + product type — `current_brand_tags` usually
  points right at it.
- Provide both when both apply. If only one tree has a fitting node, provide that one; never invent the other.
- **Non-dual stores** (everything else): `brands` is empty and brand-kind collections are folded into
  `categories`. Return a single `category_gid`. (knaack-store/JTB has branded *sections* but is not dual-tree.)

## The vocabulary is now the FULL collection set
`categories` includes **every non-promo collection** — the nav tree **and** off-nav "floating" collections
(Drill Bits, Drill Bit Sets, Replacement Parts, Replacement Blades, Accessories, Specialty Tools, …). If you
think "there's no collection for this," check again — there almost always is. Only promo/sale collections are
excluded as targets.

## Placement rules for the hard cases
- **Storage vs. tool (universal):** an organizer/case/rail/bag that **includes tools** (sockets, wrenches,
  ratchets, bits) → the **tool** category (e.g. Sockets, Tool Sets). An organizer **with no tools included** →
  the **storage** category (Jobsite Storage, Tool Belts & Bags, etc.).
- **Replacement blades / parts:** if there's no specific blade/part collection for that exact tool, use the
  general **Replacement Parts** or **Accessories** collection — don't send to review.
- **Accessories with no exact-match collection:** if no collection matches that precise accessory style, use a
  more general **Accessories** / **Replacement Parts** collection for the right subtree.
- **Datacom / VDV crimpers & connectors:** these are voice-data-video tools — keep them in the **Telecom**
  categories, **not** the main electrical Crimping Tools / Cable Termination categories.
- **Obscure / specialty tools:** use a **Specialty Tools** (or Specialty Cutting/Knives/Instruments) collection
  when one fits, then the general Accessories/Parts fallback.
- **Drill/cutting bits:** real categories — Drill Bits / Drill Bit Sets / Masonry & Tile Drill Bits (category
  tree) and branded bit collections (brand tree). Never route bits to review for "no category."
- **Review is the last resort.** With the full vocabulary plus the general Accessories/Replacement-Parts
  fallbacks, very few items are genuinely unplaceable. Only `review: true` when you truly cannot place it.

## decisions.json (what you write, step 1c)
```json
{"decisions": [
  {"product_id":"123","title":"…","category_gid":"gid://shopify/Collection/456","brand_gid":"gid://shopify/Collection/789","category_tag":"Impact Wrenches","confidence":"high"},
  {"product_id":"124","title":"…","category_gid":"gid://shopify/Collection/456","category_tag":"Pliers","confidence":"high"},
  {"product_id":"125","title":"…","review":true,"reason":"…"}
]}
```
- `category_gid` — a gid from `categories`. `brand_gid` — a gid from `brands` (dual-tree stores only; omit
  otherwise). At least one of the two is required for a confident decision. `category_tag` is just a readable
  label for summaries. A bare `category_tag` with no gid is accepted only when it maps to exactly one node.
- **Never invent a gid.** The engine routes any gid not in the store's collections to review.

## What gets written (step 1e, via `apply_run.py` batches)
For every confident decision:
1. **Add** the union of the chosen node(s)' closures — category-tree tags (brand stripped) **plus** brand-tree
   tags (brand kept) when a `brand_gid` was given.
2. **Remove** `New Item V2` (the chain is complete).
3. **Add** `CL-categorized`.

Review-queue items get none of these — they keep `New Item V2` and resurface next run.

## Tag-write mechanics (handled by the engine batches)
One tag per product per call; ≤30 (product, tag) pairs per call (bulk-tool limit + clobber-bug guard).
`apply_run.py` produces the correctly-sized `add_batch_*.json`. Every write returns a rollback file — record
them in the run summary.
