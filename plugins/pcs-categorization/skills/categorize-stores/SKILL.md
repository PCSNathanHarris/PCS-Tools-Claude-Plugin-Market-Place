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
**Read `reference/universal-rules.md` (the cross-store placement rules) and `reference/store-quirks.md` (this
store's exceptions) in full; `reference/tagging-rules.md` has the decisions.json mechanics.** In short:
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
  {"product_id": "123", "title": "...", "category_gids": ["gid://shopify/Collection/456", "gid://shopify/Collection/457"], "brand_gid": "gid://shopify/Collection/789", "platform_gid": "gid://shopify/Collection/321", "category_tag": "Circular Saws", "confidence": 92},
  {"product_id": "124", "title": "...", "category_gid": "gid://shopify/Collection/456", "category_tag": "Pliers", "confidence": 80},
  {"product_id": "789", "title": "...", "review": true, "reason": "no clear category", "confidence": 15}
]}
```
`category_gids` = a **list** of Shop-by-Category nodes — one per **parallel category structure** the product
belongs to (Power Tools / Shop By Trade — universal rule 8c). The legacy single `category_gid` still works for
a one-structure pick. `brand_gid` = Shop-by-Brand node (dual-tree stores); `platform_gid` = battery-platform
node (when the product is on a platform — see universal rule 8b). All are non-exclusive and the engine unions
their closures. At least one is required for a confident decision. `category_tag` is just a readable label. A
bare `category_tag` with no gid is accepted only when it maps to exactly one node.
The vocabulary now includes **every non-promo collection** (nav + floating) — review is a true last resort
(`reference/tagging-rules.md` has the Accessories/Replacement-Parts fallbacks).

**`confidence` is a 0–100 integer** (it drives the report's red/yellow/green). Assign it on this scale:
anchor-confirmed deep leaf (the product already self-tags it) **90–100**; strong single structured signal
(facet / clear spec) **75–89**; inferred from title/description **50–74**; fallback placement (general bucket
or vendor brand-root) **25–49**; review **<25**. If omitted, `build_report.py` computes a signal-based proxy.

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

### 1f — Build the report workbook  *(no Shopify writes)*
**On a multi-store run (the weekly all-stores pipeline), SKIP per-store delivery here** — the single
combined **one-tab-per-store** workbook built in Step 2 is the sole delivered report (see Step 2 + Key
rules). Run the per-store `build_report.py --store …` below **only** for a single-store / on-demand run.

Run (single-store run only): `python build_report.py --store <store-key> --week <week>`
It writes the per-product **report `.xlsx`** — columns **Store · Shopify ID · Shopify Handle · Variant SKU ·
Title · Vendor · Category Tree Logic · Proposed Tags Applied · Confidence (0–100)**, with the Confidence cell
**color-filled** red (0–33) / yellow (34–66) / green (67–100) — into the **Google-Drive-for-Desktop synced
folder** (`config.report_dir()`, default `G:\My Drive\Claude Shopify Categorization Reviews`), where Drive
uploads it automatically; an audit copy also lands in the run dir. **Do NOT push the workbook through the MCP
Drive connector** — a binary `.xlsx` and a full multi-row sheet both exceed the connector's inline per-message
ceiling, and the connector cannot create tabs or cell colors (`reference/report-format.md`). If the synced
folder is missing (Drive for Desktop not running), the script keeps the audit copy and prints how to deliver
it — note that in the summary.

### 1g — Review queue → local backup (+ optional small Drive Doc)
`review-queue.json` in the run dir is the local backup. The review list is small text, so it MAY also go to
the Drive folder as a **Google Doc** via `mcp__310c6af1-2764-468c-99d5-8035b95250e6__create_file`: `parentId`
= `1xteTZd7A1GRIHOq5dABz4BECgOk6LHuW`, `contentMimeType: "text/plain"`, omit `disableConversionToGoogleType`,
`title` = **`<store-key>-<YYYY-MM-DD>-review`**, `textContent` = clean readable text (product · id · reason).
The connector is fine for this *small* Doc; it is **not** used for the report workbook (see 1f). If Drive
fails, keep the local backup and note it (`reference/confidence-and-drive.md`).

### 1h — Append lessons  *(formed AFTER scanning — the store's last step)*
Do this **at the end** of the store's work so issues surfaced during scanning/classification are captured.
Append to `<data_dir>/lessons-learned/<store-key>.md` what this run taught: the date/week, counts
(classified / removed NIV2 / review), and **new heuristics** (keyword→category mappings you used, store
quirks, ambiguous calls + how you resolved them). When a lesson is **cross-store** (generalizes beyond this
store), ALSO append it to **`<data_dir>/lessons-learned/PROJECT-LESSONS.md`**. Per `reference/lessons-protocol.md`
+ `reference/lessons-sync.md`. These files grow every run, are read first next time, and are pushed to the
plugin repo at step 2.

### 1i — Per-store run summary
Write `<data_dir>/runs/<week>/<slug>/RUN-SUMMARY.md`: tree-diff highlights, # classified + tags written,
# `New Item V2` removed, # to review, report-workbook path + delivery status, rollback files, notable decisions.

## Step 2 — Finish  *(gateless — no approval prompts; everything is reviewed after)*
After all stores:
1. **Combined weekly workbook (THE multi-store deliverable)** — `python build_report.py --week <week>`
   (no `--store`): `categorization-weekly-<YYYY-MM-DD>.xlsx`, **one tab per store**, into the Drive-synced
   report folder. When a run covers more than one store this is the **single** report delivered — per-store
   workbooks are not delivered separately (step 1f).
2. **Sync lessons to the repo** — `python sync_repo.py --week <week> --note "<one-line summary>"`: commits +
   pushes the updated `lessons-learned/` (store mds + `PROJECT-LESSONS.md`) and a dated `change-reports/`
   entry to the plugin repo. **Scoped to lessons + change-reports only, gateless, fail-safe** — see
   `reference/lessons-sync.md` and `reference/write-scope.md`.
3. Write `<data_dir>/runs/<week>/CROSS-STORE-SUMMARY.md` (per-store totals + review counts + any failures +
   the weekly workbook path + the lessons-sync push/skip status). Print a short final report.
4. **Always link the reports Drive folder at the end of the run.** Every run — single-store, multi-store, or
   all-no-op — must finish by giving the user the Google Drive folder where the report workbooks and review
   Docs live:
   **Claude Shopify Categorization Reviews** — https://drive.google.com/drive/folders/1xteTZd7A1GRIHOq5dABz4BECgOk6LHuW
   This is the online counterpart of the `config.report_dir()` Drive-for-Desktop synced folder and the same
   folder id used as `parentId` for review Docs. Include the link verbatim in **both** `CROSS-STORE-SUMMARY.md`
   and the printed final report.

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
- **Autonomous & gateless.** The whole pipeline runs unattended on a schedule with **no approval prompts
  anywhere** — place confidently, only genuinely-uncertain items go to review, never ask the user. A store
  with 0 eligible items is a valid no-op. Everything is reviewed *after*; that's safe only because the writes
  are the **three** in `reference/write-scope.md` (Shopify product tags · `lessons-learned/`+`change-reports/`
  git push · the Drive project folder) — nothing else, ever.
- **Lessons** — per-store `<store>.md` **and** cross-store `PROJECT-LESSONS.md` — are read at 1a, **formed at
  the end** (1h, after scanning), and **pushed to the plugin repo** at step 2 with a dated change report
  (`reference/lessons-sync.md`). The push is scoped to lessons/change-reports only and is fail-safe.
- **Report = colored `.xlsx` via the Drive-synced folder, never the connector.** Every run produces a report
  workbook (`build_report.py`) with a 0–100 color-coded Confidence column. A **single-store** run names the
  store in the filename (one tab); a **multi-store** run produces **exactly one** workbook with **one tab per
  store** (`categorization-weekly-<date>.xlsx`) — individual per-store files are NOT delivered. It is delivered by writing into the
  Google-Drive-for-Desktop folder (Drive must be running for the cron). The MCP Drive connector can't carry it
  (binary/size/no-tabs/no-colors) — only small text Docs (the review queue). See `reference/report-format.md`.
