# Labels & HERO detection

Every plugin-generated Task gets a `labels` field with **exactly three**
labels. Plus HERO is auto-detected from row shape (no manual flagging).

## L1 — Year label

4-digit year as a single label: `2026`, `2027`, etc.

Source: parser CSV filename (`<Vendor>-Q<N>-<YYYY>-*.csv`) or the Task's
Start Date as fallback.

## L2 — Quarter label

Always universal `Q1` / `Q2` / `Q3` / `Q4` regardless of vendor.

Source: parser CSV filename quarter digit.

**Why universal Q-notation in labels but vendor-specific period in
titles?** Labels are for cross-vendor filtering (e.g. `labels = Q3 AND
labels = 2026` returns every Q3 2026 Task across all vendors). Titles
preserve the team's existing per-vendor display conventions. The two
fields serve different audiences.

## L3 — Promo type label

Exactly one of these values per Task (the promo-type label):

| Parser source → | Label |
|---|---|
| Promo-List.csv rows | `Kit-Promo` |
| RSA-Kits.csv rows | `Kit-Promo` (RSA flavor signaled by POS Redemption=Yes, not by label) |
| NLP-Sheet.csv rows (any `Source Marker`, including special-buy) | `NLP` |
| RSA-NLP.csv rows | `NLP` |
| Needs-Pricing.csv rows (out of scope) | `NLP` |
| Other-Promotions.csv, Promo Type `promo-code` | `Coupon` |
| Other-Promotions.csv, Promo Type `e-rebate` | `E-Rebate` |
| Other-Promotions.csv, Promo Type `buy-more-save-more` | `BMSM` |

Only one promo-type label per Task. No multi-type labels. (Parser v1.2.0 routes
coupon / e-rebate / BMSM promos through `Other-Promotions.csv`; before that they
were excluded, so `Coupon` / `E-Rebate` / `BMSM` were unreachable.)

## L4 — Auto-HERO detection

A Task is HERO when **any** of these triggers fire:

| Trigger | Detection logic |
|---|---|
| BMSM sale | The row comes from `Other-Promotions.csv` with Promo Type `buy-more-save-more` (parser v1.2.0). These now reach the plugin — emit the HERO (label `BMSM` + Priority Highest). |
| Kit promo with starter kit as free good | Promo-List row has a free SKU (slot price = 0.00) whose description or Promo Name contains `starter kit` (case-insensitive). |
| Kit promo with 2+ free goods | Promo-List row has **2 or more** slots filled where price = 0.00 (counting slots 2..6). Mix of bare tools / batteries / both — doesn't matter, the count alone triggers HERO. |

When ANY trigger fires:
- Set Priority field = `Highest` (Jira priority id `1`).
- Append ` (HERO)` to the Task summary (Rule N7).
- Labels stay unchanged — there is no `HERO` label.

## Promo Type field vs promo-type label (v0.3.0)

The **Promo Type custom field** consolidates `promo-code` / `buy-more-save-more` /
buy-X-get-Y to **`Manufacturer Coupon`** (see `field-mapping.md` → Shared field
derivations). The promo-type **label** does **not** consolidate — keep emitting the
per-type label (`Coupon` / `E-Rebate` / `BMSM`) per L3. Don't conflate the field with
the label. And **Buy In Promo is never an auto-default** — it's Think-Tank-only; an
all-paid kit is asked about, never auto-set.

## Implementation notes

- Labels in Jira are an array of strings on the `labels` system field.
  Set via the Atlassian MCP `createJiraIssue` or `editJiraIssue` tool
  with the `labels` field in the `additional_fields` (or `fields`)
  parameter.
- Labels are **case-sensitive** in Jira. Emit exactly `Kit-Promo`,
  `NLP`, `Coupon`, `E-Rebate`, `BMSM`, `Q1`/`Q2`/`Q3`/`Q4` with the casing
  shown.
- The `2026` (year) label is just a string — Jira doesn't validate it's
  a year, but keep the format consistent.

## Example label sets

| Task type | Labels |
|---|---|
| Milwaukee Q3 2026 NLP | `2026`, `Q3`, `NLP` |
| DeWalt Q3 2026 kit promo (Free Battery) | `2026`, `Q3`, `Kit-Promo` |
| Milwaukee Q3 2026 RSA kit | `2026`, `Q3`, `Kit-Promo` (POS Redemption=Yes signals RSA; not a separate label) |
| Makita Q3 2026 E-Rebate | `2026`, `Q3`, `E-Rebate` |
| Crescent Q3 2026 Coupon (Other-Promotions) | `2026`, `Q3`, `Coupon` |
| Milwaukee Q3 2026 BMSM (HERO) | `2026`, `Q3`, `BMSM` (Priority Highest) |
