# Reference — NetSuite Facet Import Format

Trims the post-backfill export down to the exact import NetSuite expects.

## Output columns
`Input Product Name`, `Internal ID`, then `Facet 1 … Facet N`.
- `N` = the max number of facets on any **included** row after backfill. Trim trailing empty Facet columns so the header has exactly N facet columns.

## Per-row rule
1. Collect the row's non-empty `Facet` cells (each is `Label: value`).
2. **Product Type must be Facet 1.** Keep the remaining facets in their original Anglera order; compact out gaps (no blank cells between facets).
3. Pad shorter rows with trailing empties to N.

## Multi-value
Multi-select attributes (Type = MULTI_SELECT: `safety_rating`, `drive_size`, `battery_compatibility`) are comma-joined inside one cell and CSV-quoted, e.g. `"Drive Size: 1/4 in, 3/8 in"`. Single-select attributes are one value.

## What to trim (drop entirely)
`Source URL *`, `Page Title`, `Detailed Description`, `Master Facet Category`, and the leftover raw `Safety Rating 1..10` and `Pack Quantity` columns — their facet versions already exist as `Facet` cells (those raw columns are unremoved Anglera source fields).

## Row scope
Include **only rows with ≥ 1 facet cell.** Drop rows that have nothing (not even Product Type).

## Formatting
- `Input Product Name` passes through unchanged (brand prefix + internal spacing preserved, e.g. `DeWalt  448696-00`).
- UTF-8 with BOM, CSV. **Filename: `Facet Backfill NS Import - <Vendor/Category>.csv`** (e.g. `Facet Backfill NS Import - Guardian.csv`).
- Facet labels are the attribute `Name` from `attributes (15).csv` (e.g. `sold_by` → "Sold As").

## Delivery to Google Drive
Upload the finished file to the shared Drive folder (anyone-with-link) via the Google
Drive connector — do NOT change any sharing/permissions (the folder already grants access):
- `create_file` with `parentId = 1IB4PzPFoUMWDQmYBzo6cV56tviXVXcgK`, `title = "Facet Backfill NS Import - <Vendor>"`, `contentMimeType = text/csv`, `disableConversionToGoogleType = true` (keep it a real CSV, not a Google Sheet).
- Also upload the QA/comparison summary and `dropdown_additions_needed.csv` to the same folder with matching `Facet Backfill ... - <Vendor>` names.
- Report the returned Drive file link(s) to the operator.

## Self-check before delivering
- Row 1 header = `Input Product Name, Internal ID, Facet 1 … Facet N` (no other columns).
- Every row's Facet 1 starts with `Product Type:` (unless that SKU genuinely has no PT — then it's whatever its first facet is).
- No blank cell appears before a non-blank facet in any row.
- No dropped/trimmed column leaked through.
