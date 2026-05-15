# Output Specification

---

## Output columns

The main data sheets use these 22 columns in this exact order.

| # | Column | Source |
|---|---|---|
| 1 | `Model #` | Raw display value from manufacturer primary SKU column |
| 2 | `Manufacturer SKU 2` | Raw value from backup SKU column 2 (blank if not selected) |
| 3 | `Manufacturer SKU 3` | Raw value from backup SKU column 3 (blank if not selected) |
| 4 | `MAP` | Parsed MAP price as a number; blank if null |
| 5 | `Minimum Advertised Promo Price` | Parsed promo MAP price as a number; blank if null |
| 6 | `Minimum Advertised Promo Price Effective Dates` | Raw string from promo dates column |
| 7 | `Description` | Raw string from description column |
| 8 | `UPC` | Cleaned UPC (scientific-notation numbers collapsed to integer string) |
| 9 | `formatted UPC` | Raw string from formatted UPC column |
| 10 | `Internal ID` | From matched ERP row; blank if unmatched |
| 11 | `Purchase Price` | Parsed number from ERP; blank if null or unmatched |
| 12 | `Keep Online Sales Price` | Raw string from ERP keep-sales-price column |
| 13 | `Current Online Sales Price` | Parsed number from ERP; blank if null |
| 14 | `Current ERP MAP Price` | Parsed number from ERP; blank if null |
| 15 | `Matched Manufacturer SKU` | The raw SKU value that produced the ERP hit |
| 16 | `Matched Manufacturer SKU Field` | Column name the matched SKU came from |
| 17 | `Lookup Source` | `"Vendor Name via <field>"`, `"MPN via <field>"`, or `"No match"` |
| 18 | `Verification Status` | `"Ready"`, `"Needs review"`, or `"Missing ERP match"` |
| 19 | `Verification Notes` | Human-readable explanation of all flags |
| 20 | `Is MAP Blank Or Zero` | `"Yes"` / `"No"` |
| 21 | `Is MAP Lower Than Purchase Price` | `"Yes"` / `"No"` |
| 22 | `Is Promo MAP Lower Than Purchase Price` | `"Yes"` / `"No"` |

**Number formatting:** Write numeric price values as Python `float` (not
strings). `openpyxl` will render them as numbers in Excel. Use `""` (empty
string) wherever a value is `None` — never write `"None"` or `"NaN"`.

**UPC cleaning:** If the raw UPC value contains `"E"` (scientific notation
from Excel), convert to `int` and back to string. Otherwise pass through as-is.

---

## Workbook sheets

Build the workbook with exactly four sheets in this order.

### Sheet 1 — `MAP Update Review`
All rows where `is_unmatched == False` (matched rows only).
These are the rows the user will import into NetSuite.

### Sheet 2 — `Exceptions`
All rows where `needs_review == True` (any flag set, including unmatched).
This is the focused review queue.

### Sheet 3 — `All Manufacturer Rows`
Every manufacturer row, matched or not. Full audit trail.

### Sheet 4 — `Summary`
Two-column table: `Metric` | `Value`

| Metric | Value |
|---|---|
| Manufacturer rows | count of manufacturer source rows with at least one usable SKU |
| ERP rows | count of ERP source rows |
| Manufacturer SKU fields | comma-joined list of selected field names |
| Manufacturer MAP field | name of the selected MAP column |
| ERP SKU match order | `"Vendor Name, then MPN"` |
| Rows exported to main sheet | count of rows on Sheet 1 |
| Matched rows | count where `is_unmatched == False` |
| Needs review | count where `needs_review == True` |
| Missing ERP match | count where `is_unmatched == True` |
| MAP blank or zero | count where `is_map_blank_or_zero == True` |
| MAP below purchase | count where `is_map_below_purchase == True` |
| Promo MAP below purchase | count where `is_promo_below_purchase == True` |
| Keep Sales Price review | count where `keep_price_review == True` |

---

## File naming

Save the output workbook in the **same directory as the manufacturer file**.

Pattern: `<ManufacturerBaseName>-MAP-Review-<YYYY-MM-DD>.xlsx`

Example: manufacturer file `DeWalt-MAP-Q2-2026.xlsx` run on 2026-05-14
produces `DeWalt-MAP-Q2-2026-MAP-Review-2026-05-14.xlsx`.

---

## Summary report (printed to stdout)

```
MAP Price Update — Complete
===========================
Manufacturer rows processed : <n>
ERP rows available          : <n>
Matched rows                : <n>  (<pct>% of manufacturer rows)
Needs review                : <n>
  Missing ERP match         : <n>
  MAP blank or zero         : <n>
  MAP below purchase price  : <n>
  Promo MAP below purchase  : <n>
  Keep Sales Price review   : <n>

Output file: <full path to xlsx>
```

Percentages rounded to one decimal place. If manufacturer rows is 0,
print `0.0%` rather than dividing by zero.
