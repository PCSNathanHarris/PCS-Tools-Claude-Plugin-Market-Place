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

Exactly one of these four values per Task:

| Parser source → | Label |
|---|---|
| Promo-List.csv rows | `Kit-Promo` |
| RSA-Kits.csv rows | `Kit-Promo` (RSA flavor signaled by POS Redemption=Yes, not by label) |
| NLP-Sheet.csv rows (any `Source Marker`, including special-buy) | `NLP` |
| RSA-NLP.csv rows | `NLP` |
| Needs-Pricing.csv rows (out of scope v0.1.0) | `NLP` |
| Coupon-code promos (out of scope v0.1.0) | `Coupon` |
| E-Rebate promos (deck-flagged) | `E-Rebate` |

Only one promo-type label per Task. No multi-type labels.

## L4 — Auto-HERO detection

A Task is HERO when **any** of these triggers fire:

| Trigger | Detection logic |
|---|---|
| BMSM sale | Deck page is BMSM. **Gap:** parser currently excludes BMSM as `non_included` reason `buy-more-save-more` — they don't reach Promo-List/NLP-Sheet. BMSM HEROs need a parser-side change before v0.1.0 can catch them. Document, don't emit. |
| Kit promo with starter kit as free good | Promo-List row has a free SKU (slot price = 0.00) whose description or Promo Name contains `starter kit` (case-insensitive). |
| Kit promo with 2+ free goods | Promo-List row has **2 or more** slots filled where price = 0.00 (counting slots 2..6). Mix of bare tools / batteries / both — doesn't matter, the count alone triggers HERO. |

When ANY trigger fires:
- Set Priority field = `Highest` (Jira priority id `1`).
- Append ` (HERO)` to the Task summary (Rule N7).
- Labels stay unchanged — there is no `HERO` label.

## Implementation notes

- Labels in Jira are an array of strings on the `labels` system field.
  Set via the Atlassian MCP `createJiraIssue` or `editJiraIssue` tool
  with the `labels` field in the `additional_fields` (or `fields`)
  parameter.
- Labels are **case-sensitive** in Jira. Emit exactly `Kit-Promo`,
  `NLP`, `Coupon`, `E-Rebate`, `Q1`/`Q2`/`Q3`/`Q4` with the casing
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
| Crescent Q3 2026 Coupon (v0.1.0 manual) | `2026`, `Q3`, `Coupon` |
