# Field mapping — CSV row → Jira Task

Per-CSV field assignments. Custom field IDs differ between PAT and PROM
— see the remap table at the end.

---

## Shared field derivations (v0.3.0)

These fields follow the **same rules on every Task**, whatever the source CSV. The
per-CSV tables below defer to this section. Discover each field's option IDs at run
start via issue-type metadata (`getJiraIssueTypeMetaWithFields`); if a needed option
or field isn't found, **flag for the operator — never guess**.

**Promo Type** (`customfield_10778` PAT / `10474` PROM):
- Kit with a **free good** (any slot price `0.00`) → `Manufacturer Free Goods`.
- **NLP / special-buy** → `Manufacturer NLP`.
- **Coupon / BMSM / buy-X-get-Y** — Other-Promotions `promo-code` **or**
  `buy-more-save-more` — all consolidate to **`Manufacturer Coupon`**.
- **E-rebate** (Other-Promotions `e-rebate`) → `E-rebate`.
- **Self funding** → do **not** set this field (a coworker configures these); log it.
- **Buy In Promo is Think-Tank-only** (purchase-only, no online execution). Do **not**
  auto-default an all-paid deck kit to Buy In. If a kit has no free good and no
  online-execution dates, **ask**: `All-paid kit, no free good — Promo Type = Buy In
  Promo (Think Tank only) or leave unset? (Buy In / Unset)`.

**Online Execution** (`customfield_10775` PAT / `10739` PROM):
- `Yes` when the promo **has online-execution dates** (kit `Start`/`End`, or NLP /
  Other `Online Execution` dates present). `No` for RSA and Buy-In.
- **Online-only task gate:** if a promo is **not online-executable** — `Online Execution`
  resolves to `No` **and** there's no online advertising window (e.g. an Other-Promotions
  in-store-only / spend-threshold / volume deal) — **create no Task.** RSA is the deliberate
  exception: it's `No` but still tracked. See the Other-Promotions section + SKILL.md Step 6.

**Needs POS Redemption** (`customfield_10774` PAT / `10475` PROM):
- `Yes` if the promo is **RSA or carries a credit** (RSA-Kits `Item Credit N` /
  RSA-NLP `Credit Amount`), **OR** if the promo's **deck page image shows credit /
  mail-in / "redeem at" / vendor-redemption clues** — for **any vendor** (see
  `reference/deck-images.md`). Otherwise `No`. **This replaces the old Flex/EGO/SKIL
  vendor-name default — decide it from the deck, not the vendor name.**

