# Description spec — Task description content + storefront mapping

The Task description is markdown. Render in this order, with these
exact section headings (case-sensitive).

## Template

```markdown
**Date range:** <Start Date> – <End Date>

**Funding source:** <text if extractable; e.g. "Fully Funded by Milwaukee", "Apex Funded — 10/5 split"; omit the line if not known>

**Promo Identifier:** <PCE NNNNNN | PCR NNNNNN | leave blank if none>

**SKUs:**
| Slot | SKU | Qty | Price | Notes |
| --- | --- | --- | --- | --- |
| Paid | 2962-22 | 1 | $499.00 | M18 FUEL ½" Hammer Drill |
| Free | 48-11-1850 | 1 | FREE | M18 REDLITHIUM XC5.0 Battery |

**Collection Links:**
TUP - <blank URL — Nathan fills in collection link>
RTS - <blank URL — Nathan fills in collection link>
MTS - <blank URL — Nathan fills in collection link>

**NetSuite:**
Promo - <blank URL — paste NS Promo URL>
Redemption Tracking - <blank URL — paste NS Saved Search URL>

**Source:** <CSV filename> row <N>[, deck page <N> if available]
```

## Section rules

- **Date range:** required. Convert parser `M/D/YYYY` to a readable
  format (e.g. `5/4/2026 – 8/2/2026`) — em-dash separator.
- **Funding source:** omit the line entirely if you can't extract one.
  Don't put `Funding source: (unknown)` — it adds noise.
- **Promo Identifier:** show only if a PCE/PCR was in the parser's
  Promo Name. When PCS adds a dedicated custom field, this line goes
  away (skill bumps version).
- **SKUs:** required. One row per slot for Promo-List groups (paid
  rows first, then free); one row per SKU for NLP-Sheet groups (single
  paid SKU each). Use `FREE` literal in the Price column for slots
  where price = 0.00.
- **Collection Links:** required. Use the per-vendor mapping below.
  Always render the labels with blank URLs — never invent URLs.
- **NetSuite:** required. Always emit both `Promo` and `Redemption
  Tracking` rows with blank URLs.
- **Source:** required. Always include for traceability.

## Other-Promotions description (BMSM / e-rebate / promo-code) — v0.2.0

For `Other-Promotions.csv` Tasks, render the standard Template (Date range,
Promo Identifier, SKUs, Collection Links, NetSuite, Source) **plus** a
type-specific block right after the Promo Identifier line:

- **Promo type:** `Buy More Save More` | `E-Rebate` | `Coupon` (from `Promo Type`).
- **e-rebate** → also add:
  ```
  **Rebate amount:** $<Rebate Amount>
  **Redeem at:** <Redemption URL>
  ```
- **promo-code** → also add:
  ```
  **Promo code:** <Promo Code>
  **Discount:** <Discount>
  ```
- **buy-more-save-more** → also add:
  ```
  **Tiers:** <tier ladder, e.g. "Buy 5+ = 10% off; Buy 10+ = 15% off">
  **Discount:** <Discount>
  ```

The **SKUs** table lists the qualifying SKUs — one row per SKU, `Slot` = `Item`,
`Price` = the `Price` column when present (else blank), `Notes` = model /
description. These promos have no paid/free pairing, so don't force `FREE` rows.

Never render a FLEX `SOT…` identifier as a **Promo code:** — it belongs on the
**Promo Identifier:** line.

## Image handling

**Never reference images in the description.** No `Deck Page Screenshot: [paste image]`
placeholder, no "see attached" line.

When a Jira token file is present (`reference/integrations.md`), attach the promo's
**deck-page screenshot** — resolved from the row's `Page` to the parser's
`deck_pages/p<NNN>.png` (`reference/deck-images.md`) — via the direct Jira REST call.
No token / no page image → silently omit. The image is also **read** (not described) to
set Needs POS Redemption.

## NLP sub-task attachments (v0.3.0)

For a consolidated NLP parent's date-group sub-tasks (`reference/nlp-consolidation.md`),
attach the two generated CSVs (start-pricing + revert schedule) to each **sub-task** (not
the parent). The parent description lists the date groups + overall window; each
sub-task's description is the `MM/DD-MM/DD` window + a one-line "pricing + revert schedule
attached." Don't dump the SKU table into the body.

## Promo Deck URL is a field, not a description line

Set the **Promo Deck URL** custom field (`reference/integrations.md` Drive search) — do
**not** also add a deck-link line to the description (avoid duplication).

## Vendor → Storefront mapping

Per-vendor list of Collection Link rows to emit. Each row uses the
storefront short code, a literal ` - `, then a blank URL placeholder.

| Vendor | Storefronts (emit one row per code, in this order) |
|---|---|
| Milwaukee | TUP, RTS, MTS |
| DeWalt | TUP, ATO, MTS |
| GearWrench | TUP, GWS, MTS |
| Crescent | TUP, MTS |
| Bosch | TUP, MTS |
| EGO | TUP, MTS |
| Flex | TUP, MTS |
| Makita | TUP, JPT, MTS |
| JPW | TUP |
| Fluke | TUP |
| SKIL | TUP |
| Stiletto / Empire (Milwaukee sub-brands) | (inherit Milwaukee: TUP, RTS, MTS) |

Storefront short codes:

| Code | Full name | Notes |
|---|---|---|
| TUP | ToolUp | PCS main storefront, everything-style coverage |
| RTS | RedToolStore | Milwaukee-focused |
| ATO | AuthorizedToolOutlet | DeWalt / SBD-focused |
| GWS | GearWrenchShop | Apex / GearWrench-focused |
| JPT | Jobsite Power Tools | Makita-only channel |
| MTS | My Tool Store | Everything-style storefront, similar coverage to TUP |

## Rendering details

- Use markdown tables for the SKU section. Stick to the column order
  shown (`Slot | SKU | Qty | Price | Notes`).
- Render prices with a leading `$` and 2-decimal fixed: `$499.00`,
  `$1,395.00`. For free goods, use the literal `FREE` (not `$0.00`).
- The `Notes` column carries the SKU's description / model name when
  available; leave blank if not extractable.
- Don't include the Cartesian explosion as separate rows. The full
  paid × free matrix collapses into one SKU table with paid SKUs in
  the upper rows and free SKUs in the lower rows.

## Example — Milwaukee Q3 2026 Free Battery promo

```markdown
**Date range:** 5/4/2026 – 8/2/2026

**Funding source:** Fully Funded by Milwaukee

**Promo Identifier:** PCE 262776

**SKUs:**
| Slot | SKU | Qty | Price | Notes |
| --- | --- | --- | --- | --- |
| Paid | 2962-22 | 1 | $499.00 | M18 FUEL ½" Hammer Drill |
| Paid | 2767-22 | 1 | $549.00 | M18 FUEL ¼" Hex Impact |
| Free | 48-11-1850 | 1 | FREE | M18 REDLITHIUM XC5.0 Battery |
| Free | 48-11-2440 | 1 | FREE | M18 REDLITHIUM HD9.0 Battery |

**Collection Links:**
TUP - 
RTS - 
MTS - 

**NetSuite:**
Promo - 
Redemption Tracking - 

**Source:** Milwaukee-Q3-2026-Promo-List.csv rows 12–15
```
