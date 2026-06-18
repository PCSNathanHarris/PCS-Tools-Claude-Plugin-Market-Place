# Output CSV schemas

All CSV outputs use `utf-8-sig` encoding, CRLF line endings, comma
delimiter, standard CSV quoting. (`For-Review` is the exception — an `.xlsx`
workbook.) See `conventions.md` for general rules (dates, prices, empty cells).

The schemas below match exactly what `kb/anglera.py`,
`kb/deck_parser/audit.py`, and `kb/nlp_sheet.py` produce in the
current app. The AI-stripped fork of the app reads these files as the
Stage 1 inputs to Stage 2/3/4 — column order matters.

---

## promo_list.csv

Source: `kb/kit_builder.py::write_promo_list_csv` / `PROMO_LIST_HEADERS`

**27 columns**, in this exact order:

| # | Column | Source / format |
|---|--------|-----------------|
| 1 | `Promo Name` | Free-text deal name + bracketed PCE/PCR if present, e.g. `"Mx Fuel Kit Get One Free [PCE 252601]"` |
| 2 | `Start Date` | `M/D/YYYY` non-padded |
| 3 | `End Date` | `M/D/YYYY` non-padded |
| 4 | `Item SKU 1` | First slot SKU |
| 5 | `Item Qty 1` | Integer, default `1` |
| 6 | `Item Price 1` | 2-decimal fixed (`199.00`) or `0.00` for free good |
| 7 | `Item Credit 1` | **Almost always blank** |
| 8–11 | `Item SKU 2` / `Qty 2` / `Price 2` / `Credit 2` | Same shape |
| 12–15 | `Item SKU 3` / ... / `Credit 3` | Same shape |
| 16–19 | `Item SKU 4` / ... / `Credit 4` | Same shape |
| 20–23 | `Item SKU 5` / ... / `Credit 5` | Same shape |
| 24–27 | `Item SKU 6` / ... / `Credit 6` | Same shape |

**Empty slots emit 4 empty cells** (SKU, Qty, Price, Credit all blank).

### Sample row — typical B1G1 (1 paid + 1 free)

```csv
Promo Name,Start Date,End Date,Item SKU 1,Item Qty 1,Item Price 1,Item Credit 1,Item SKU 2,Item Qty 2,Item Price 2,Item Credit 2,Item SKU 3,Item Qty 3,Item Price 3,Item Credit 3,Item SKU 4,Item Qty 4,Item Price 4,Item Credit 4,Item SKU 5,Item Qty 5,Item Price 5,Item Credit 5,Item SKU 6,Item Qty 6,Item Price 6,Item Credit 6
Mx Fuel Kit Get One Free [PCE 252601],5/4/2026,8/2/2026,2962-22,1,499.00,,48-11-1850,1,0.00,,,,,,,,,,,,,,,,,,,
```

### Sample row — multi-paid bundle (3 paid, no free)

```csv
86 Pc. Mix Drive Socket Set Bundle,3/1/2026,5/31/2026,81230P,1,99.99,,80950T,1,,,80551,1,,,,,,,,,,,,,,,,
```

