# Makita

## Brand keywords

- `makita`
- `lxt` (18V LXT platform)
- `xgt` (40V XGT platform)
- `cxt` (12V CXT platform)

## SKU pattern

Regex: `\b[A-Z]{2,4}\d{2,4}[A-Z0-9-]*\b`

Examples:
- `XAD02Z`, `XPH14Z`, `GT200D` (cordless tools)
- `BL1850B`, `BL4040` (batteries)
- `GMH04PLX` (XGT kits)

The pattern is broader than DeWalt's — Makita uses many letter
prefixes (`X`, `B`, `G`, `D`, `R`, etc.). Be conservative: only emit
SKUs that match this shape AND appear in/near a price-bearing row.

## Promo code pattern

Regex: `\b(XGT|LXT)[\s-]*([A-Z0-9.\s]+?\d+(?:\.\d+)?)` (case-insensitive)

Examples:
- `XGT Q2 1.03.0`
- `LXT 2025 Q3`

Makita codes are bottom-right corner identifiers; often absent entirely.
When present, append in brackets to `promo_name`:

- `"FX01-Z XGT Hammer Drill Promo [XGT Q2 1.03.0]"`

If no code is visible, the deal title alone is `promo_name`.

## Price label priority

1. `PMAP` (Promo MAP)
2. `MAP`
3. `HPP` (rarely used; some legacy decks)
4. `Special Price`
5. `Promo Price`

**Fallback rule (v0.3.0 — explicit)**: walk the list above in order and
take the **first non-empty tier**. If `PMAP` is missing, fall through
to `MAP`, then `HPP`, then `Special Price`, then `Promo Price`. A paid
SKU must NOT be dropped if any tier has a value. See
`reference/conventions.md#price-label-fallback-rule`.

## Missing-price routing

**Makita-specific override (v0.3.0)**: Makita decks regularly ship rows
with blank or `N/A` prices because vendor pricing decks haven't been
finalized yet. The team fills these in manually.

When a paid SKU is detected on a Makita page but **every** tier in the
priority list is blank or `N/A`:

- Do **NOT** drop to `non_included.csv` with reason `missing-price`
  (that's the rule for other vendors).
- **Emit the row to `Makita-<QN>-<YYYY>-Needs-Pricing.csv`** with the
  schema documented at `reference/output-csvs.md#needs-pricingcsv`.
- The team uses this file as a worklist — they fill in the missing
  pricing and merge those rows into the main promo list manually.

This override only fires when ALL tiers are empty. If even one tier
(e.g. `MAP`) has a value, follow the fallback rule and emit to
`promo_list.csv` normally.

For all other vendors (DeWalt, Milwaukee, Bosch, EGO, Flex, GearWrench,
Crescent), the standard `non_included` reason `missing-price` routing
still applies.

## Non-price labels (CRITICAL — NEVER treat as price)

- **`Dealer`** — wholesale cost
- **`M1`**, **`M2`**, **`M3`** — purchase tiers (NOT prices). Common
  trap. "M1" looks like a price column but it's a buying-volume tier.
- `List Price` — sometimes shown but always lower priority than MAP
- `Description`
- `QTY`

## Header signatures

Most common headers:
- `Model Description Dealer M1 MAP` (most common — 129+ pages in audit)
- `Model Description Dealer M1 MAP PMAP`
- `MODEL # LIST PRICE DEALER M1 MAP`

Signature tokens:
- `Model`, `Model #`
- `Description`
- `Dealer`
- `M1`
- `MAP`
- `PMAP`
- `HPP`
- `List Price`
- `Special Price`
- `Promo Price`
- `QTY`
- `Total Price`

## Quirks

- **`M1` is a purchase tier, NOT a price**. NEVER pick the `M1` column
  as the customer price. The customer price is `MAP` (or `PMAP` when
  shown).
- **`receive M1`** in promo title text refers to the M1 purchase tier,
  not a SKU named "M1" — ignore.
- **`Recommended Accessory` lines** are NOT part of the deal — exclude
  any SKUs on those lines.
- **Side-by-side tables** (Makita Q4 layouts): two parallel SKU+price
  tables on one page. See `edge-cases.md#side-by-side-tables-makita-q4`.
- **Date label**: `Promo Execution`.
- **XGT vs LXT vs CXT**: separate Makita platforms. A page may carry
  only XGT-prefix codes; treat platform name as a non-blocking hint —
  the SKUs and price labels are the same Makita conventions.
