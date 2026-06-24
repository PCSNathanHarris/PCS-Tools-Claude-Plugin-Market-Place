# DeWalt

## Brand keywords

- `dewalt`
- `atomic` (Atomic platform)
- `flexvolt`
- `20v max`, `60v max`
- `xr` (softer signal)

## SKU pattern

Regex: `\bD[CW](?:[A-Z]{1,2})?\d{3,4}[A-Z0-9-]*\b`

Examples:
- `DCF891B`, `DCS438B`, `DCD800B` (bare-tool SKUs)
- `DCB205-2C` (battery 2-packs)
- `DCK2050M2` (combo kits)
- `DWHT16071` (hand tools — DW prefix variant)
- `DW735`, `DW7350`, `DW735X` (bare corded / benchtop line — `DW` + digits, **no middle letter**)
- `DWS713`, `DWE7491RS`, `DWX723` (corded saws / stands)

The pattern matches `DC` (cordless) or `DW` (corded / hand-tool) prefixes, an
**optional** 1–2 alpha letters, then 3–4 digits, optionally followed by configuration
suffixes. The 1–2-letter group is **optional** so bare corded SKUs like `DW735`
(`DW` + `735`, no middle letter) match — older benchtop / corded SKUs were previously
held to For-Review as `sku-pattern-mismatch`. It still rejects non-SKU noise (phone
numbers, dates) thanks to the required `D[CW]` prefix and word boundaries.

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
- `IN-STORE ONLY` (a channel flag in the PMAPP / price column — **not** a price; it's a
  brick-and-mortar exclusion signal, see below)
- `N/C` (free good — no charge), `Bundle` (bundled member), `N/A` (no price)

## PMAPP column = the online / in-store oracle (DeWalt)

The tracker / cheat-sheet `PMAPP` value is the single most important DeWalt channel
signal — apply it **per SKU** (mixed pages are common, e.g. one in-store SKU among online
ones, or mixed battery rows):

- **numeric `PMAPP`** → online-eligible: build the kit / NLP at that price.
- **`PMAPP = IN-STORE ONLY`** → **brick-and-mortar exclusion.** Route the SKU to
  `Non-Included.csv` reason `brick-and-mortar` — **no kit, no NLP, no Other-Promotions
  row, no Jira task.** The deck footer `ADVERTISING WINDOW: IN-STORE ONLY` is the same
  signal at the page level (both agreed across the Q3 deck).
- **`N/C`** → free good (price `0.00`).
- **`Bundle`** → bundled member (price `0.00`; total on the anchor — see
  `edge-cases.md#multi-paid-bundle-no-free-goods`).
- **`N/A`** → no price (fall through the price-label chain; if all tiers blank →
  `missing-price`).

Volume / spend-threshold programs (e.g. "buy 9 adhesive boxes get 1 free", spend-tier
discounts, pallet pricing) with **no online advertising window** are likewise not
online-executable → `Non-Included` (`brick-and-mortar` / `spend-to-earn`), **never**
`Other-Promotions`. Only genuinely online BMSM / e-rebate / promo-code deals belong in
`Other-Promotions.csv`.

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
- **Title vs PMAPP price disagreement**: when a deal's prose / title says one price but the
  PMAPP Selling Price column says another (e.g. `DCB210-2` Labor Day RSA NLP reads "@ $329"
  in the description but PMAPP = `$269.00`), **emit the PMAPP price** (every sibling row uses
  PMAPP) and **flag it to For-Review** — never silently auto-resolve a price disagreement.
- **Confidentiality footer**: every DeWalt page repeats `Confidential Document Property of
  DEWALT…`; **ignore it** when scoring `new-product` / `brick-mortar` markers (it falsely
  tripped page triage). Anchor `new-product` on section headers (`NEW PRODUCT LAUNCHES`,
  `TRANSITION TIMELINE`), not stray footer words. See `page-classification.md`.
- **`Atomic` and `XR` platform mentions** don't guarantee DeWalt — but
  combined with `DCF`/`DCS`/`DCD`/`DCB` SKU prefixes the detection is
  highly confident.