**Promo Deck URL** (NEW field — discover `customfield_<id>` by **name** at run start;
flag if it isn't on the issue type):
- Set to the **vendor + quarter main deck** Google Drive link, found by searching the
  hub folder via the Drive connector (`reference/integrations.md`). Fallbacks:
  operator-paste → hub-folder link → leave blank + flag.

**Start / Due dates:** Start = the promo's start (`customfield_10015`); **Due
(`duedate`) = the last takedown day = the promo's End / Online Execution End.** ISO
`YYYY-MM-DD`.

---

## Promo-List.csv (kit promos)

Parser schema: 27 columns. `Promo Name`, `Start Date`, `End Date`,
then 6 × `(Item SKU N, Qty N, Price N, Credit N)` slots.

Group rows by `(Promo Name, Start Date, End Date)` → 1 Task per group.
Cartesian explosion (multiple paid × multiple free) collapses back into
one Task whose description holds the full SKU matrix.

| Jira field | Source |
|---|---|
| `summary` | Canonical title per `naming-rules.md` (Promo Name → derive a **generalized** Category from row shape → prepend `<YYYY> <Period> - ` per vendor → append the deck `[<ID>]` at the end per **N8**; **no vendor prefix, no SKUs**) |
| `customfield_<start-date>` | `Start Date` — convert `M/D/YYYY` to ISO `YYYY-MM-DD` |
| `duedate` | `End Date` — same conversion |
| `description` | Per `description-spec.md` (Date range header + SKU table + storefront links + NetSuite links + Promo Identifier + source CSV reference) |
| `labels` | per `labels.md` — Vendor + `Q<N>-<YYYY>` + promo-type label(s) (RSA promos also get `RSA`) |
| `priority` | **Not auto-set** — leave the Jira default. No HERO / no Priority bump (v0.3.0). |
| `assignee` | **Unassigned** |
| `parent` | Vendor Epic from `vendor-epics.md` |
| Promo Type custom field | Per **Shared field derivations**: free good present → `Manufacturer Free Goods`; all-paid kit → **ask** (never auto Buy In). |
| POS Redemption custom field | Per **Shared field derivations** (RSA/credit, or a deck-image redemption clue). |
| Online Execution custom field | Per **Shared field derivations** (`Yes` — kit has online dates). |

---

## NLP-Sheet.csv (single-SKU price drops)

Parser schema: 9 columns. `Promo Name`, `SKU`, `Promo Price`, `Online
Execution Start`, `Online Execution End`, `Vendor`, `Page`, `Price
Label`, `Source Marker`.

**v0.3.0 — NLPs no longer make one Task per Promo Name.** All **non-RSA** NLPs for
the vendor/quarter consolidate into **one parent Task** with a **sub-task per
`(start, takedown)` date group**, and each sub-task gets two generated CSVs
(start-pricing + revert schedule) attached — see `reference/nlp-consolidation.md`.
The field rows below apply to the parent Task.

| Jira field | Source |
|---|---|
| `summary` | `<YYYY> <Period> - NLPs` (or vendor-specific compound for SKIL) per `naming-rules.md` Rule N4 |
| Start date custom field | `Online Execution Start` |
| `duedate` | `Online Execution End` |
| `description` | Per `description-spec.md` — SKU table has one row per CSV row (SKU + Promo Price + Price Label) |
| `labels` | per `labels.md` — Vendor + `Q<N>-<YYYY>` + promo-type label(s) (RSA promos also get `RSA`) |
| `priority` | **Not auto-set** — leave the Jira default (v0.3.0). |
| `assignee` | **Unassigned** |
| `parent` | Vendor Epic from `vendor-epics.md` |
| Promo Type custom field | `Manufacturer NLP` (special-buy folds in) — per **Shared field derivations**. |
| POS Redemption custom field | Per **Shared field derivations** (RSA/credit, or a deck-image redemption clue). |
| Online Execution custom field | Per **Shared field derivations** (`Yes`). |

If `Promo Price` is blank, emit the SKU row anyway with `TBD` in the
description table and a "Needs manual pricing" line below the table.

---

## RSA-Kits.csv

Same 27-column schema as Promo-List.csv. `Promo Name` ends with `-RSA`
suffix; `Item Credit N` columns carry the per-unit dollar credit the
sales rep earns.

**Manual review per row** before Task creation (per SKILL.md Step 6).
Skip rows declined.

| Jira field | Source (overrides vs Promo-List) |
|---|---|
| `summary` | Same as Promo-List but **strip the `-RSA` suffix from Promo Name** before canonicalizing. The RSA nature is signaled by POS Redemption=Yes + RSA credit table in description. |
| Promo Type custom field | `Manufacturer Free Goods` |
| **POS Redemption** | **`Yes`** — RSAs always POS redemption |
| **Online Execution** | **`No`** — RSAs are sales-rep-facing, not online |
| `labels` | per `labels.md` — Vendor + `Q<N>-<YYYY>` + promo-type label(s) (RSA promos also get `RSA`) |
| Description | Include a dedicated "RSA Credit" section showing per-SKU credit amounts in addition to the standard SKU table |

---

## RSA-NLP.csv

Same 10-column schema as NLP-Sheet.csv plus `Credit Amount` column at
the end.

**Manual review per row** before Task creation.

| Jira field | Source (overrides vs NLP-Sheet) |
|---|---|
| `summary` | Same as NLP-Sheet but strip `-RSA` suffix from Promo Name |
| Promo Type custom field | `Manufacturer NLP` |
| **POS Redemption** | **`Yes`** |
| **Online Execution** | **`No`** |
| `labels` | per `labels.md` — Vendor + `Q<N>-<YYYY>` + promo-type label(s) (RSA promos also get `RSA`) |
| Description SKU table | Include `Credit Amount` column per SKU |

---

## Other-Promotions.csv (BMSM / e-rebate / promo-code) — v0.2.0

Parser schema: 16 columns (`pcs-promo-parser` `output-csvs.md#other-promotionscsv`).
Key columns: `Promo Type`, `Promo Name`, `SKU`, `Tier`, `Discount`,
`Rebate Amount`, `Redemption URL`, `Promo Code`, `Price`, `Qty`, `Start Date`,
`End Date`, `Vendor`, `Page`, `Source Marker`, `Detail`.

Group rows by `(Promo Name, Promo Type, Start Date, End Date)` → 1 Task per
group; all SKUs roll into the description table. **Manual review per group**
before creation (SKILL.md Step 6) — these promo families are new, so confirm each.

**Online-only gate (skip non-online groups):** before reviewing a group, resolve its Online
Execution. If it's **not online-executable** — `No` with **no online window** (an in-store-only
deal, or a spend-threshold / volume program with no online advertising window, e.g. DeWalt
`PMAPP = IN-STORE ONLY`) — **auto-skip it: create no Task, log it in the audit summary.** These
should already arrive in `Non-Included.csv` from the parser (reason `brick-and-mortar` /
`spend-to-earn`); the gate here is the backstop. Only genuinely online BMSM / e-rebate /
promo-code groups proceed to the Y/N review.

