# Tagging rules

## The goal
For each eligible product, find the **bottom-most (deepest) category** it belongs to, then tag it with that
leaf **plus every ancestor category tag** up the tree. Brand is the product's **Vendor**, never a category tag.

## Eligible products (the engine already filters these)
- Tagged `New Item V2`, **and**
- `custom.is_kit_item` ≠ `true` (kits are excluded), **and**
- not carrying a store-specific skip tag. Current skip rule: **`knaack-store` (JTB)** skips any product tagged
  **`remove`** — those are jobsite storage boxes that ship *with tools*, so they are not jobsite-storage items
  and must not be categorized. `candidates.json` only ever contains eligible products.

## Choosing the category (your judgment, step 1c)
- Read **all of the product-card info** together: `title`, `vendor`, `description`, **`facets_product_type`**
  (a strong placement signal when present), and **every `metafields` entry** (structured *and* unstructured).
  The description and `facets_product_type` are usually the most decisive — read them fully.
- Pick the **single deepest node** from the candidates file's `categories` list and return its **`gid`**. Each
  entry has a `gid`, a readable `path`, its `parents`, and the exact `tags_to_apply`. Use the `path` to choose
  the right one when a leaf name repeats — e.g. `… > M12 > Impact Wrenches` vs `… > M18 > Impact Wrenches`, or
  the same tool type under two different brands. The tree `.md` shows the big-picture structure.
- `current_category_tags` on a candidate are category tags it *already* carries (anchors) — a strong hint to
  the correct subtree, but verify against the product info; don't blindly trust them.
- **Pick a real node.** `category_gid` must be a `gid` from `categories`; never invent one. Set `category_tag`
  to that node's title for readable summaries. A bare `category_tag` with no gid is accepted only if it maps
  to exactly one node — if the name is shared (common for battery platforms / brand lines), the item is routed
  to review. So always supply the `gid`.
- **One node per product.** The engine applies **that node's own** closure (leaf + trusted ancestors, brand
  stripped) — never a union across same-named nodes, and you do **not** list ancestors yourself. If a product
  genuinely spans two unrelated nodes, pick the single best/primary one and note it in lessons; don't list two.
- If no node in the tree fits, mark the item `review: true` with a reason — **never** force a wrong tag.

## What gets written (step 1e, via `apply_run.py` batches)
For every **confident** decision:
1. **Add** the leaf tag + all ancestor category tags (brand/vendor names are stripped from the closure).
2. **Remove** `New Item V2` — only happens for confidently-categorized products (the chain is complete).
3. **Add** `CL-categorized` — the marker that Claude fully categorized this product.

Review-queue items get **none** of these writes; they keep `New Item V2` so they resurface next run.

## Tag-write mechanics (handled by the engine batches)
- One tag per product per call; ≤30 (product, tag) pairs per call — to stay within the bulk tool's limits and
  avoid the multi-tag clobber bug. `apply_run.py` produces the correctly-sized `add_batch_*.json` files.
- Every write returns a rollback file — record them in the run summary.
