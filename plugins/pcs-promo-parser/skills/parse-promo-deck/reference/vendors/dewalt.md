# DeWalt

## Brand keywords

- `dewalt`
- `atomic` (Atomic platform)
- `flexvolt`
- `20v max`, `60v max`
- `xr` (softer signal)

## SKU pattern

Regex: `\bD[CW][A-Z]{1,2}\d{3,4}[A-Z0-9-]*\b`

Examples:
- `DCF891B`, `DCS438B`, `DCD800B` (bare-tool SKUs)
- `DCB205-2C` (battery 2-packs)
- `DCK2050M2` (combo kits)
- `DWHT16071` (hand tools — DW prefix variant)

The pattern matches `DC` (cordless) or `DW` (corded / hand-tool)
prefixes with 1–2 alpha letters and 3–4 digits, optionally followed by
configuration suffixes.

## Promo code pattern (PCR / P-)

Regex: `\b(?:PCR\s*\d{6,9}|P-\d{6,9})\b` (case-insensitive)

DeWalt uses two equivalent forms — `PCR 123456` and `P-00209433`.
When a code is on the page, append in brackets:

- `"Buy 2 Get 1 Free Combo [PCR 123456]"`
- `"DCK2050M2 Bundle Promo [P-00209433]"`

## Price label priority

1. `PMAPP` (Platinum MAPP — most common)
2. `MAPP`
3. `Promo Price`
4. `IMAP`
5. `MAP`

`PMAPP` and `MAPP` are the customer-facing prices (Promo MAPP and
regular MAPP, respectively). `PLATINUM` is dealer cost — NEVER a
customer price.

**Fallback rule (v0.3.0 — explicit)**: walk the list above in order and
take the **first non-empty tier**. If `PMAPP` is missing, fall through
to `MAPP`. If `MAPP` is also missing, try `Promo Price`. Continue to
`IMAP`, then `MAP`. A paid SKU must **NOT** be dropped if any tier in
the chain has a value — drop to `non_included` reason `missing-price`
only when ALL five tiers are blank. See
`reference/conventions.md#price-label-fallback-rule` for the worked
example.

## Non-price labels (NEVER treat as price)

- `Platinum` (dealer cost)
- `Description`

## Header signatures

Common header rows:
- `SKU DESCRIPTION PLATINUM MAPP PROMO PRICE`
- `SKU DESCRIPTION PLATINUM MAPP PROMO PRICE PMAPP`
- `SKU DESCRIPTION PLATINUM PMAPP`
- Side-by-side variant: `SKU PLATINUM MAPP SKU PLATINUM MAPP`

Signature tokens:
- `SKU`
- `DESCRIPTION`
- `MAPP`
- `PMAPP`
- `PROMO PRICE`
- `PLATINUM`

## Quirks

- **Image-only free goods**: DeWalt B1G1 / B2G1 promos often render the
  free SKU only as a labeled product image, not as a row in the price
  table. Scan the page image for `FREE` callouts next to product
  pictures and read the SKU printed under each. See
  `edge-cases.md#image-only-free-skus-dewalt`.
- **Whitespace-broken price tokens**: DeWalt 2023 Q4 PDFs sometimes
  emit prices with internal spaces (`$ 1 33.00` for `$133.00`).
  Tolerate spaces inside the numeric portion.
- **Side-by-side tables**: when you see two `SKU ... MAPP` header
  blocks side-by-side, parse them as two independent column groups
  per row. See `edge-cases.md#side-by-side-tables-makita-q4`.
- **Date label**: Use `Advertising Window` or `Advertised Sell Through`.
  Never use Buy-In / Order-Pull windows.
- **`Atomic` and `XR` platform mentions** don't guarantee DeWalt — but
  combined with `DCF`/`DCS`/`DCD`/`DCB` SKU prefixes the detection is
  highly confident.
