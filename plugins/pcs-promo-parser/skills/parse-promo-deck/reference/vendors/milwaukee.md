# Milwaukee

## Brand keywords (vendor detection)

Case-insensitive substring match. Higher counts win.

- `milwaukee`
- `m12`
- `m18`
- `mx fuel`, `mx ` (MX Fuel battery platform)
- `redlithium`, `redstick`
- `fuel`, `powerstate`, `redlink`, `one-key` (platform features — softer signals)

## SKU pattern

Regex: `\b\d{2,4}-(?:\d{2,3}-)?\d{2,4}[A-Z]{0,3}\b`

Examples:
- `2962-22`, `2767-20` (4-digit-2-digit form, kits)
- `48-11-1850`, `48-11-2440` (3-segment form, batteries / accessories)
- `48-73-1300` (helmets / safety)
- `MXF002-2XC` (MX Fuel SKUs — letter prefix is also valid)

For **MX Fuel** specifically, also accept SKUs of the form `MXF\d{3,4}-\d[XAS]C?` or similar — the vendor uses a letter prefix for these.

## Promo code pattern (PCE)

Regex: `PCE[#:\s]*(\d{6})` (case-insensitive)

When a PCE code is on the page, append it in brackets to `promo_name`:

- `"Buy an Mx Fuel Kit Get One Free [PCE 252601]"`
- `"MX FUEL Carry-On Power Supply Special Buy [PCE 262776]"`

Use the **full prefix-with-number** form (`PCE 262776`), not the bare digits.

## Price label priority

Walk in order; first column whose header matches AND has a numeric
value wins:

1. `Promo IMAP`
2. `IMAP`

Both labels mean "customer-facing online price." `Promo IMAP` is the
promotional override; `IMAP` is the regular online minimum.

## Non-price labels (NEVER treat as price)

- `Heavy Duty Price`
- `Heavy Duty`
- `Description`

`Heavy Duty Price` is a category-tier reference number, not the
customer price. Always prefer `Promo IMAP` over `Heavy Duty Price`
even if both columns have values.

## Header signatures (table-header detection)

A line is the price-table header if it contains **≥1** price-bearing
label AND **≥2 total** of these tokens:

- `ITEM #`
- `DESCRIPTION`
- `IMAP`
- `PROMO IMAP`
- `QUALIFYING ITEMS` (banner, not header — see traps below)
- `FREE GOOD` (banner, not header)
- `HEAVY DUTY`

## Quirks and accumulated rules

- **`QUALIFYING ITEMS` / `FREE GOOD` are SECTION BANNERS, not headers**.
  Always look past them for the real price-table header line with
  `Item # / Description / IMAP / Promo IMAP`.
- **Multi-line headers**: Milwaukee splits column titles across 2 lines
  often, e.g.:
  ```
  PRICE     DUTY      PRICE     IMAP
  ITEM #    DESCRIPTION   HEAVY DUTY  PROMO IMAP
  ```
  Merge consecutive header lines before column extraction.
- **MX Fuel pages**: same price label priority (`Promo IMAP → IMAP`).
  These pages often have multiple qualifying SKUs at a single price
  point shown as a row of product image panels — see
  `edge-cases.md#multi-image-sku-panels-milwaukee-mx-fuel`.
- **Single-member B1G1**: Milwaukee promos with "Get X Free" titles
  may have the free SKU panel hidden as an image-only sidebar. If you
  extract only ONE paid SKU and the title says B1G1, scan the page
  image carefully for the free SKU — see
  `edge-cases.md#b1g1--single-member-with-hidden-free-good`.
- **Heavy Duty Price strikethrough**: Heavy Duty Price is often shown
  struck-out as a "was/now" comparison next to Promo IMAP. The strike
  is decorative — it's not a killed SKU. Continue to pick `Promo IMAP`.
- **Date label**: Use `Online Execution`. Common date layout:
  ```
  Online Execution: 5/4/2026 - 8/2/2026
  Buy-In: 4/1/2026 - 5/3/2026
  ```
  Never use the Buy-In window.
- **PCE 6-digit only**: the pattern `PCE[#:\s]*(\d{6})` requires
  exactly 6 digits. If you see `PCE 12345` (5 digits) or `PCE 1234567`
  (7 digits) it's not a Milwaukee PCE — likely a typo or a different
  vendor's code. Don't append it.
