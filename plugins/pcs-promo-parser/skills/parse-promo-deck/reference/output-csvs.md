# Output CSV schemas

All four files use `utf-8-sig` encoding, CRLF line endings, comma
delimiter, standard CSV quoting. See `conventions.md` for general rules
(dates, prices, empty cells).

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
| `buy-more-save-more` | BMSM, volume-tiered pricing, "Buy 5 save 10%" |
| `promo-code-only` | Page IS a coupon code (use code XYZ at checkout) |
| `arp` | Authorized Retailer Program — channel-restricted, not for general online |
| `killed` | Strikethrough on the SKU itself (deal cancelled) |
| `missing-price` | Paid SKU detected but no extractable price (non-Makita; Makita routes to `Needs-Pricing.csv` instead) |
| `image-only-free-good` | Free SKU visible only in image, no row in price table |
| `strikethrough` | SKU was struck out in the source — exclude |
| `new-product` | Page or section flagged as a new product launch / new arrival — skipped entirely (v0.3.0) |

**Retired in v0.3.0**: reason code `rsa` is no longer emitted. RSA pages
now route to `RSA-Kits.csv` / `RSA-NLP.csv` (see schemas below).

### Sample rows

```csv
Page,Reason,SKU,Deal Text,Detail
23,price-change,2962-22,Get 20% Off Heavy-Duty Pricing,SPECIAL_BUY_MARKER matched: "20% Off"
45,brick-and-mortar,,In-Store Execution Only - Promote at $99,BM_MARKER matched
67,spend-to-earn,,Buy $800 in Concrete Accessories Get 1 Free,SPEND_TO_EARN_MARKER: "Buy $800"
89,promo-code-only,,Use Code SUMMER25 at Checkout,PROMO_CODE_MARKER: "use code"
12,missing-price,DCS438B,Buy Drill Get Battery Free,price column not found
14,rsa,,RSA Reward Program — Earn $15 per Kit Sold,RSA_MARKER matched
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

**13 columns** (v0.3.0), single row per parse run:

| # | Column | Source |
|---|--------|--------|
| 1 | `Deck` | Path or filename of the parsed deck |
| 2 | `Vendor` | Detected vendor display name (e.g. `Milwaukee`) |
| 3 | `Total Pages` | Page count of the deck |
| 4 | `Kit Pages` | Pages classified as kit-promo |
| 5 | `NLP Pages` | Pages routed to NLP Sheet (NLP_MARKER / SPECIAL_BUY_MARKER) |
| 6 | `RSA Pages` | Pages classified as RSA (routed to RSA-Kits or RSA-NLP; v0.3.0) |
| 7 | `Excluded Pages` | Pages that landed in `non_included.csv` (sum of all non-NLP, non-RSA exclusion reasons) |
| 8 | `Promo Rows` | Total rows in `Promo-List.csv` |
| 9 | `NLP Rows` | Total rows in `NLP-Sheet.csv` |
| 10 | `RSA Kit Rows` | Total rows in `RSA-Kits.csv` (v0.3.0) |
| 11 | `RSA NLP Rows` | Total rows in `RSA-NLP.csv` (v0.3.0) |
| 12 | `Needs Pricing Rows` | Total rows in `Needs-Pricing.csv` (v0.3.0; Makita usually 0 for other vendors) |
| 13 | `Non-Included Count` | Total rows in `Non-Included.csv` |
| 14 | `Run At UTC` | ISO 8601 UTC timestamp (e.g. `2026-05-12T17:23:00Z`) |

### Sample row

```csv
Deck,Vendor,Total Pages,Kit Pages,NLP Pages,RSA Pages,Excluded Pages,Promo Rows,NLP Rows,RSA Kit Rows,RSA NLP Rows,Needs Pricing Rows,Non-Included Count,Run At UTC
Milwaukee_P2_2026.pdf,Milwaukee,98,28,55,5,8,412,287,18,7,0,15,2026-05-12T17:23:00Z
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

If `RSA-Kits.csv` has no rows for a given run, emit a header-only file.

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

Emit header-only if no RSA-NLP rows.

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

Emit header-only for non-Makita vendors (file exists but contains only
the header row).

---

## Empty-file convention

Even when a list is empty, **emit the header-only file**. Downstream
stages of the app expect all four files to exist.

For example, a deck with no excluded pages still writes:

```csv
Page,Reason,SKU,Deal Text,Detail
```

(Just the header row, terminated by `\r\n`.)
