# Write scope — HARD guardrail

This routine has exactly **one** kind of side effect on a store: **product tags**. Nothing else. This is the
single most important rule in the plugin.

## The ONLY Shopify writes allowed
- `mcp__shopify__shopify_bulk_apply_tags`  (primary — used for the batch files)
- `mcp__shopify__shopify_add_product_tag`  (single-product fallback only)
- `mcp__shopify__shopify_remove_product_tag`  (single-product fallback only)

Use the bulk tool with the `apply_run.py` batch files. The single-tag tools are only for a one-off fixup.

## NEVER call these (non-exhaustive)
Anything that mutates collections, metafields, menus, products beyond tags, themes, or files:
`shopify_create_collection`, `shopify_update_collection`, `shopify_delete_collection`,
`shopify_publish_collections`, `shopify_unpublish_collections`, `shopify_add_products_to_collection`,
`shopify_bulk_add_to_collections`, `shopify_bulk_create_collections`, `shopify_bulk_set_metafields`,
`shopify_add_menu_item`, `shopify_remove_menu_item`, `shopify_upload_file`, and any non-`shopify_*`
store-mutating tool. The bundled Python engine is read-only and must stay that way.

## Consequences of the scope
- **New categories** discovered during the tree refresh (step 1b) → recorded in `tree-diff.md` and reflected
  in the local tree only. **Never create or edit a collection** to add a category. A human curates collections.
- **A product whose correct category has no collection/tag** in the tree → it goes to the **review queue**,
  not a fabricated tag.
- The category tree itself is **read** from the store and **stored locally**; the store's collections/menus
  are never modified by this routine.

## MCP failure protocol
If a `shopify_*` tag tool errors, times out, or returns unexpected results: **stop, surface the exact error,
and ask how to proceed.** Do not substitute raw API calls, the Shopify CLI, GraphQL mutations, the Admin UI,
or any other path. The audit trail and rollback guarantees only hold when these designated tools are used.
The same applies to the Drive MCP (see `confidence-and-drive.md` — there, keep the local backup and continue).