| Jira field | Source |
|---|---|
| `summary` | Per `naming-rules.md`: `e-rebate` → N1 template, Category `E-Rebate`; `buy-more-save-more` → N1 template, Category `BMSM`; `promo-code` → the **N2** coupon format `<Vendor> <YYYY> Coupon Code - <CODE>` (`<CODE>` = `Promo Code`). Keep the deck `[<ID>]` at the end per **N8** (omit on consolidated / multi-ID groups). |
| Start date custom field | `Start Date` → ISO `YYYY-MM-DD` |
| `duedate` | `End Date` → ISO |
| `description` | Per `description-spec.md` Other-Promotions block (type line + SKU table + Redemption URL / Promo Code / Tier+Discount as applicable + Promo Identifier + source CSV) |
| `labels` | per `labels.md` — Vendor + `Q<N>-<YYYY>` + promo-type label(s): `Coupon` for promo-code; `Coupon`+`BMSM` for buy-more-save-more; `E-Rebate` for e-rebate |
| `priority` | **Not auto-set** — leave the Jira default. No HERO / no Priority bump (v0.3.0). |
| `assignee` | **Unassigned** |
| `parent` | `promo-code` → the **Coupon-code promos** Epic; `e-rebate` / `buy-more-save-more` → the **vendor** Epic (`vendor-epics.md`) |
| Promo Type custom field | Per **Shared field derivations**: `promo-code` **and** `buy-more-save-more` → `Manufacturer Coupon`; `e-rebate` → `E-rebate`. (Discover option IDs at run start; flag if missing.) |
| POS Redemption custom field | Per **Shared field derivations** — normally `No`, but `Yes` if the deck page shows mail-in / redeem-at / credit clues. |
| Online Execution custom field | Per **Shared field derivations** (`Yes`). |

Type-specific description detail: **e-rebate** → show `Rebate Amount` +
`Redemption URL`; **promo-code** → show the `Promo Code` + `Discount`; **BMSM** →
show the `Tier` ladder + `Discount`. Never put a FLEX `SOT…` value in a code
field — the parser already keeps it out of `Promo Code`.

---

## Out of scope (no Task creation)

