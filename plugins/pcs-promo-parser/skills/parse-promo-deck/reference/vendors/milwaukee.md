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

Milwaukee uses several SKU shapes — standard tool/battery SKUs **plus** sub-brand
and apparel codes. The Step 5.5 verification gate (Layer B) applies the **first
regex below**, so it is a single alternation covering every accepted form:

```
\b(?:\d{2,4}-(?:\d{2,3}-)?\d{2,4}[A-Z]{0,3}|MXF\d{3,4}-\d[A-Z]{1,3}|\d{3,4}[A-Z]{1,3}-\d{2}[A-Z0-9]*|\d{4}[A-Z]{1,2}|E\d{2}\.\d{2}|TI\d{2}[A-Z]{2}|[A-Z]\d{3}[A-Z](?:/[A-Z])*|M[A-Z]{1,4}\d{2,4})\b
```

### Accepted SKU forms (sub-brands)

| Form | Example(s) | Branch |
|---|---|---|
| Standard tool / battery | `2962-22`, `2767-20`, `48-11-1850`, `48-73-1300` | `\d{2,4}-(?:\d{2,3}-)?\d{2,4}[A-Z]{0,3}` |
| MX Fuel | `MXF002-2XC` | `MXF\d{3,4}-\d[A-Z]{1,3}` |
| Letter-infix | `2855P-20`, `2935CU-21S` | `\d{3,4}[A-Z]{1,3}-\d{2}[A-Z0-9]*` |
| Bare model | `2013R` | `\d{4}[A-Z]{1,2}` |
| Empire | `E75.24` | `E\d{2}\.\d{2}` |
| Stiletto | `TI14MC` | `TI\d{2}[A-Z]{2}` |
| Apparel | `F251B/G/P` | `[A-Z]\d{3}[A-Z](?:/[A-Z])*` |
| Layout / accessory | `MLDIG14`, `MT205` | `M[A-Z]{1,4}\d{2,4}` |

These sub-brand forms (MX Fuel, Empire, Stiletto, apparel, layout/accessory) are
legitimate Milwaukee-family SKUs. The old digit-first / hyphen-required pattern
wrongly held them to For-Review — they're real products and belong in the NLP /
promo outputs.

**Why this is safe — and the one caveat.** The SKU pattern is only a *secondary*
sanity gate; the **real backstop is grounding** — every staged SKU must be
text-grounded and/or independently vision-confirmed against the page before it can
be written (Step 5.5 / `reference/verification.md`), and SKUs are only staged from
actual price-table / SKU-panel rows, never from footer text. The **bare-model
branch (`\d{4}[A-Z]{1,2}`) is the loosest** — it can match a stray 4-digit+letter
token — so it leans hardest on grounding. A bare year like `2026` (no trailing
letter) does not match it, and anything that slips through still has to be
vision-confirmed in a SKU column to be emitted.

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

**The on-slide pricing table is the price source — a cheat sheet should rarely
be needed for Milwaukee.** Combo-kit and multi-tool slides print a multi-column
table such as `ITEM # / DESCRIPTION / 50% OFF LIST / HEAVY DUTY / PROMO PRICE /
IMAP / PROMO IMAP`. Read the table off the slide image and take **`Promo IMAP`,
else `IMAP`**. The columns `50% OFF LIST`, `HEAVY DUTY` (/ `Heavy Duty Price`),
and `PROMO PRICE` are **NOT** the customer price — never pick them. Only fall
back to a cheat sheet when the slide genuinely has no readable IMAP/Promo IMAP
column; a priced Milwaukee slide should not land in `missing-price`.

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
- **`PCE# E-REBATE` = e-rebate → Other-Promotions.** When the PCE field reads
  the literal word `E-REBATE` (not 6 digits), the slide is an online-rebate
  promo — route the whole page to `Other-Promotions.csv` (Promo Type `e-rebate`)
  and emit NO kit rows, even though it shows a free-goods package + a price
  table. A `REDEEM AT …` header with a `milwaukeetool.com/e-rebate` URL is the
  same signal. (v1.2.0: e-rebates are parsed, not excluded.) See
  `reference/exclusion-markers.md#e_rebate_marker` and
  `reference/page-classification.md` (#3c).
- **Split battery slides (bold-line divider).** Milwaukee battery promos often
  put two free goods (e.g. a `$79` and a `$129` battery) on one slide and split
  the qualifying tools with a **bold black line**, each group earning only the
  battery on its side. Do NOT Cartesian every tool against both batteries — pair
  each group with its own free good. **If you can't confidently pair them, show
  the proposed split and ask the operator to confirm before holding it** (hold to
  For-Review only if unanswered). See
  `reference/edge-cases.md#split-slides--qualifying-groups-with-per-group-free-goods`.
