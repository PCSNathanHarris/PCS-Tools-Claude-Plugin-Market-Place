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

### 5. Buy-More-Save-More / volume-tiered → `non_included` reason `buy-more-save-more`

Pages that say "Buy 5 save 10%" or "Buy More Save More" or "BMSM" or
"Volume Discount". Tiered pricing, not a fixed kit.

### 6. Promo-code / coupon / checkout-code only → `non_included` reason `promo-code-only`

Pages whose entire deal is "Use code XYZ at checkout for $50 off."
There's no free good — the page IS the discount mechanism.

**TRAP**: FLEX uses `PROMO CODE: SOT2514219` as a deal **identifier**,
not a discount code. That pattern alone does NOT mean
`promo-code-only`. See `exclusion-markers.md` for the carve-out.

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

Exception: priority #7 (NLP routing) takes precedence over #6
(`promo-code-only`) only when the page has a clear price column and
extractable SKUs. If a page has BOTH "use code at checkout" AND a
visible Special Buy price column, prefer the NLP routing — the price
data is valuable. When in doubt, route to NLP.

---

## Empty / image-only pages

If a page extracts zero text and zero recognizable SKUs from the image,
treat as **cover/marketing** (case #8) — skip silently. Don't emit a
`non_included` row for blank pages.
