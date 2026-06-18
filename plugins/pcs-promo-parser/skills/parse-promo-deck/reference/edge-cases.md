# Edge cases

These are real-world page layouts the rule parser struggled with.
Documenting them here so the AI-driven skill handles them correctly
from day one.

---

## B1G1 / single-member-with-hidden-free-good

**The trap**: a page shows a single paid SKU at the top (e.g.
"Buy a Milwaukee MX Fuel Kit Get One Free") with a clear price, but
the free SKU is rendered ONLY as an image panel at the bottom-right
with the free SKU number printed underneath in small type. The text
extractor often misses it entirely.

**Resolution**:
- If the promo TITLE contains B1G1 language (`Get`, `Free`, `with
  purchase`, `bundled`, B1G1, B2G1, etc.) AND you only extracted one
  paid SKU, **assume a free good exists** and scan the page image
  carefully for:
  - Small SKU labels under product images
  - "FREE" tags in image panels
  - Strikethrough on a price (indicates "now free")
- If you find the free SKU, emit the Cartesian row pair.
- If you genuinely cannot find it after a careful look, emit the paid
  SKU as a single-member row AND add a `non_included` entry with reason
  `image-only-free-good`, SKU blank, Detail "B1G1 title with no visible
  free SKU".

This is critical for Milwaukee MX Fuel pages and DeWalt B1G1 promos.

---

## Multi-pick free goods ("Get N" / "Choice of N")

Some promos pair a single anchor (a starter kit or qualifying tool) with
a **customer's choice of N free goods** from a pool of M options. The
deal price covers the anchor PLUS the N picked free goods together.

**Real-world example — DeWalt P-00209847**:
> "20V MAX Bare Tool Bundle — Buy DCB205-2C Get 2 Bare Tools" @ $299

Anchor = `DCB205-2C` (battery starter kit). Free-good pool = 13 bare
tools. Customer picks **any 2** of the 13 — and may pick **two of the same**
tool. The correct emit is **every multiset** of 2 picks from the 13
(combinations **with repetition**), paired with the anchor —
`C(13+2-1, 2) = C(14, 2) = 91` rows (78 distinct pairs + 13 same-tool doubles),
each with **three** SKU slots filled (anchor + pick_A + pick_B; a double simply
repeats the SKU).

**The trap (two ways to get it wrong)**: (1) misreading it as a standard
Cartesian (1 paid × 13 free = 13 two-slot rows) undercounts every multi-tool
combination; (2) emitting only the *distinct* pairs (`C(13,2)=78`) drops the
"two of the same free good" options the customer is actually entitled to.

### Title-pattern detection (case-insensitive)

Capture N from any of these patterns:

- `\bGet\s+(\d+)\b` — "Get 2 Bare Tools", "Get 3 Free"
- `\bChoice\s+of\s+(\d+)\b` — "Choice of 2"
- `\bChoose\s+(\d+)\b` — "Choose 3 Tools"
- `\b(\d+)\s+of\s+the\s+following\b` — "2 of the following"
- `\bany\s+(\d+)\b\s+(?:of|free|bare)` — "any 2 free tools"

If N is captured and N ≥ 2 and the free-good pool has M ≥ 1 items,
switch from Cartesian to **combinations with repetition (multisets)** — see
"Duplicates" below.

### Duplicates (allowed by default)

A choose-N free-good promo lets the customer take N of the **same** free good
(e.g. two of `48-11-1850`), so emit **multisets** by default:
`C(M+N-1, N)` rows, which include the N-of-the-same rows. `ANY MIX` / `any
combination` wording confirms this. Suppress duplicates (fall back to strict
`C(M, N)`, no repeats) **only** when the deck explicitly says the picks must
differ — e.g. "2 **different** tools", "no duplicates", "one of each".

### Row layout

- Slot 1 = paid anchor SKU (qty 1, price = deal price, credit blank).
- Slots 2..(N+1) = the N picks, **sorted lexicographically** by SKU within each
  row (stable diffs across re-parses). Each gets qty 1, price `0.00`, credit
  blank. For a **double** (same free good picked twice), the SKU simply occupies
  two of these slots — the downstream importer's qty-collapse merges them to
  qty 2.
- Total slots filled = `1 + N`. Remaining slots emit 4 empty cells each.

### Worked example — P-00209847 (anchor + Choose 2 of 13 free tools)

13 tools: `DCD806B, DCF630B, DCF860B, DCF911B, DCG408B, DCH133B,
DCS334B, DCS356B, DCS382B, DCS438B, DCS565B, DCW210B, DCW600B`.

Emit `C(14, 2) = 91` rows — 78 distinct pairs **plus 13 same-tool doubles**
(the customer may take two of one tool). First row (alphabetically-sorted pair):

```csv
20V MAX Bare Tool Bundle Buy DCB205-2C Get 2 Bare Tools [P-00209847],5/3/2026,8/3/2026,DCB205-2C,1,299.00,,DCD806B,1,0.00,,DCF630B,1,0.00,,,,,,,,,,,,,
```

