# Conventions

These conventions are baked into the PCS Kit Builder pipeline. Every
output file the skill writes must follow them — downstream stages will
break or silently emit wrong data otherwise.

---

## Dates

- **Format**: `M/D/YYYY` with NO leading zeros.
- ✅ `5/4/2026`, `12/1/2026`, `1/15/2026`
- ❌ `05/04/2026`, `2026-05-04`, `May 4, 2026`, `5/4/26`

If you see a date in any other format, normalize it before writing:
- `05/04/2026` → `5/4/2026`
- `5-4-2026` → `5/4/2026`
- `2026-05-04` → `5/4/2026`
- `May 4, 2026` → `5/4/2026`
- `5/4/26` → `5/4/2026` (2-digit years assume current century)

For written-month date ranges (Bosch convention: `August 1 - October 31,
2025`), if only the second month carries a year, use it for both.

The date label to extract depends on the vendor — see
`reference/vendors/<vendor>.md`. Never use **Buy-In** dates; those are
internal dealer windows. Use **Online Execution** / **Promo Execution**
/ **Advertised Sell Through** / **Advertising Window** instead.

---

## CSV encoding

- **Encoding**: `utf-8-sig` (UTF-8 with byte-order mark / BOM).
- **Line ending**: `\r\n` (CRLF) — Excel-friendly on Windows.
- **Delimiter**: `,` (comma).
- **Quoting**: standard CSV — quote any cell containing a comma,
  newline, or double-quote; escape internal double-quotes by doubling.

When using the Write tool, emit the BOM as the first 3 bytes
(`\xEF\xBB\xBF`) followed by the CSV content. If you're not certain
your output has the BOM, write it explicitly at the start of the file.

---

## Empty cells

- **Empty cells emit as empty string**, NOT as `0`, `null`, `None`, or `-`.
- A `PromoRow` with only slot 1 filled emits:
  ```
  Promo,1/1/2026,3/31/2026,DCS438B,1,179.00,,,,,,,,,,,,,,,,,,,,,
  ```
  (24 empty cells for slots 2–6, plus 1 empty `Item Credit 1` cell.)

---

## Price format

- **2-decimal fixed format**: `199.00`, `1.50`, `1395.00`, `0.00`.
- ❌ `199`, `199.0`, `$199.00`, `199.000000001`, `0`
- Use `Decimal` with `ROUND_HALF_UP` semantics if computing — avoids
  IEEE-754 float artifacts.
- Strip currency symbols, commas, and surrounding whitespace before
  parsing: `$ 1,395.00` → `1395.00`.
- Free goods emit `0.00` in the Price column.

---

## SkuSlot shape

Every "filled" item in a row carries four values, in this fixed order:

| Field  | Meaning | Default |
|--------|---------|---------|
| `sku`  | Vendor SKU as printed on the deck (pre-NetSuite lookup) | "" |
| `qty`  | Quantity required for the deal | 1 |
| `price`| Customer-facing price (0.00 for free goods) | 0.00 |
| `credit`| Almost always blank/empty in Stage 1 output | empty |

A `PromoRow` carries up to **6 slots**. Blank/unused slots emit 4 empty
cells. Most kit promos use 1–2 slots (1 paid + 1 free); multi-paid
bundles or multi-free B1G2 promos use more.

---

## Cartesian row generation

When a deal offers **N qualifying paid options × M free-good options**,
emit **N × M rows**, not max(N, M).

Example: a Milwaukee promo with 3 qualifying tool kits and 2 possible
free batteries:
- Paid: A, B, C
- Free: X, Y
- Emit 6 rows:
  ```
  Promo, ..., A, 1, 299.00, ..., X, 1, 0.00, ...
  Promo, ..., A, 1, 299.00, ..., Y, 1, 0.00, ...
  Promo, ..., B, 1, 349.00, ..., X, 1, 0.00, ...
  Promo, ..., B, 1, 349.00, ..., Y, 1, 0.00, ...
  Promo, ..., C, 1, 399.00, ..., X, 1, 0.00, ...
  Promo, ..., C, 1, 399.00, ..., Y, 1, 0.00, ...
  ```

All rows share the same `Promo Name`, `Start Date`, `End Date`.

For multi-paid bundles with NO free goods (e.g. GearWrench socket sets
sold as one bundled price), put all paid SKUs in slots of a SINGLE row
— the entire bundle is one promo, not a Cartesian explosion.

---

## Price label fallback rule

Each vendor reference file lists a **`price_label_priority`** — an
ordered set of price-column header tokens (e.g. for DeWalt: `PMAPP →
MAPP → Promo Price → IMAP → MAP`). When extracting a customer-facing
price for a paid SKU:

1. Walk the priority list **in order**.
2. The **first non-empty match wins**. Take the value from that column
   for the row.
3. A paid SKU may **NOT** be dropped if ANY tier in the priority chain
   has a value. Only drop to `non_included` reason `missing-price` when
   **every** tier is blank, `N/A`, or otherwise unextractable.

**Worked example — DeWalt SKU with PMAPP missing**:

```
SKU       PLATINUM   PMAPP      MAPP    Promo Price
DCS438B   159.00     (blank)    229.00  229.00
```

PMAPP is the highest-priority tier but it's blank. The fallback rule
requires checking MAPP next, which has `229.00`. Emit the row with
`Item Price = 229.00`. Do **not** drop the SKU to `non_included` — a
later tier had data.

**Vendor-specific override**: Makita routes the "all tiers empty" case
to `Needs-Pricing.csv` instead of `non_included` — see
`reference/vendors/makita.md#missing-price-routing`. All other vendors
follow the standard drop-to-`non_included` rule.

---

## "No paid SKU without a price" rule

If you can identify a paid SKU on a kit page but cannot extract a price
for it from ANY tier in `price_label_priority` (every column blank,
OCR failure across all tiers, etc.), **drop that SKU to
`non_included.csv` with reason `missing-price`** (or to Makita's
`Needs-Pricing.csv` per the override above).

Do NOT emit a `0.00` priced paid row — the only zero-priced rows in
`promo_list.csv` are explicit free goods (e.g. those tagged `FREE` in
the price column or appearing under a `FREE GOOD` panel).

This is a hard rule: wrong prices propagate downstream as wrong
NetSuite items and cost real money to correct.

---

## Brand-prefix map (informational)

Each vendor maps to a 4-character prefix used by NetSuite downstream.
The skill does NOT emit this prefix — Stages 3/4 handle it — but it
helps to recognize the vendor association:

| Vendor | Prefix |
|--------|--------|
| Milwaukee | `MILW` |
| DeWalt | `DEWA` |
| Makita | `MAKI` |
| Bosch | `BOSC` |
| GearWrench | `GEAR` |
| EGO | `EGO ` |
| Flex | `FLEX` |
| Crescent | `CRES` |

---

## Display Name brackets (informational, for downstream context)

Regular kits use **parens** around the date range in Display Name:
`(5/4-8/2)`.

RSA kits (Credit > 0) use **square brackets**: `[5/4-8/2]`.

This skill emits Stage 1 outputs only; Stage 3 builds Display Names.
But if a deck explicitly shows `[date-range]` it's a hint the promo
involves credit/RSA.
