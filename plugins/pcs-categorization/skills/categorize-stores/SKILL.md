---
name: categorize-stores
description: Autonomous weekly product categorization across the Toolup stores. Refreshes each store's category tree from live collections (detecting newly-added categories), classifies New Item V2 non-kit products to their bottom-most category and applies that tag plus all ancestor category tags, removes New Item V2 when complete, adds CL-categorized. Product-tag writes are the ONLY writes; low-confidence items go to a Google Drive review queue with a local backup; a per-store lessons file grows over time. Use weekly (scheduled) or on demand.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Categorize Stores — weekly autonomous run

Run the full categorization pipeline **store by store**, with **no user input**. For each store you
refresh its category tree, classify every eligible `New Item V2` product, **write only product tags**,
route anything you can't confidently place to a Google Drive review queue, and grow that store's
lessons file. The Python **engine** does all the deterministic reads + write-prep; **you** (Claude) do
the classification judgment; the **`shopify_*` MCP** does the tag writes.

This skill is fully autonomous. Try hard to place every item yourself — only genuinely-uncertain items
go to review. Never ask the user mid-run.

## Step 0 — Setup (once per run)

1. **Engine location**: the `engine/` folder of this plugin (sibling of `skills/`). Resolve its absolute
   path from this SKILL's location (installed under `.../plugins/cache/pcs-tools/pcs-categorization/<version>/engine`).
   Run all engine scripts with `python` **from inside that `engine/` dir**.
2. **Data dir**: `python -c "import config; print(config.data_dir())"` — the persistent store of
   `maps/`, `lessons-learned/`, `runs/`. (Defaults to the Automated Categorization project; override with
   `PCS_CATEGORIZATION_DATA`.) Credentials come from `toolup-themes/mcp/.env` via `config.py`.
3. **MCP check**: confirm the Shopify MCP (`mcp__shopify__*`) is available. Check the Google Drive MCP too;
   if it's unavailable this run, continue — review files are always written locally as backup (see Step 1f).
4. **Store order**: `reference/store-order.md` — **RTS → ATO → then the rest; exclude TUP**. Klein is
   built nav-less (the engine handles it automatically).

## Step 1 — For each store, in order

### 1a — Read the store's lessons
Read `<data_dir>/lessons-learned/<store-key>.md` (create an empty one if missing). Apply its learned
heuristics (keyword→category mappings, store quirks, prior decisions) throughout this store's run.

### 1b — Refresh tree + detect new categories  *(read-only to Shopify)*
Run: `python weekly_run.py --store <store-key>`
It rebuilds the tree from all sources, **diffs vs the previous tree**, and gathers eligible products.
Read `<data_dir>/runs/<week>/<slug>/tree-diff.md`. If new categories appeared, note them in the run
summary — **the local tree is already updated; never create or edit collections** (`reference/write-scope.md`).

### 1c — Classify  *(your judgment)*
Read `<data_dir>/runs/<week>/<slug>/candidates.json` and (for structure) `<data_dir>/maps/<slug>/<slug>-category-tree.md`.
**Read `reference/tagging-rules.md` in full — it carries the placement rules.** In short:
- **First, read the tags the product already has** (`current_category_tags`, `current_brand_tags`, `all_tags`).
  Most `New Item V2` items are already partially/fully categorized — confirm/complete those tags rather than
  classifying from scratch. Verify against the product info; correct an anchor only if the product contradicts it.
- When anchors are thin, weigh **every** data point: `title`, `vendor`, `type`, `description`,
  `facets_product_type`, and **every** `metafields` entry (structured *and* unstructured) + store lessons.
- The candidates file has a **`categories`** list (Shop-by-Category) and, on **dual-tree stores**
  (`dual_tree: true`, e.g. MTS), a separate **`brands`** list (Shop-by-Brand). Each entry has a `gid`, readable
  `path`, `parents`, and exact `tags_to_apply`. Pick the deepest fitting **category** node, and on dual-tree
  stores **also** the matching **brand** node — the product gets BOTH closures. `path` disambiguates reused leaf
  names (M12 vs M18, brand A vs B).