(Bundle Retail in the first slot; other slots' Price/Credit blank.)

### Sample row — Cartesian explosion (2 paid × 2 free → 4 rows)

```csv
Buy a Drill, Get a Battery Free [PCE 262776],5/4/2026,8/2/2026,2962-22,1,499.00,,48-11-1850,1,0.00,,,,,,,,,,,,,,,,,,
Buy a Drill, Get a Battery Free [PCE 262776],5/4/2026,8/2/2026,2962-22,1,499.00,,48-11-2440,1,0.00,,,,,,,,,,,,,,,,,,
Buy a Drill, Get a Battery Free [PCE 262776],5/4/2026,8/2/2026,2767-22,1,549.00,,48-11-1850,1,0.00,,,,,,,,,,,,,,,,,,
Buy a Drill, Get a Battery Free [PCE 262776],5/4/2026,8/2/2026,2767-22,1,549.00,,48-11-2440,1,0.00,,,,,,,,,,,,,,,,,,
```

All four rows share the same Promo Name + dates.

---

## non_included.csv

Source: `kb/deck_parser/audit.py::write_non_included` / `NON_INCLUDED_HEADERS`

**5 columns**, in this exact order:

| # | Column | Source / format |
|---|--------|-----------------|
| 1 | `Page` | 1-indexed page number where the exclusion was detected |
| 2 | `Reason` | One of the reason codes below |
| 3 | `SKU` | Affected SKU (blank if page-level exclusion with no extracted SKUs) |
| 4 | `Deal Text` | Short snippet of the promo title / marker text from the page |
| 5 | `Detail` | Free-text detail — e.g. matched marker phrase, error message |

### Valid `Reason` codes

| Code | Cause |
|------|-------|
| `price-change` | NLP / Special Buy / Clearance / EDLP / Price Drop / `% Off` (only when page can't be NLP-routed) |
| `brick-and-mortar` | In-store only, branches only, B&M, not online |
| `spiff` | Sales-rep incentive |
| `rsa` | Retail Sales Associate incentive program |
| `spend-to-earn` | Buy $N in category → get reward; spend-and-earn rebates |
| `pos-redemption` | POS / mail-in / instant rebate or redemption mechanism |
| `arp` | Authorized Retailer Program — channel-restricted, not for general online |
| `killed` | Strikethrough on the SKU itself (deal cancelled) |
| `missing-price` | Paid SKU detected but no extractable price (non-Makita; Makita routes to `Needs-Pricing.csv` instead) |
| `image-only-free-good` | Free SKU visible only in image, no row in price table |
| `strikethrough` | SKU was struck out in the source — exclude |
| `new-product` | Page or section flagged as a new product launch / new arrival — skipped entirely (v0.3.0) |

**Retired in v0.3.0**: reason code `rsa` is no longer emitted. RSA pages
now route to `RSA-Kits.csv` / `RSA-NLP.csv` (see schemas below).

**Retired in v1.2.0**: reason codes `e-rebate`, `buy-more-save-more`, and
`promo-code-only` are no longer emitted to `Non-Included.csv`. Those pages are
now **parsed** into `Other-Promotions.csv` (see schema below). The
`Non-Included.csv` column layout is unchanged — only this reason set shrank.

### Sample rows

```csv
Page,Reason,SKU,Deal Text,Detail
23,price-change,2962-22,Get 20% Off Heavy-Duty Pricing,SPECIAL_BUY_MARKER matched: "20% Off"
45,brick-and-mortar,,In-Store Execution Only - Promote at $99,BM_MARKER matched
67,spend-to-earn,,Buy $800 in Concrete Accessories Get 1 Free,SPEND_TO_EARN_MARKER: "Buy $800"
12,missing-price,DCS438B,Buy Drill Get Battery Free,price column not found
22,pos-redemption,,Mail-In Rebate: $50 back by mail,POS_REDEMPTION_MARKER: "Mail-In Rebate"
31,arp,,ARP Exclusive — Authorized Retailer Only,ARP_MARKER matched
```

---

## nlp_sheet.csv

Source: `kb/nlp_sheet.py::write_nlp_sheet_csv` / `NLP_SHEET_COLUMNS`
(v0.5.9 expands this — see Promo Name column below)

**9 columns**, in this exact order:

| # | Column | Source / format |
|---|--------|-----------------|
| 1 | `Promo Name` | Free-text deal title + bracketed PCE/PCR (e.g. `"PCE 262776"`). Blank if no identifier visible. |
| 2 | `SKU` | One SKU per row |
| 3 | `Promo Price` | 2-decimal fixed price. **Blank if price unextractable** (user fills in manually downstream). |
| 4 | `Online Execution Start` | `M/D/YYYY` non-padded |
| 5 | `Online Execution End` | `M/D/YYYY` non-padded |
| 6 | `Vendor` | Display name, e.g. `Milwaukee` |
| 7 | `Page` | 1-indexed page number |
| 8 | `Price Label` | Which header column was matched (e.g. `Promo IMAP`, `MAP`) |
| 9 | `Source Marker` | `nlp` (NLP_MARKER matched) or `special-buy` (SPECIAL_BUY_MARKER matched) |

### Sample rows

```csv
Promo Name,SKU,Promo Price,Online Execution Start,Online Execution End,Vendor,Page,Price Label,Source Marker
MX FUEL Carry-On Power Supply Special Buy [PCE 262776],MXF002-2XC,1399.00,5/4/2026,8/2/2026,Milwaukee,33,Promo IMAP,special-buy
MX FUEL Carry-On Power Supply Special Buy [PCE 262776],MXF002-1XC,899.00,5/4/2026,8/2/2026,Milwaukee,33,Promo IMAP,special-buy
M18 Drill Driver NLP,2607-20,99.00,5/4/2026,8/2/2026,Milwaukee,67,IMAP,nlp
```

If a SKU has no extractable price, emit it anyway with `Promo Price`
blank — that's a flag for the user to fill in manually.

---

## parser_audit.csv

Source: skill-flavored variant. The original
`kb/deck_parser/audit.py::write_parser_audit` has fields specific to
the rule parser (skipped-page-by-marker breakdown); the skill emits a
simpler, AI-mode audit.

**20 columns** (v1.3.0), single row per parse run. **This file is ALWAYS
written** (even when every count is zero) — it is the run manifest, so
downstream stages can read the counts and know which other outputs exist
(empty outputs are not written; see the empty-file convention below).

| # | Column | Source |
|---|--------|--------|
| 1 | `Deck` | Path or filename of the parsed deck |
| 2 | `Vendor` | Detected vendor display name (e.g. `Milwaukee`) |
| 3 | `Total Pages` | Page count of the deck |
| 4 | `Kit Pages` | Pages classified as kit-promo |
| 5 | `NLP Pages` | Pages routed to NLP Sheet (NLP_MARKER / SPECIAL_BUY_MARKER) |
| 6 | `RSA Pages` | Pages classified as RSA (routed to RSA-Kits or RSA-NLP; v0.3.0) |
| 7 | `Excluded Pages` | Pages that landed in `Non-Included.csv` (true exclusions only — NOT Other-Promotions) |
| 8 | `Other-Promotions Pages` | Pages routed to `Other-Promotions.csv` (e-rebate / BMSM / promo-code; v1.2.0) |
| 9 | `Promo Rows` | Total rows in `Promo-List.csv` |
| 10 | `NLP Rows` | Total rows in `NLP-Sheet.csv` |
| 11 | `RSA Kit Rows` | Total rows in `RSA-Kits.csv` (v0.3.0) |
| 12 | `RSA NLP Rows` | Total rows in `RSA-NLP.csv` (v0.3.0) |
| 13 | `Needs Pricing Rows` | Total rows in `Needs-Pricing.csv` (v0.3.0; Makita usually 0 for other vendors) |
| 14 | `Non-Included Count` | Total rows in `Non-Included.csv` |
| 15 | `Other-Promotions Rows` | Total rows in `Other-Promotions.csv` (v1.2.0) |
| 16 | `For-Review Rows` | Total review items; `0` ⇒ no `For-Review.xlsx` is written (v1.2.0) |
| 17 | `Run At UTC` | ISO 8601 UTC timestamp (e.g. `2026-06-18T17:23:00Z`) |
| 18 | `Flags` | Semicolon-joined run-level flags (e.g. `crescent-unconfirmed`); blank when none (v1.2.0) |
| 19 | `SKUs Verified` | SKUs that passed the Step 5.5 verification gate and were written to an emit output (v1.3.0) |
| 20 | `SKUs Held` | SKUs/prices HELD by Step 5.5 (failed grounding) — withheld from every emit output and surfaced as `unverified` For-Review rows. **Excludes `missed-on-page`** (under-extraction, not a withheld emit). The orchestrator's reconcile anchor (v1.3.0) |

Columns 19-20 are **appended** (positions 1-18 unchanged) — positional readers keep working.

### Sample row

```csv
Deck,Vendor,Total Pages,Kit Pages,NLP Pages,RSA Pages,Excluded Pages,Other-Promotions Pages,Promo Rows,NLP Rows,RSA Kit Rows,RSA NLP Rows,Needs Pricing Rows,Non-Included Count,Other-Promotions Rows,For-Review Rows,Run At UTC,Flags,SKUs Verified,SKUs Held
Milwaukee_Q2_2026.pdf,Milwaukee,98,28,55,5,5,3,412,287,18,7,0,12,9,4,2026-06-18T17:23:00Z,crescent-unconfirmed,734,3
```

---

## RSA-Kits.csv

Source: v0.3.0 addition. Same 27-column schema as `Promo-List.csv` (see
top of this file). Difference is **how the rows are populated**:

- `Promo Name` ends with the literal suffix `-RSA`. Example:
  `"M18 Drill RSA Reward [P-00xxxxx]-RSA"`.
- `Item Credit N` columns carry the RSA credit amount for each slot
  (the dollar amount the associate earns per unit sold). Format is
  2-decimal fixed (`15.00`). Blank if credit amount was not
  extractable from the page.
- Otherwise, slot/qty/price conventions match `Promo-List.csv`.

### Sample row

```csv
Promo Name,Start Date,End Date,Item SKU 1,Item Qty 1,Item Price 1,Item Credit 1,Item SKU 2,Item Qty 2,Item Price 2,Item Credit 2,Item SKU 3,Item Qty 3,Item Price 3,Item Credit 3,Item SKU 4,Item Qty 4,Item Price 4,Item Credit 4,Item SKU 5,Item Qty 5,Item Price 5,Item Credit 5,Item SKU 6,Item Qty 6,Item Price 6,Item Credit 6
20V MAX RSA Reward Buy DCB205-2C [P-00xxxxx]-RSA,5/3/2026,8/3/2026,DCB205-2C,1,299.00,15.00,,,,,,,,,,,,,,,,,,,,
```

If there are no RSA kit rows for a given run, do NOT write `RSA-Kits.csv`
(v1.2.0 — empty outputs are skipped; the count lives in `Parser-Audit.csv`).

---

## RSA-NLP.csv

Source: v0.3.0 addition. Same 9-column schema as `NLP-Sheet.csv` plus
one additional 10th column `Credit Amount` appended at the right.

**10 columns**, in this exact order:

| # | Column | Source / format |
|---|--------|-----------------|
| 1 | `Promo Name` | Deal title + bracketed PCE/PCR if present, **with `-RSA` suffix appended** (e.g. `"M18 Battery RSA Incentive [PCE 262776]-RSA"`) |
| 2 | `SKU` | One SKU per row |
| 3 | `Promo Price` | 2-decimal fixed price (or blank if not extractable) |
| 4 | `Online Execution Start` | `M/D/YYYY` non-padded |
| 5 | `Online Execution End` | `M/D/YYYY` non-padded |
| 6 | `Vendor` | Display name |
| 7 | `Page` | 1-indexed page number |
| 8 | `Price Label` | Which header column was matched |
| 9 | `Source Marker` | Always `rsa` for this file |
| 10 | `Credit Amount` | 2-decimal fixed credit amount per unit (e.g. `15.00`); blank if not extractable |

### Sample row

```csv
Promo Name,SKU,Promo Price,Online Execution Start,Online Execution End,Vendor,Page,Price Label,Source Marker,Credit Amount
M18 Battery RSA Incentive [PCE 262776]-RSA,48-11-1850,99.00,5/4/2026,8/2/2026,Milwaukee,42,IMAP,rsa,5.00
```

If there are no RSA-NLP rows, do NOT write `RSA-NLP.csv` (v1.2.0 — empty
outputs are skipped).

---

## Needs-Pricing.csv

Source: v0.3.0 addition. Makita-only routing for paid SKUs where every
tier of the vendor price priority is blank or `N/A`. See
`reference/vendors/makita.md#missing-price-routing`.

**8 columns**, in this exact order:

| # | Column | Source / format |
|---|--------|-----------------|
| 1 | `Promo Name` | Deal title + bracketed promo identifier if present |
| 2 | `Page` | 1-indexed page number |
| 3 | `SKU` | The paid SKU missing pricing |
| 4 | `Qty` | Integer, default `1` |
| 5 | `Price Label Searched` | Pipe-separated list of every label tried, in priority order, e.g. `PMAP|MAP|HPP|Special Price|Promo Price` |
| 6 | `Deal Text` | Short snippet of the deal title or marker text from the page (for human context) |
| 7 | `Vendor` | Display name (always `Makita` under the v0.3.0 override) |
| 8 | `Source Marker` | `missing-price` |

### Sample row

```csv
Promo Name,Page,SKU,Qty,Price Label Searched,Deal Text,Vendor,Source Marker
XGT Hammer Drill Promo [XGT Q2 1.03.0],14,GMH04PLX,1,PMAP|MAP|HPP|Special Price|Promo Price,XGT Hammer Drill Promo - price TBD,Makita,missing-price
```

For non-Makita vendors there are normally no rows, so `Needs-Pricing.csv` is
simply not written (v1.2.0 — empty outputs are skipped).

---

## Other-Promotions.csv

Source: v1.2.0 addition. Holds promos that used to be excluded — Buy-More-
Save-More, e-rebate, and promo-code deals — now **parsed** with their SKUs +
details. One row per SKU (or one blank-SKU row if none were extractable).
**Written only when it has ≥1 row** (see empty-file convention below).

**16 columns**, in this exact order:

| # | Column | Source / format |
|---|--------|-----------------|
| 1 | `Promo Type` | `buy-more-save-more` \| `e-rebate` \| `promo-code` |
| 2 | `Promo Name` | Deal title + bracketed identifier (e-rebate may be `[PCE E-REBATE]`) |
| 3 | `SKU` | One vendor SKU per row; blank if none extractable |
| 4 | `Tier` | BMSM tier label (`Buy 5+`, `Buy 3 save $20`); blank otherwise |
| 5 | `Discount` | `10%` / `$20` / `$50 off`; blank for a pure e-rebate |
| 6 | `Rebate Amount` | e-rebate $ back / free-goods value (2-decimal, `50.00`); blank otherwise |
| 7 | `Redemption URL` | e-rebate portal URL; blank otherwise |
| 8 | `Promo Code` | Literal checkout code (`SUMMER25`); blank otherwise. **Never** a FLEX `SOT…` identifier |
| 9 | `Price` | Anchor / customer price if a table exists (2-decimal); blank if none |
| 10 | `Qty` | Integer, default `1` |
| 11 | `Start Date` | `M/D/YYYY` non-padded |
| 12 | `End Date` | `M/D/YYYY` non-padded |
| 13 | `Vendor` | Display name |
| 14 | `Page` | 1-indexed page number |
| 15 | `Source Marker` | `bmsm` \| `e-rebate` \| `promo-code` |
| 16 | `Detail` | Free-text: matched marker phrase / tier ladder / notes |

Type-specific columns are blank when not applicable (a BMSM row leaves
`Rebate Amount` / `Redemption URL` / `Promo Code` blank, etc.).

### Sample rows

```csv
Promo Type,Promo Name,SKU,Tier,Discount,Rebate Amount,Redemption URL,Promo Code,Price,Qty,Start Date,End Date,Vendor,Page,Source Marker,Detail
buy-more-save-more,Buy More Save More Accessories,48-11-1850,Buy 5+,10%,,,,,1,5/4/2026,8/2/2026,Milwaukee,52,bmsm,"Tiered: 5+=10%, 10+=15%"
e-rebate,Buy an M12 FUEL ProPEX Get Free Goods [PCE E-REBATE],2473-22,,,79.00,milwaukeetool.com/e-rebate/ic,,399.00,1,5/4/2026,8/2/2026,Milwaukee,71,e-rebate,"REDEEM AT .../e-rebate; PCE# E-REBATE; free goods present"
promo-code,Summer Savings Coupon,,,$50 off,,,SUMMER25,,1,6/1/2026,6/30/2026,DeWalt,88,promo-code,"Use code SUMMER25 at checkout"
```

---

## For-Review.xlsx

Source: v1.2.0 addition. **An `.xlsx` workbook, not a CSV** — and **written only
when there is ≥1 review item** (the one conditional, non-CSV output). It collects
everything the parser could not confidently classify (Review Class
`low-confidence`), any row missing required data (Review Class `missing-data`),
and any SKU/price **held by the Step 5.5 verification gate** (Review Class
`unverified`). Generated by a throwaway `openpyxl` script (the marketplace
ships no runtime code); one sheet named `For Review`, with a **bold + frozen
header row**.

**10 columns**, in this exact order:

| # | Column | Meaning |
|---|--------|---------|
| 1 | `Review Class` | `low-confidence` \| `missing-data` \| `unverified` |
| 2 | `PCE/Identifier` | PCE / PCR / Flex-SOT / Makita code if any (matches the chat table) |
| 3 | `Promo Name` | Deal title as extracted (may be partial) |
| 4 | `Page` | 1-indexed page number |
| 5 | `Vendor` | Display name |
| 6 | `Reason(s)` | Semicolon-joined reason codes (vocab below) |
| 7 | `SKUs` | Comma-joined SKUs (blank if none) |
| 8 | `Missing Field` | `price` \| `sku` for missing-data; blank for low-confidence / unverified |
| 9 | `Suggested Bucket` | `kit` \| `nlp` \| `other-promotions` \| `non-included` \| `unknown` (parser's best guess) |
| 10 | `Detail` | What was ambiguous / which markers conflicted / source snippet |

**Reason vocabulary:** `ambiguous-layout`, `conflicting-markers`,
`unknown-page-type`, `crescent-layout-unconfirmed`, `missing-price`,
`missing-price-makita`, `missing-sku`, `split-mapping-unconfirmed`,
`multi-promo-unclear`; **verification holds (v1.3.0):** `unverified-sku`,
`sku-pattern-mismatch`, `unverified-price`, `price-cheatsheet-mismatch`,
`missed-on-page`.

**Surfacing rules.** For-Review is **additive** for `low-confidence` /
`missing-data` (the row still goes to its normal bucket) but **subtractive** for
`unverified` — a verification-held row is **withheld** from its emit output by the
Step 5.5 gate and exists only here.
- Non-Makita missing-price → stays in `Non-Included.csv` (`missing-price`) AND a
  `missing-data` For-Review row.
- Makita all-tiers-blank → stays in `Needs-Pricing.csv` AND a `missing-data`
  For-Review row (`missing-price-makita`).
- Crescent unconfirmed → best-effort rows still emitted to their normal buckets
  AND a `low-confidence` For-Review row per uncertain page.
- Split-slide mapping the operator didn't confirm → no guess, skip those pairs,
  emit a `low-confidence` row (`split-mapping-unconfirmed`).
- Genuinely unclassifiable page (classification 8a) → For-Review only, Suggested
  Bucket `unknown`.
- **Verification hold (v1.3.0)** → the failing SKU/price is HELD out of
  Promo-List / NLP / RSA / Other-Promotions; `Suggested Bucket` = the output it
  would have gone to (so a human can re-admit it after fixing the source).
  `missed-on-page` = a SKU/price the independent verifier saw but the extraction
  omitted — surfaced here, never auto-emitted. See `verification.md`.

**Chat table** (printed only when the workbook is written), columns **exactly**:
`PCE/Identifier | Page # | Reason(s) | SKUs`, followed by a markdown link to the
workbook.

---

## Empty-file convention (v1.2.0 — reversed)

**Write an output only when it has at least one data row.** Do NOT emit empty /
header-only files. A consumer that doesn't find a file must read it as "zero
rows of that type," not as an error.

Two anchors keep this safe:
- **`Parser-Audit.csv` is ALWAYS written** (one summary row) and records the
  count for every other output — it is the run manifest.
- **`For-Review.xlsx`** is also conditional (written only when there are review
  items) and is the only `.xlsx` / non-CSV output.

(Earlier versions emitted header-only files for empty lists; that convention is
retired as of v1.2.0.)

**v1.3.0:** a list that had rows before the Step 5.5 verification gate but was
**fully held** produces no file — `Parser-Audit` shows `0` rows for it and a
non-zero `SKUs Held`. Reconcile via the audit, not by treating the missing file
as an error.
