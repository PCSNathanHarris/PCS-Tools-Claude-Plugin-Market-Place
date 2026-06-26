# Engine usage

The bundled `engine/` (Python) does all deterministic reads + write-prep. It **never writes to Shopify** —
it only reads (client-credentials token from `toolup-themes/mcp/.env`) and produces local JSON/markdown.
Run every script with `python` **from inside the `engine/` dir**.

## The two orchestrators the skill calls

### `weekly_run.py` — STEP 1 (read-only)
```
python weekly_run.py --store <key> [--max-items N]
```
- Rebuilds the store's tree (runs `build_category_map.py`, or `build_klein.py` for `the-klein-store`), then
  `refine_trees.py`.
- Diffs the refreshed tree vs the previously stored one → `runs/<week>/<slug>/tree-diff.md` (new categories).
- Gathers eligible `New Item V2` non-kit products (applies store skip tags) →
  `runs/<week>/<slug>/candidates.json` with vendor/title/description, `category_vocabulary`, `brand_names`,
  and each item's existing category anchors.
- `--max-items` caps the gather (for quick tests); omit for a full run.

### `apply_run.py` — STEP 3 (no Shopify writes)
```
python apply_run.py --store <key> --week <week> --decisions <abs path to decisions.json>
```
- Reads your `decisions.json`, expands each chosen leaf to its category-only (brand-stripped) closure.
- Writes `writes/add_batch_*.json` (≤30 pairs, one tag/product/call), `writes/remove_niv2.json`,
  `writes/add_cl_categorized.json`, `review-queue.json`, and `apply-summary.json`.
- The skill then feeds these batch files to `mcp__shopify__shopify_bulk_apply_tags` — that MCP call is the
  **only** thing that writes to Shopify.

## Support scripts (called by the orchestrators or for dev only)
`build_category_map.py` / `build_klein.py` (tree build from nav + `custom.subcollections_list` metafield +
`collection-list` templates + per-handle linklists + all collections + vendors), `klein_hierarchy.py`
(Klein's curated hierarchy), `refine_trees.py` (offline tree cleanup), `shopify_read_client.py` (read-only
GraphQL client), `config.py` (`data_dir()` + credentials). Others (`get_run_candidates.py`,
`resolve_decisions.py`, `discover_new_items.py`, `inspect_collection.py`, `probe_access.py`, `build_all.py`,
`selftest.py`) are utilities — not part of the weekly path.

## Data dir & credentials
- `python -c "import config; print(config.data_dir())"` prints the persistent data dir. Override with the
  `PCS_CATEGORIZATION_DATA` env var. It holds `maps/`, `lessons-learned/`, `runs/` — it lives **outside** the
  plugin so plugin auto-updates never clobber state.
- Credentials: `config.py` reads `toolup-themes/mcp/.env` (Shopify OAuth client-credentials). If the engine
  can't authenticate, stop and report — do not improvise another access path.
