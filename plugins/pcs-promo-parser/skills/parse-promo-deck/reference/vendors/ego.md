# EGO

## Brand keywords

- `ego power`, `ego power+`
- `ego ` (note trailing space — bare "EGO" can be too generic)
- `peak power`
- `arc lithium`
- `56v`, `peak power+` (softer)

## SKU pattern

Regex: `\b[A-Z]{2,4}\d{3,5}[A-Z0-9-]*\b`

Examples:
- `LB6504`, `LB7654` (blowers)
- `BAX1500` (chainsaws)
- `ST1623T` (string trimmers)
- `BA2800T`, `BA6720T` (batteries — note the leading `BA`)

The pattern is broad — be conservative and only emit SKUs that appear
in/near a price-bearing row.

## Promo code pattern

**None.** EGO does not use per-page promo identifiers. Use deal title.

## Price label priority

1. `Promo IMAP`
2. `PMAP`
3. `2025 PMAP`
4. `2026 PMAP`
5. `IMAP`
6. `MAP`
7. `MSRP`

The year-prefixed PMAP labels (`2025 PMAP`, `2026 PMAP`) are EGO's
convention for marking which model year the promo applies to. Treat
them as equivalent to plain `PMAP`. Prefer the year-prefixed form if
both appear (it's the active promo).

## Non-price labels (NEVER treat as price)

- `Description`
- `Discount` (dollar-off amount, not a price)
- `Promo Window`
- `Chervon Funding`, `Funding` (internal accounting)

## Header signatures

Most common header:
- `Model Description 2025 MSRP 2025 PMAP Discount $ off [Promo Window] [Funding]`

Signature tokens:
- `Model`
- `Description`
- `MSRP`
- `PMAP`
- `Discount`
- `Promo Window`
- `Funding`

## Quirks

- **EGO sheets are mostly discount-only**: many slides are pure
  price-drop / clearance pages with no free goods. These should
  classify as **NLP routing** (Step 7 in the decision tree), NOT as
  kit pages. The `nlp_sheet.csv` is the right destination for these.
- **Chervon Funding column** is internal accounting — never emit as a
  price.
- **Date label**: execution / advertising date range on slide;
  conventions vary. Use the customer-facing window.
- **No PCE / promo code** — use deal title as `promo_name`.
- The `ego ` keyword has a deliberate trailing space because bare "EGO"
  appears in narrative copy of other brands (e.g. "ergonomic design")
  and would trip vendor detection.
