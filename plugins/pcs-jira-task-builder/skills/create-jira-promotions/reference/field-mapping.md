# Field mapping — CSV row → Jira Task

Per-CSV field assignments. Custom field IDs differ between PAT and PROM
— see the remap table at the end.

---

## Promo-List.csv (kit promos)

Parser schema: 27 columns. `Promo Name`, `Start Date`, `End Date`,
then 6 × `(Item SKU N, Qty N, Price N, Credit N)` slots.

Group rows by `(Promo Name, Start Date, End Date)` → 1 Task per group.
Cartesian explosion (multiple paid × multiple free) collapses back into
one Task whose description holds the full SKU matrix.

| Jira field | Source |
|---|---|
| `summary` | Canonical title per `naming-rules.md` (Promo Name → strip `[PCE…]` → derive Category from row shape → prepend `<YYYY> <Period> - ` per vendor) |
| `customfield_<start-date>` | `Start Date` — convert `M/D/YYYY` to ISO `YYYY-MM-DD` |
| `duedate` | `End Date` — same conversion |
| `description` | Per `description-spec.md` (Date range header + SKU table + storefront links + NetSuite links + Promo Identifier + source CSV reference) |
| `labels` | `[<year>, Q<N>, Kit-Promo]` |
| `priority` | `Highest` (id 1) if HERO triggers per `labels.md` Rule L4; default `Medium` (id 3) otherwise |
| `assignee` | **Unassigned** |
| `parent` | Vendor Epic from `vendor-epics.md` |
| Promo Type custom field | Derive: free SKU(s) present → `Manufacturer Free Goods`; all paid → `Buy In Promo (No customer facing execution)` |
| POS Redemption custom field | `Yes` if vendor is Flex/EGO/SKIL (per PCS Q1/Q2 default); `No` otherwise |
| Online Execution custom field | `Yes` |

---

## NLP-Sheet.csv (single-SKU price drops)

Parser schema: 9 columns. `Promo Name`, `SKU`, `Promo Price`, `Online
Execution Start`, `Online Execution End`, `Vendor`, `Page`, `Price
Label`, `Source Marker`.

Group rows by `Promo Name` → 1 Task per group. All SKUs roll into the
description table.

| Jira field | Source |
|---|---|
| `summary` | `<YYYY> <Period> - NLPs` (or vendor-specific compound for SKIL) per `naming-rules.md` Rule N4 |
| Start date custom field | `Online Execution Start` |
| `duedate` | `Online Execution End` |
| `description` | Per `description-spec.md` — SKU table has one row per CSV row (SKU + Promo Price + Price Label) |
| `labels` | `[<year>, Q<N>, NLP]` |
| `priority` | `Medium` (HERO triggers don't fire for NLPs in v0.1.0) |
| `assignee` | **Unassigned** |
| `parent` | Vendor Epic from `vendor-epics.md` |
| Promo Type custom field | `Manufacturer NLP` (special-buy folds in — same value) |
| POS Redemption custom field | `Yes` if vendor is Flex/EGO/SKIL; `No` otherwise |
| Online Execution custom field | `Yes` |

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
| `labels` | `[<year>, Q<N>, Kit-Promo]` — still Kit-Promo |
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
| `labels` | `[<year>, Q<N>, NLP]` |
| Description SKU table | Include `Credit Amount` column per SKU |

---

## Out of scope for v0.1.0

| File | Behavior |
|---|---|
| `Needs-Pricing.csv` (Makita) | Skip entirely. Nathan handles manual pricing downstream. |
| `Non-Included.csv` | Per-reason rules — see `non-included.md`. Most reasons auto-skip; a few prompt for manual review. |
| `Parser-Audit.csv` | Read for context (vendor / quarter / page counts) but no Jira write. Surface in end-of-run console summary. |

---

## Promo Identifier (temp home until custom field exists)

The parser emits `Promo Name` ending in `[PCE NNNNNN]` or `[PCR NNNNNN]`.
For v0.1.0:

1. Strip the bracketed identifier from the Task **title**.
2. Add a line to the description:
   ```
   **Promo Identifier:** PCE NNNNNN
   ```

When the PCS team adds a dedicated `Promo Identifier` custom field to
the Task issue type (tracked in their internal admin checklist), bump
this skill's version to populate that field directly and remove the
description line.

---

## Sub-tasks

Plugin creates sub-tasks **only** when a single Promo Name spans
multiple non-contiguous date windows in the same CSV.

Sub-task summary: literal `MM/DD-MM/DD` (Rule N9). Parent Task gets the
overall (earliest start, latest end) window.

Single-date-window Tasks have no sub-tasks.

---

## PAT vs PROM custom field IDs

Custom field keys differ between the two projects. After resolving the
project target in Step 1 of SKILL.md, look up the right key:

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

The allowed-value option IDs also differ between projects — when setting
a select / multi-checkbox field, query the project's issue-type field
metadata once at run start and cache the option IDs.

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
