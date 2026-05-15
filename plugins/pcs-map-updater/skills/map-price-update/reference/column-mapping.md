# Column Mapping & Matching Logic

---

## ERP column names

These are the exact column names (case-insensitive, whitespace-normalized)
the script looks for in the ERP export. Try each alias in the list and
take the first one found.

| Field | Aliases (in priority order) |
|---|---|
| Internal ID | `Internal ID`, `InternalID` |
| Vendor Name | `Vendor Name`, `VendorName` |
| MPN | `MPN`, `Model #`, `Model` |
| Purchase Price | `Purchase Price`, `PurchasePrice` |
| Keep Sales Price | `Keep Sales Price`, `Keep Online Sales Price`, `Keep SalesPrice` |
| Online Sales Price | `Online Sales Price`, `OnlineSalesPrice` |
| Current ERP MAP | `MAP Price`, `MAP`, `Current ERP MAP Price` |

---

## Manufacturer column candidates

Auto-suggested defaults when no column is pre-selected by the user.

**SKU field candidates** (pick first exact match, case-insensitive):
`Model #`, `Model#`, `Model`, `SKU`, `MPN`, `Item Number`, `Vendor Name`

**MAP field candidates** (pick first exact match, case-insensitive):
`Minimum Advertised Price`, `MAP`, `MAP Price`,
`Minimum Advertised Promo Price`

**Promo MAP candidates** (auto-detected, not user-selectable):
`Minimum Advertised Promo Price`, `Promo MAP`, `Promo Price`

**Promo Dates candidates** (auto-detected):
`Minimum Advertised Promo Price Effective Dates`,
`Promo Effective Dates`, `Promo Dates`

**Description candidates** (auto-detected):
`Description`, `Item Description`

**UPC candidates** (auto-detected):
`UPC`

**Formatted UPC candidates** (auto-detected):
`formatted UPC`, `Formatted UPC`

---

## SKU normalization

Apply this exact sequence to every SKU value before building lookup maps
or attempting a match. This prevents mismatches caused by Excel
formatting artifacts.

```python
def normalize_sku(value):
    if value is None:
        return ""
    s = str(value).strip()
    # Replace non-breaking spaces
    s = s.replace(' ', ' ')
    # Strip leading apostrophes Excel adds to force text formatting
    s = s.lstrip("'")
    s = s.strip()
    # If the value is a whole number stored as float (e.g. "12345.0"), strip the decimal
    import re
    if re.match(r'^[+-]?\d+\.0+$', s):
        s = re.sub(r'\.0+$', '', s)
    # Normalize to uppercase for case-insensitive comparison
    return s.upper()
```

Apply `normalize_sku` to every value before inserting into a lookup map
AND before looking a value up in that map. Never compare raw values.

---

## Money parsing

```python
def parse_money(value):
    if value is None:
        return None
    s = str(value).replace('$', '').replace(',', '').strip()
    if not s:
        return None
    try:
        result = float(s)
        import math
        return result if math.isfinite(result) else None
    except ValueError:
        return None
```

---

## ERP lookup maps

Build two dicts from the ERP rows **before** iterating manufacturer rows.
For duplicate keys, keep the first occurrence only.

```python
erp_by_vendor_name = {}   # normalized Vendor Name -> ERP row
erp_by_mpn = {}           # normalized MPN          -> ERP row

for row in erp_rows:
    vn = normalize_sku(row.get('vendor_name', ''))
    mpn = normalize_sku(row.get('mpn', ''))
    if vn and vn not in erp_by_vendor_name:
        erp_by_vendor_name[vn] = row
    if mpn and mpn not in erp_by_mpn:
        erp_by_mpn[mpn] = row
```

---

## Match cascade

For each manufacturer row, try every selected SKU column in slot order
(primary → backup 2 → backup 3). For each candidate:

1. **Vendor Name lookup** — `erp_by_vendor_name.get(normalize_sku(candidate))`
2. If no Vendor Name hit → **MPN lookup** — `erp_by_mpn.get(normalize_sku(candidate))`

Stop at the first hit. Record:
- `matched_manufacturer_sku` — the raw (un-normalized) candidate value that matched
- `matched_manufacturer_sku_field` — the column name the candidate came from
- `lookup_source` — `"Vendor Name via <field>"` or `"MPN via <field>"`

If no candidate in any slot produces a hit, set `lookup_source = "No match"`
and leave ERP fields blank.

---

## Validation flags

Compute these booleans for every output row after the match cascade.

| Flag | Condition |
|---|---|
| `is_map_blank_or_zero` | MAP price is `None` OR `== 0` |
| `is_map_below_purchase` | match found AND MAP > 0 AND purchase_price > 0 AND MAP < purchase_price |
| `is_promo_below_purchase` | match found AND promo_map > 0 AND purchase_price > 0 AND promo_map < purchase_price |
| `keep_price_review` | match found AND keep_sales_price is not empty AND not equal to "no" (case-insensitive) |
| `is_unmatched` | no ERP match found |
| `needs_review` | ANY of the above five flags is True |

**Verification Status** values:
- `"Missing ERP match"` — `is_unmatched` is True
- `"Needs review"` — `is_unmatched` is False AND `needs_review` is True
- `"Ready"` — all flags False

**Verification Notes** — join all applicable note strings with a space:
- `is_map_blank_or_zero` and value is 0 → `"MAP price is 0."`
- `is_map_blank_or_zero` and value is None → `"MAP price is blank."`
- `is_unmatched` → `"No ERP match found for this model."`
- `is_map_below_purchase` → `"MAP is below purchase price."`
- `is_promo_below_purchase` → `"Promo MAP is below purchase price."`
- `keep_price_review` → `"Keep Sales Price is <value>."`
- No flags → `"Ready to export."`
