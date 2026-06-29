# Write scope — HARD guardrail (the run is GATELESS)

This pipeline runs **unattended on a schedule with no approval gates** — everything is reviewed *after*.
That is only safe because the writes are tightly bounded. There are **exactly three** kinds of write, and
**nothing else**. Everything else the run does is **read-only** product/collection inspection.

## 1. Shopify — product TAG operations only
The only Shopify mutations allowed:
- `mcp__shopify__shopify_bulk_apply_tags` (primary — the `apply_run.py` batch files)
- `mcp__shopify__shopify_add_product_tag` / `shopify_remove_product_tag` (single-product fixup only)

What they do, and the **complete** set of tag changes:
- **ADD** category + brand + battery-platform closure tags, **ADD** `CL-categorized`.
- **REMOVE** `New Item V2` — the **single sanctioned removal** (add-only rule; universal rule 10).

**No other Shopify write — ever.** Never create/edit/delete/publish collections, set metafields, change
menus, edit themes, touch prices/inventory, or modify a product beyond its tags. NEVER call
`shopify_create_collection`, `shopify_update_collection`, `shopify_delete_collection`,
`shopify_publish_collections`, `shopify_add_products_to_collection`, `shopify_bulk_*` (collections/metafields),
`shopify_add_menu_item`, `shopify_upload_file`, raw API/GraphQL mutations, the Shopify CLI, or the Admin UI.

## 2. Git — lessons + change reports to the plugin repo only
`sync_repo.py` (step 2) commits and pushes **only** `plugins/pcs-categorization/lessons-learned/` and
`plugins/pcs-categorization/change-reports/`. **Never commits code** or any other path (scoped `git add`).
Fail-safe: if the repo is absent or any git step fails, it logs and continues — the run never breaks.

## 3. Google Drive — the project folder only
The report workbook (`build_report.py`) is written to the **Drive-for-Desktop synced project folder**
(`config.report_dir()` → `Claude Shopify Categorization Reviews`); the small review-queue Doc may go to the
same folder via the connector. **No other Drive/Google writes**, no other folders.

## Everything else is read-only
The tree refresh, candidate gather, and all product/collection lookups only READ. The bundled Python engine
holds a hard read-only guard (refuses any GraphQL `mutation`/`subscription`) and must stay that way.
- **New categories** found in the refresh → recorded in `tree-diff.md` + the local tree only. **Never create
  a collection.** A human curates collections.
- A product whose correct category has no collection/tag → **review queue**, never a fabricated tag.

## Failure handling (no human in the loop)
Because the run is gateless, a failed write is **logged and recorded in the run summary for after-the-fact
review — never routed around.** Do NOT substitute raw API/CLI/GraphQL/Admin-UI for a failed `shopify_*` tool.
On a tag-write failure, leave `New Item V2` on the un-tagged items (they resurface next run), note it, and
move on. A Drive/git failure → keep the local copy, note it, continue.