| File | Behavior |
|---|---|
| `Needs-Pricing.csv` (Makita) | Skip entirely. Nathan handles manual pricing downstream. |
| `Non-Included.csv` | Per-reason rules — see `non-included.md`. Most reasons auto-skip; a few prompt for manual review. |
| `For-Review.xlsx` | **Never a Jira input** — operator-review workbook only. |
| `Parser-Audit.csv` | Read for context (vendor / quarter / page counts; also the row-count manifest, since empty outputs aren't written) but no Jira write. Surface in end-of-run console summary. |

---

## Promo Identifier (in the title + a description line, until a custom field exists)

The parser emits `Promo Name` ending in `[PCE NNNNNN]` or `[PCR NNNNNN]`.
As of v0.4.0 (Rule N8):

1. **Keep** the identifier in the Task **title**, at the end, bracketed with a colon:
   `… [PCR: P-00208522]` / `… [PCE: 262776]`. Omit on no-ID pages and on consolidated /
   multi-ID Tasks.
2. **Also** add a belt-and-suspenders line to the description:
   ```
   **Promo Identifier:** PCE NNNNNN
   ```

When the PCS team adds a dedicated `Promo Identifier` custom field to
the Task issue type (tracked in their internal admin checklist), bump
this skill's version to populate that field directly and drop the
description line (the title bracket stays).

---

## Sub-tasks

Two cases create sub-tasks:
- **Kit / Other multi-window:** one Promo Name spanning multiple non-contiguous date
  windows in the same CSV → a sub-task per window. Single-window Tasks have none.
- **NLP consolidation (v0.3.0):** the single NLP parent Task per vendor/quarter gets a
  sub-task per `(start, takedown)` date group, each with two attached CSVs — see
  `reference/nlp-consolidation.md`.

Sub-task summary: literal `MM/DD-MM/DD` (Rule N9). The parent Task gets the overall
(earliest start, latest takedown) window.

---

## PAT vs PROM — fields are NOT identical; discover at runtime

**PAT is a sandbox. Its custom-field set, option *labels*, and option *IDs* do NOT match
PROM.** Never assume a field exists, and never assume an option is labeled `Yes`. At run
start, call `getJiraIssueTypeMetaWithFields` for the **target** project, enumerate which of
these fields actually exist, and cache the **option IDs by label**. If a field or option is
missing, **skip it and log — do not fail, do not guess.**

Known PAT quirks (observed this run):
- **POS Redemption / Online Execution on PAT are single-option multi-checkbox fields whose one
  option is literally labeled `"Option 1"`** (it *is* the affirmative — there is no `Yes`).
  Select that option's **ID**; never send the string `Yes`.
- **`Promo Deck URL` does not exist on the PAT Task type** → silently skip + flag (don't error).

Field-key hints (PROM is the source of truth; **PAT keys/IDs below are hints, not guarantees —
discover at runtime**):

| Field name | PAT key | PROM key |
|---|---|---|
| Promo Type | `customfield_10778` | `customfield_10474` |
| Needs POS Redemption | `customfield_10774` | `customfield_10475` |
| Online Execution | `customfield_10775` | `customfield_10739` |
| Categorized | `customfield_10773` | `customfield_10740` |
| Promo Launched | `customfield_10776` | `customfield_10472` |
| Promo Taken Down | `customfield_10777` | `customfield_10473` |
| Site Graphics Assigned | `customfield_10779` | `customfield_10476` |
| Start date | `customfield_10015` (same in both) | `customfield_10015` |
| Promo Deck URL | discover by **name** (absent on PAT) | discover by **name** at run start |

The allowed-value **option IDs also differ between projects** — when setting a select /
multi-checkbox field, query the project's issue-type field metadata once at run start and
cache the option IDs **by label**.

---

## Empty / unknown row handling

- If a Promo-List group has only 1 paid slot and no free slot: probably
  a multi-paid bundle. Title `<Category>` = `Bundles`. Single row in
  description SKU table.
- If a Promo-List group has zero paid slots: malformed parser output.
  Log + skip; show in console summary.
- If a row's `Promo Name` is blank: log + skip with a clear reason in
  the audit log; show in console summary.
- If derived `<Category>` doesn't match the controlled vocabulary in
  `naming-rules.md` Rule N5: **prompt the user** for the right token
  rather than guessing.