A same-tool double (two of `DCD806B`):

```csv
20V MAX Bare Tool Bundle Buy DCB205-2C Get 2 Bare Tools [P-00209847],5/3/2026,8/3/2026,DCB205-2C,1,299.00,,DCD806B,1,0.00,,DCD806B,1,0.00,,,,,,,,,,,,,
```

Last row:

```csv
20V MAX Bare Tool Bundle Buy DCB205-2C Get 2 Bare Tools [P-00209847],5/3/2026,8/3/2026,DCB205-2C,1,299.00,,DCS565B,1,0.00,,DCW600B,1,0.00,,,,,,,,,,,,,
```

Each row is a distinct multiset — 78 mixed pairs + 13 same-tool doubles. The
anchor SKU and its price are constant across all 91 rows.

### N = 1 case

If N = 1 (e.g. "Get 1 Free Tool" / standard B1G1), behavior is **unchanged**:
fall back to the regular 1×M Cartesian rule (M two-slot rows). The
combinations path only activates for N ≥ 2.

### Multiple anchors with "Choose N"

If the deck shows multiple anchors AND a "Choose N" pool, treat as
nested: for each anchor, emit the multiset rows `C(M+N-1, N)`. Total rows =
`(anchor count) × C(M+N-1, N)`. Anchor SKU goes in slot 1 of each row.

---

## Split slides — qualifying groups with per-group free goods

**The trap**: one slide offers TWO (or more) free goods, and the qualifying
items are partitioned into groups where **each group earns only one specific
free good** — not a free choice of either. A full Cartesian across the whole
slide is WRONG: it pairs every qualifying tool with every free good.