Write `<data_dir>/runs/<week>/<slug>/decisions.json`:
```json
{"decisions": [
  {"product_id": "123", "title": "...", "category_gid": "gid://shopify/Collection/456", "brand_gid": "gid://shopify/Collection/789", "category_tag": "Impact Wrenches", "confidence": "high"},
  {"product_id": "124", "title": "...", "category_gid": "gid://shopify/Collection/456", "category_tag": "Pliers", "confidence": "high"},
  {"product_id": "789", "title": "...", "review": true, "reason": "no clear category"}
]}
```
`category_gid` is the Shop-by-Category node; `brand_gid` is the Shop-by-Brand node (dual-tree stores only — omit
otherwise). At least one is required for a confident decision; the engine unions their closures. `category_tag`
is just a readable label. A bare `category_tag` with no gid is accepted only when it maps to exactly one node.
The vocabulary now includes **every non-promo collection** (nav + floating) — review is a true last resort
(`reference/tagging-rules.md` has the Accessories/Replacement-Parts fallbacks).

### 1d — Resolve to tag batches  *(no Shopify writes)*
Run: `python apply_run.py --store <store-key> --week <week> --decisions <abs path to decisions.json>`
It expands each chosen node to its closure (leaf + ancestors) and **unions** the `category_gid` and
`brand_gid` closures per product, then writes the batch files + `review-queue.json` + `apply-summary.json`.

### 1e — Write tags  *(the ONLY Shopify writes)*
Read `apply-summary.json`. For each file, call `mcp__shopify__shopify_bulk_apply_tags` (args under
`params`: `store`, `operation`, `assignments_file` = the **absolute** path):
- every `add_batch_*.json` → `operation: "add"`
- `remove_niv2.json` → `operation: "remove"`  (removes `New Item V2` from completed products)
- `add_cl_categorized.json` → `operation: "add"`  (the Claude-categorized marker)
Record each returned `rollback_file`. **Never** call any other write tool (`reference/write-scope.md`).

### 1f — Review queue → Drive (Google Doc) + local backup
`review-queue.json` in the run dir is the local backup. Upload a copy to the Drive review folder as a
**Google Doc** (not markdown) via `mcp__310c6af1-2764-468c-99d5-8035b95250e6__create_file`: `parentId`
= `1xteTZd7A1GRIHOq5dABz4BECgOk6LHuW`, `contentMimeType: "text/plain"`, and **omit**
`disableConversionToGoogleType` so Drive converts it to a Doc. `title` = **`<store-key>-<YYYY-MM-DD>-review`**
(store + run date, e.g. `weather-guard-store-2026-06-26-review`). Put the review list in `textContent` as
clean readable text (product · id · reason — no markdown tables). If the Drive MCP fails, keep the local
backup and note it in the summary (`reference/confidence-and-drive.md`).

### 1g — Append lessons
Append to `<data_dir>/lessons-learned/<store-key>.md` what this run taught: the date/week, counts
(classified / removed NIV2 / review), and **new heuristics** (keyword→category mappings you used, store
quirks, ambiguous calls + how you resolved them). Per `reference/lessons-protocol.md`. This file grows
every run and is read first next time.

### 1h — Per-store run summary
Write `<data_dir>/runs/<week>/<slug>/RUN-SUMMARY.md`: tree-diff highlights, # classified + tags written,
# `New Item V2` removed, # to review (+ Drive link/status), rollback files, notable decisions.

## Step 2 — Finish
After all stores: write `<data_dir>/runs/<week>/CROSS-STORE-SUMMARY.md` (per-store totals + review
counts + any failures). Print a short final report.

## Key rules
- **Write scope = product tags only.** The only Shopify writes are `shopify_add_product_tag`,
  `shopify_remove_product_tag`, `shopify_bulk_apply_tags`. Never create/edit collections, metafields,
  menus, themes, or files on a store. (`reference/write-scope.md`)
- **Existing tags first.** Most `New Item V2` items are already partially/fully categorized — read
  `current_category_tags` / `current_brand_tags` / `all_tags`, confirm against the product, finalize.
- **Bottom-most + ancestors, per tree.** Pick the deepest applicable **node** by `gid`; the engine applies that
  node's own closure (never a cross-node union of same-named nodes). On **dual-tree stores** (`dual_tree:true`,
  e.g. MTS) pick a Shop-by-Category node **and** a Shop-by-Brand node — the product gets both, and brand tags ARE
  applied. On other stores brand = vendor and is stripped (one category pick).
- **New categories** found in 1b → update the local tree + report only; never create collections.
- **Vocabulary = every non-promo collection.** With the full nav+floating category tree and (dual-tree) brand
  tree, plus the general Accessories/Replacement-Parts fallbacks in `reference/tagging-rules.md`, review is a
  true last resort. Never invent a tag.
- **Autonomous.** Place confidently on your own; only genuinely-uncertain items go to review. Don't ask
  the user. A store with 0 eligible items is a valid no-op — record it and move on.
- **Per-store lessons** are read at 1a and appended at 1g — they are how runs improve over time.
