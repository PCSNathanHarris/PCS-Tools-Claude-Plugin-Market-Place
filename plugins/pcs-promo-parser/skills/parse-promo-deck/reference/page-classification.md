# Page classification decision tree

For every page in the deck, walk this tree top-to-bottom. **First match
wins** — once a page hits any rule it's classified, and you move on to
the next page.

The exact marker phrases and regex equivalents are in
`exclusion-markers.md`. This file is the priority logic only.

---

## Decision tree (priority order)

### 1. Strikethrough on entire SKU panel → `non_included` reason `killed`

If the whole price panel / SKU list on the page is visually struck out,
the entire deal was killed before publication. Emit one
`non_included` row per affected SKU with reason `killed`. Do NOT emit
to `promo_rows` or `nlp_rows`.

Distinguish from individual struck SKUs in an otherwise-active panel
— those route to `non_included` reason `strikethrough` (see #10 below)
but the rest of the page still parses normally.

### 2. Brick-and-mortar / in-store-only / not-online → `non_included` reason `brick-and-mortar`

Pages stamped as B&M-only, in-store execution only, branches only,
direct-ship only, etc. These can't be sold online so we don't kit them.

Emit one `non_included` row (with the page's primary SKU if extractable,
blank otherwise).

**Apply per-SKU on mixed pages.** The signal can be page-level (a deck footer like DeWalt's
`ADVERTISING WINDOW: IN-STORE ONLY`) **or per-SKU** (e.g. the DeWalt tracker's
`PMAPP = IN-STORE ONLY` on some rows of an otherwise-online page). When only some SKUs are
in-store, exclude **just those** SKUs to `brick-and-mortar` and parse the rest of the page
normally — like the per-SKU strikethrough handling (#10). See
`vendors/dewalt.md` ("PMAPP column = the online / in-store oracle").

### 3. SPIFF / sales-rep incentive → `non_included` reason `spiff`

Sales-rep-only incentives (e.g. "$20 SPIFF for moving 5 units"). Not
customer-facing.

### 3a. RSA / Retail Sales Associate incentive → dedicated RSA outputs

**Routing change (v0.3.0)**: RSA pages no longer route to
`non_included.csv`. They route to two new dedicated outputs:

- Kit-shaped RSA promos (anchor + free good with a credit amount per
  pairing) → `<Vendor>-<QN>-<YYYY>-RSA-Kits.csv` (same 27-col schema as
  `promo_list.csv`; populate `Item Credit N`).
- Single-SKU RSA promos (associate earns $N per unit, no pairing) →
  `<Vendor>-<QN>-<YYYY>-RSA-NLP.csv` (same 9-col schema as
  `nlp_sheet.csv` plus a 10th `Credit Amount` column appended at the
  right).

**Append `-RSA` to the `Promo Name` cell** on every RSA row so the
suffix survives downstream merging. Example:
`"M18 Drill RSA Reward [P-00xxxxx]"` → `"M18 Drill RSA Reward [P-00xxxxx]-RSA"`.

**Mixed pages (customer promo + RSA section)**: emit the customer-facing
kit rows to `promo_list.csv` AND the RSA rows to RSA-Kits/RSA-NLP. Both
paths run; they're not mutually exclusive.

See `exclusion-markers.md#rsa_marker` for credit-amount extraction
patterns.

### 3b. New product launch → `non_included` reason `new-product`

Pages or sections highlighting **new product launches / new arrivals**
are vendor announcements, not promos. Skip them entirely.

Emit one `non_included` row per page (with the page's primary SKU if
extractable, blank otherwise) with reason `new-product`. Do NOT emit
kit, NLP, or RSA rows for these pages.

See `exclusion-markers.md#new_product_marker` for phrase list.

Distinguish carefully from **NLP** (`New Lower Price` / case #7) —
that's a shelf-price drop and routes to the NLP Sheet, not exclusions.
Match NLP first.

**Footer triage — ignore repeated confidentiality footers.** Score `new-product` (and
`brick-mortar`) on **section headers**, not on stray words in a page footer. DeWalt repeats
`Confidential Document Property of DEWALT…` on every page, which falsely tripped
`NEW PRODUCT` / `BRICK-MORTAR` triage; ignore that boilerplate footer and anchor the
classification on real section banners (`NEW PRODUCT LAUNCHES`, `TRANSITION TIMELINE`).

### 3c. E-rebate (online rebate portal) → `other_promotions` (Promo Type `e-rebate`)

Slides fulfilled through an online rebate portal are not kits, even though they
show a "free goods package" and a price table. They are also NOT a Non-Included
exclusion — route them to `Other-Promotions.csv`. Identify by either signal:

- A `REDEEM AT …` header with an `e-rebate` URL (e.g.
  `milwaukeetool.com/e-rebate`), or
- A **PCE / promo identifier whose value is `E-REBATE`** (non-numeric) — this
  alone is decisive.

Emit one `other_promotions` row per affected SKU with Promo Type `e-rebate`
(capture the redemption URL and any rebate amount / anchor price). Emit **no**
kit / NLP / RSA rows and **no** Non-Included row for the page. **This is checked
here — above the kit fallthrough — and OVERRIDES the "B1G1 table → kit page"
exception in 4a.** A free-goods package + price table does NOT turn an e-rebate
slide into a kit; it becomes an Other-Promotions (e-rebate) row instead.
See `exclusion-markers.md#e_rebate_marker`.

### 4. Spend-to-earn / rebate → `non_included` reason `spend-to-earn`

The customer must spend a threshold dollar amount to earn the free good.
Examples: "Buy $800 in Concrete Accessories Get 1 Free", "Earn $50
rebate when you spend $500", "$100 in promo bucks". These are NOT kits
— there's no fixed paid/free pair.

### 4a. POS Redemption / mail-in rebate → `non_included` reason `pos-redemption`

Pages where the entire deal mechanism is a point-of-sale redemption,
mail-in rebate, or similar form-based reward. There is no fixed free-
good SKU paired at the kit level.

Examples: "Mail-In Rebate: $50 back by mail", "POS Redemption — present
at register", "Rebate Form enclosed".

Exception: if the page also carries a full B1G1 price table with paired
free-good SKUs, classify as a kit page (#9) — the kit structure wins.
**But e-rebate slides (#3c) are exempt from this exception** — an
`E-REBATE` PCE or a `REDEEM AT …/e-rebate` header routes the page to
`Other-Promotions.csv` (Promo Type `e-rebate`) even with a full free-goods
table; it is never kitted.

### 5. Buy-More-Save-More / volume-tiered → `other_promotions` (Promo Type `buy-more-save-more`)

Pages that say "Buy 5 save 10%" or "Buy More Save More" or "BMSM" or
"Volume Discount". Tiered pricing, not a fixed kit. Emit one `other_promotions`
row per SKU (capture the tier text in `Tier` and the discount in `Discount`). Emit no
kit / NLP / RSA rows.

**Online-window gate (only ONLINE BMSM goes to Other-Promotions).** A BMSM / volume /
spend-tier deal belongs in `Other-Promotions.csv` **only if it has an online advertising
window**. If it's in-store-only or has no online window (e.g. DeWalt `PMAPP = IN-STORE ONLY`,
a spend-threshold with no online dates, pallet / contractor pricing), route it to
`Non-Included.csv` instead — reason `brick-and-mortar` (in-store) or `spend-to-earn`
(threshold) — so it **never becomes a Jira task**. Anchors-&-Fasteners-style volume programs
(spend-tier discounts, push-in coupler pallet pricing, "buy 9 boxes get 1 free") are the
typical case: Non-Included, not Other-Promotions.

### 6. Promo-code / coupon / checkout-code only → `other_promotions` (Promo Type `promo-code`)

Pages whose entire deal is "Use code XYZ at checkout for $50 off." There's no
free good — the page IS the discount mechanism. Route to `Other-Promotions.csv`
(Promo Type `promo-code`); capture the checkout code in `Promo Code` and the
discount in `Discount`. Emit no kit / NLP / RSA rows and no Non-Included row.

**TRAP**: FLEX uses `PROMO CODE: SOT2514219` as a deal **identifier**, not a
discount code. That pattern alone does NOT make the page promo-code and must NOT
create an Other-Promotions (promo-code) row — carry the identifier in the deal
title brackets instead. See `exclusion-markers.md` for the carve-out.

### 6a. ARP / Authorized Retailer Program → `non_included` reason `arp`

Pages for Authorized Retail Program deals that are channel-restricted
and cannot be sold through general online channels.

Emit one `non_included` row per page (with the page's primary SKU if
extractable, blank otherwise). Do NOT emit kit rows even if a price
table is present — the channel restriction takes precedence.

### 7. NLP / Special Buy / Clearance / % Off / Price Drop → emit to `nlp_rows`

This is the special routing case. Pages with permanent or
semi-permanent shelf-price drops carry real SKUs that the team still
wants in NetSuite — they just aren't kit promos. Route them to the
**NLP Sheet** instead of `non_included`.

Marker phrases:
- `NLP`, `New Lower Price`
- `Special Buy`, `Special Pricing`
- `EDLP`, `Everyday Low Price`
- `Clearance`
- `Price Reduction`, `Price Drop`, `Price Cut`
- `Permanent Price Change`
- `(Get) X% Off` (with a digit), `Promote At X%`

For each NLP page:
1. Run the SAME header detection the kit path uses.
2. Pick the customer price using the vendor's `price_label_priority`.
3. Emit one `NLPRow` per SKU with:
   - `promo_name` = deal title + bracketed PCE if present
     (`"MX FUEL Power Supply Special Buy [PCE 262776]"`)
   - `sku` = the SKU
   - `promo_price` = matched price (or blank if not extractable)
   - dates from the page
   - `vendor` = detected vendor display name
   - `page` = 1-indexed page number
   - `price_label` = which column header matched (e.g. `Promo IMAP`)
   - `source_marker` = `nlp` if NLP_MARKER hit, else `special-buy`

### 8. Cover / TOC / dealer info / marketing → skip silently

Pages with no SKUs and no promo content (cover pages, table of
contents, dealer-info pages, brand-marketing pages, divider pages).
These count toward `Total Pages` in the audit but emit no rows
anywhere.

Don't try to force these into any category. Just count and move on.

### 8a. Unclassifiable / low-confidence → `for_review`

If a page cannot be confidently classified — ambiguous or unknown layout, two
or more conflicting markers with no priority winner, an unrecognized page type,
or a Crescent-style layout the operator did not confirm — record it in
`for_review` (Review Class `low-confidence`) with a reason and the parser's
best-guess Suggested Bucket. Emit **no** kit / NLP / Other-Promotions /
Non-Included rows for it. This sits ABOVE the kit fallthrough (#9) so an
ambiguous page is sent to human review rather than silently kitted, but BELOW
the deterministic markers (#1–#8) so confident classifications still win.

Missing-required-data rows (blank price/SKU on an otherwise-classified row) are
ALSO added to `for_review` (Review Class `missing-data`) in addition to their
normal routing (Non-Included `missing-price` / Makita `Needs-Pricing`).

### 9. Otherwise → **kit page**: emit Cartesian rows to `promo_rows`

This is the default case. The page is a B1G1 / B-X-G-Y / multi-paid-
bundle promo. Extract:

- **Promo title** (deal name from the page)
- **PCE / PCR / promo identifier** (append as `[PCE NNNNNN]` to
  promo_name)
- **Dates** (`Online Execution`, `Promo Execution`, `Advertised Sell
  Through`, `Advertising Window` — vendor-specific)
- **Paid SKUs** with prices (from `price_label_priority`)
- **Free SKUs** (marked `FREE` in price column, or under a `FREE GOOD`
  section banner)
- Emit **N paid × M free Cartesian rows** with one paid SKU in slot 1
  and one free SKU in slot 2 per row.

If `M == 0` (no free goods detected) the page is a multi-paid bundle
or pure paid-promo:
- For GearWrench bundles: one row, all SKUs in slots 1..N.
- For other vendors with no free goods: investigate further — most B1G1
  vendors hide free goods as image-only panels (see
  `edge-cases.md#image-only-free-goods`). Don't emit a single-member
  row if a free good is plausibly present but unread.

### 10. Per-SKU strikethrough inside an otherwise-active panel → `non_included` reason `strikethrough`

If only one or two SKUs in an otherwise-good panel are visually struck,
exclude just those SKUs (`non_included` reason `strikethrough`) and
continue parsing the page normally for the rest.

This is per-SKU not per-page — handled DURING extraction, not at the
classification step.

---

## Multiple markers on one page

Some pages legitimately hit multiple markers (e.g. "Buy More Save More
on Special Buy items"). Apply the **first match in priority order**
above. So a BMSM page that's also marked Special Buy is classified as
`buy-more-save-more` (priority #5 beats #7).

E-rebate precedence: an **e-rebate signal** (a `PCE = E-REBATE` value, or a
`REDEEM AT …/e-rebate` header) outranks the kit fallthrough (#9) **and** the 4a
"B1G1 table → kit" exception. When present, route to `Other-Promotions.csv`
(Promo Type `e-rebate`) regardless of any free-goods package or price table on
the page.

Exception: priority #7 (NLP routing) takes precedence over #6 (promo-code
Other-Promotions) only when the page has a clear price column and extractable
SKUs. If a page has BOTH "use code at checkout" AND a visible Special Buy price
column, prefer the NLP routing — the price data is valuable. When in doubt,
route to NLP.

---

## Empty / image-only pages

If a page extracts zero text and zero recognizable SKUs from the image,
treat as **cover/marketing** (case #8) — skip silently. Don't emit a
`non_included` row for blank pages.
