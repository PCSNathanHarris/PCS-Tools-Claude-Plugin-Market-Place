# Flex

## Brand keywords

- `flex tools`
- `flex 24v`
- `flex stacked`, `flex stack pack`

Bare `flex` alone is too generic (appears in "flex shaft", "flex
cable", etc.) — require one of the multi-word phrases.

## SKU pattern

Regex: `\bFX\d{3,5}[A-Z0-9-]*\b`

Examples:
- `FX1271T-Z`, `FX2131A-Z` (cordless tools)
- `FX0211-1A` (configurations)
- `FX0331-K2` (kits)

## Promo code pattern

**None reliable.** Flex prints reference numbers in the deck footer
but these are NOT page-specific promo codes. Use deal title for
`promo_name`.

### CRITICAL — `PROMO CODE:` is a deal identifier, NOT a checkout code

Every Flex kit page carries a string like:

- `PROMO CODE: SOT2514219`
- `PROMO CODE: FLX1234567`

**This is the deal's tracking identifier**, equivalent to Milwaukee's
PCE. Treat it as a PCE-style identifier — extract the code portion and
append in brackets to `promo_name`:

- `"Flex 24V Stacked Drill Kit Promo [SOT2514219]"`

**Do NOT classify Flex pages as `promo-code-only` exclusions just because
they contain `PROMO CODE:`**. That's a false positive. The
`PROMO_CODE_MARKER` requires "use code", "enter code", "apply code at
checkout", or the explicit word "discount/coupon/checkout code" — see
`exclusion-markers.md#critical-trap--flex-deal-identifiers`.

## Price label priority

1. `T2 Promo Price`
2. `PMAPP`
3. `PMAP`
4. `Promo Price`
5. `IMAP`
6. `MAP`
7. `MSRP`

`T2 Promo Price` is the customer Tier 2 promo price (online dealer
price). `PMAPP` is the regular promo MAPP.

## Non-price labels (NEVER treat as price)

- `Description`
- `Buy QTY`
- `Case QTY`
- `Window`
- `T1 Promo Price` (Tier 1 = wholesale)

## Header signatures

- `Model Description T2 Promo Price MSRP PMAPP Buy QTY Window`

Signature tokens:
- `Model`
- `Description`
- `T2 Promo Price`
- `MSRP`
- `PMAPP`
- `Buy QTY`
- `Window`

## Quirks

- **T1 vs T2**: T1 is wholesale (NOT a customer price), T2 is the
  customer Tier 2 promo. Always prefer `T2 Promo Price` over T1.
- **`PROMO CODE:` is a deal identifier** — see the CRITICAL section
  above.
- **Date label**: execution date range shown on slide.
- **FX SKU prefix** is highly specific; if you see FX-prefix SKUs the
  vendor is almost certainly Flex.
