# GearWrench

## Brand keywords

- `gearwrench`
- `gear wrench`

## SKU pattern

Regex: `\b\d{4,6}D?\b`

Examples:
- `81230P`, `80551`, `80950T` (sockets / bits)
- `893302` (extended)

Note: bare 4–6 digit numbers can collide with other tokens (page
numbers, dollar amounts, year ranges). Be conservative — only emit
SKUs that appear in/near a price-bearing row AND match the GearWrench
catalog shape.

## Promo code pattern

**None.** GearWrench bundles use the **bundle name** as the promo
identifier:

- `"86 Pc. Mix Drive Socket Set Bundle"`
- `"100 Pc. Drive Tool Set Bundle"`

The bundle name IS the `promo_name`. No bracketed code.

## Price label priority

1. `Bundle Retail`
2. `Sugg. Retail`
3. `Sugg Retail`
4. `Suggested Retail`

`Bundle Retail` is the bundled-set price; that's the only customer-
facing column on most GearWrench pages.

## Non-price labels

- `Description`

## Header signatures

- `Item # Part No Description Bundle Retail`
- `Item # Description Sug Retail Bundle Retail`

Signature tokens:
- `Item #`
- `Part No.`, `Part No`, `Part #`
- `Description`
- `Bundle Retail`
- `Sug Retail`, `Sugg Retail`

## Quirks

- **Bundles are NOT B1G1**. All SKUs in a GearWrench bundle are sold
  together at ONE total price. Emit a single row with all SKUs in
  slots 1..N; only `Item Price 1` carries the Bundle Retail value;
  other slots' Price columns are blank.
- **NO Cartesian explosion** — see `conventions.md#cartesian-row-generation`.
- **Date label**: top of promo page.
- The bundle SKU count varies (3–8 SKUs typical). If a bundle has more
  than 6 SKUs, that's a problem — `PromoRow.slots` only has 6 slots.
  Surface the overflow in `non_included` reason `missing-price` with
  Detail "bundle has >6 SKUs, slots overflow".