This is common on Milwaukee battery slides. Example (PCE 263131, "BUY A SELECT
M12 TOOL GET (1) M12 BATTERY FREE"): a **bold black divider line** splits the
qualifying tools into a top group and a bottom group; the free goods `$79 →
48-11-2425` and `$129 → 48-11-2450` sit stacked on the right, one aligned to
each group. Correct: **top tools pair only with 48-11-2425; bottom tools pair
only with 48-11-2450.** Cross-pairing (every tool × both batteries) is the bug.

### How to detect a split

A slide is split when BOTH hold:
1. There are **2+ free goods**, AND
2. The qualifying area is **partitioned** — by a bold/black divider line, a
   clear whitespace band, or separate sub-tables/panels — with each partition
   visually aligned to one of the free goods (same side / row / column).

A divider that's "just a thin bold line" still counts — look at the image, not
only the text layer.

### How to pair

Map each qualifying group to its free good(s), using this authority order:
1. An on-slide **table that associates items with their free good** (some slides
   print a "free goods associated" table beneath the grid) — authoritative.
2. **Spatial alignment** — which free good sits on the same side/row as the
   group across the divider.
3. Per-group free-good **labels / $-values / titles** printed beside the group.

Then emit rows **per group** — apply the normal Cartesian (or choose-N multiset)
rule **within** each group against ITS free good(s) only. Never cross-pair
across the divider. All groups share the same `promo_name` (same PCE) — the
split only controls which (paid, free) pairs are emitted.

### When the mapping is ambiguous

If you detect a divider/multiple free goods but **cannot confidently** decide
which group earns which free good (no table, unclear alignment), **stop and ask
the operator** to confirm the group→free-good mapping before emitting. Do not
guess, and do not silently fall back to a full Cartesian.

If the operator does not confirm, **skip those pairs** and add a `for_review`
row (Review Class `low-confidence`, reason `split-mapping-unconfirmed`,
Suggested Bucket `kit`) so the slide is surfaced for human review rather than
guessed at. See `output-csvs.md#for-reviewxlsx`.

---

## Multi-paid bundle (no free goods)

GearWrench socket-set bundles, some Bosch / Makita combo kits, etc.
Several SKUs sold together at one bundle price; no separate free good.

**Resolution**: emit ONE row with all SKUs in slots 1..N. The
Bundle Retail / total price goes in `Item Price 1`; the other slots'
Price/Credit columns are blank.

Do NOT do Cartesian here — these aren't paired deals.

---

## Image-only free SKUs (DeWalt)

DeWalt 20V MAX + FLEXVOLT promos sometimes show the free good ONLY as
a labeled product image in a separate panel from the qualifying tools.
The price table lists only the paid SKUs; the free SKU has no row.

**Resolution**: look in the image for a `FREE` callout next to a
product picture, and read the SKU printed under or beside the picture.
Add it to the Cartesian emit.

If you really can't extract the SKU, surface it as
`non_included` reason `image-only-free-good` so the user knows there's
a gap.

---

## Side-by-side tables (Makita Q4)

Makita Q4 / year-end decks sometimes lay out two parallel tables
side-by-side:

```
SKU  Description  M1  MAP   | SKU  Description  M1  MAP
1234 ...          10  299   | 5678 ...          12  399
```

The rule parser's right-align fallback gives the RIGHT SKU correct
prices but the LEFT loses them. Side-by-side detection is hard.

**Resolution**: when you see two header rows side-by-side, parse them
as TWO independent column groups. Each row in the data area has two
SKU+price tuples — emit them as two separate paid SKUs in the same
promo group (or two separate promos if the headers indicate distinct
deal titles).

---

## Multi-promo per page

A single page may stack two distinct promos (each with its own header,
qualifying items, and free goods) vertically. Common on Bosch and
Milwaukee.

**Resolution**: parse each promo block independently. Each becomes its
own group of Cartesian rows in `promo_list.csv` with a distinct
`promo_name`. Same page number applies to both groups.

If both promos share a single PCE code, append the same `[PCE NNNNNN]`
to each promo_name and let the deal title differ.

---

## Section banners that look like table headers

Milwaukee in particular uses big-text banners like:

```
QUALIFYING ITEMS              FREE GOOD
```

These look like a header row but contain NO price-bearing column label.
**Do not treat them as headers.** A real header line has at least one
of the vendor's `price_label_priority` tokens (IMAP, MAP, MSRP, etc.)
AND at least two total signature hits.

A common Milwaukee pattern:

```
QUALIFYING ITEMS                       FREE GOOD                    <-- banner, NOT header
Item #  Description  IMAP  Promo IMAP  Item #  Description          <-- real header
2962-22 ...          499.00 399.00     48-11-1850 ...               <-- data
```

Read past the banner and find the real header line.

---

## Multi-line headers

Some vendors split column titles across two lines:

```
HEAVY DUTY    PROMO     PROMO
PRICE         PRICE     IMAP
DCF891B       299.00    279.00
```

**Resolution**: when consecutive lines both look like header tokens
(no SKU at line start, contains words from `header_signatures`), merge
them as one logical header before extraction.

---

## DeWalt whitespace-broken price tokens

DeWalt 2023 Q4 PDFs sometimes emit prices with internal spaces:
`$ 1 33.00` for `$133.00`, or `$ 99.00` for `$99.00`.

**Resolution**: when matching prices, tolerate spaces inside the
numeric portion — strip whitespace before parsing the float.

---

## "Recommended Accessory" / "Sold Separately" lines

Common on Makita pages. These lines list related products that the
customer can BUY along with the deal — they are NOT free with the deal.

**Resolution**: exclude SKUs on lines that contain `Recommended
Accessory` or `Sold Separately` (case-insensitive). Don't emit them.

---

## PCE / PCR / promo identifier handling

When a vendor prints a promo identifier on the page, include the full
identifier in `promo_name` wrapped in square brackets:

- Milwaukee: `PCE` followed by 6 digits → `[PCE 252601]`
- DeWalt: `PCR` followed by 6–9 digits OR `P-` followed by 6–9 digits
  → `[PCR 123456]` or `[P-00209433]`
- Bosch / Makita / EGO / Flex / GearWrench / Crescent: usually no
  reliable per-page identifier; fall back to the deal title for
  `promo_name`.

Use the **full prefix-with-number** form (`PCE 262776`, not just
`262776`). If no identifier is visible, omit the brackets entirely —
do NOT invent a code.

The PCE/PCR is appended at the END of the deal title:
✅ `"Buy an Mx Fuel Kit Get One Free [PCE 252601]"`
❌ `"[PCE 252601] Buy an Mx Fuel Kit Get One Free"`

This same convention applies to **NLP Sheet** rows — the `Promo Name`
column there carries the deal title + PCE for NLP / Special Buy pages
too.

---

## Buy-In vs Online Execution dates

Vendor decks often show TWO date ranges:
- **Buy-In Window** (e.g. "Buy In: 4/1/2026 - 5/3/2026") — internal
  dealer purchase period. NEVER use this.
- **Online Execution** (or `Promo Execution`, `Advertised Sell Through`,
  `Advertising Window`) — customer-facing promo period. **Use this.**

If both are on the page, identify the customer-facing one by the label
keyword and pick that. If you can't tell, default to the LATER /
LONGER range — that's almost always the customer window.

---

## Written-month date ranges (Bosch)

Bosch and some Crescent flyers use prose dates:

- `August 1 - October 31, 2025`
- `Aug 1 – Oct 31, 2025`
- `January 15, 2026 to March 31, 2026`

When only the second month carries a year, use it for both. Convert to
non-padded `M/D/YYYY`: `August 1 - October 31, 2025` → `8/1/2025` and
`10/31/2025`.

---

## Empty / image-only pages

If a page has zero extractable text AND no recognizable SKU pattern in
the image, classify as **cover/marketing** — skip silently. Don't emit
to any of the three row lists. Count toward `Total Pages` in audit
only.

---

## Multi-image SKU panels (Milwaukee MX Fuel)

MX Fuel battery / charger / accessory promos sometimes show 3–5
qualifying tools in a row of image panels, with the SKU printed
underneath each. The price table at the bottom may only list ONE row
because all paid options share the same Promo IMAP price.

**Resolution**: extract all the SKUs from the image panels as
QUALIFYING SKUs, all at the same price. Then Cartesian against any
free goods. So 4 paid × 1 free = 4 rows.
