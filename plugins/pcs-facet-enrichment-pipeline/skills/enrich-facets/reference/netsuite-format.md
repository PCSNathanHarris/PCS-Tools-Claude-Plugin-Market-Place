# Reference — NetSuite Facet Import Format

Trims the post-backfill export down to the exact import NetSuite expects.

## Output columns
`Input Product Name`, `Internal ID`, then `Facet 1 … Facet N`.
- `N` = the max number of facets on any **included** row after backfill. Trim trailing empty Facet columns so the header has exactly N facet columns.

## Per-row rule
1. Collect the row's non-empty `Facet` cells (each is `Label: value`).
2. **Product Type must be Facet 1.** Keep the remaining facets in their original Anglera order; compact out gaps (no blank cells between facets).
3. Pad shorter rows with trailing empties to N.

## Multi-value — only three attributes; collapse everything else
**Only `safety_rating`, `drive_size`, and `battery_compatibility`** may carry multiple comma-joined values in one cell (CSV-quoted, e.g. `"Drive Size: 1/4 in, 3/8 in"`). Every other facet is single-value.

**Enforce single-value here as a final pass.** Anglera's export sometimes leaves multiple comma-joined values in a descriptive field (e.g. `For Use On: Concrete, Masonry, Drywall`, `For Use With`, `For Joining`, `Material`), and those flow straight through unless collapsed. Run a short generated script over every included row (there can be hundreds of these cells) that, for each facet cell whose attribute is **not** one of the three allowed above, keeps only the **first** listed value:

- Split on the first comma that separates list items and keep the trimmed text before it: `For Use On: Concrete, Masonry, Drywall` → `For Use On: Concrete`.
- **Protect numeric thousands separators** — a comma flanked by a digit on *both* sides with no space (e.g. `10,000`) is part of a number, not a list. Leave the value whole: `Viscosity: 10,000 cps` stays `10,000 cps`; `Tensile Strength: 1,200 psi` stays whole. (Rule: only split at a comma whose neighbours aren't both digits.)
- Leave the three allowed multi-select attributes untouched.

## What to trim (drop entirely)
`Source URL *`, `Page Title`, `Detailed Description`, `Master Facet Category`, and the leftover raw `Safety Rating 1..10` and `Pack Quantity` columns — their facet versions already exist as `Facet` cells (those raw columns are unremoved Anglera source fields).

## Row scope
Include **only rows with ≥ 1 facet cell.** Drop rows that have nothing (not even Product Type).

## Formatting
- `Input Product Name` passes through unchanged (brand prefix + internal spacing preserved, e.g. `DeWalt  448696-00`).
- UTF-8 with BOM, CSV. **Filename: `Facet Backfill NS Import - <Vendor/Category>.csv`** (e.g. `Facet Backfill NS Import - Guardian.csv`).
- Facet labels are the attribute `Name` from `attributes (15).csv` (e.g. `sold_by` → "Sold As").

## Delivery to Google Drive
Upload **only this NS import file** to the shared Drive "NS import folder" (anyone-with-link)
via the Google Drive connector — do NOT change any sharing/permissions (the folder already
grants access):
- `create_file` with `parentId = 1IB4PzPFoUMWDQmYBzo6cV56tviXVXcgK`, `title = "Facet Backfill NS Import - <Vendor>"`, `contentMimeType = text/csv`, `disableConversionToGoogleType = true` (keep it a real CSV, not a Google Sheet).
- **This is the only file that goes to Drive.** The QA/comparison summary, `dropdown_additions_needed.csv`, gap report, backfill plan, and the PDP-filled xlsx/log all stay in the operator's **local** working folder — do not upload them.
- Report the returned Drive file link to the operator.

## Self-check before delivering
- Row 1 header = `Input Product Name, Internal ID, Facet 1 … Facet N` (no other columns).
- Every row's Facet 1 starts with `Product Type:` (unless that SKU genuinely has no PT — then it's whatever its first facet is).
- No blank cell appears before a non-blank facet in any row.
- No dropped/trimmed column leaked through.
- No facet cell **except** `safety_rating` / `drive_size` / `battery_compatibility` contains a list-comma (a comma with a non-digit on either side). Numeric values like `10,000` are fine.
