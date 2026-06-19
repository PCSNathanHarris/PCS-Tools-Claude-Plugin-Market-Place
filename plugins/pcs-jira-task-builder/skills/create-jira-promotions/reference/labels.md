# Labels

Every plugin-generated Task gets a `labels` field with **exactly three labels —
Vendor, Quarter, and Promo Type** (v0.3.0). **There is no HERO auto-detection and no
Priority auto-bump** — the plugin never marks a Task HERO and never sets Priority.

## L1 — Vendor label

The vendor display name as a single label: `Milwaukee`, `DeWalt`, `Makita`, `Bosch`,
`EGO`, `Flex`, `GearWrench`, `Crescent`. (Sub-brands inherit their parent — Stiletto /
Empire → `Milwaukee`.)

Source: parser CSV filename (`<Vendor>-Q<N>-<YYYY>-*.csv`).

## L2 — Quarter label

Always universal `Q1` / `Q2` / `Q3` / `Q4`, regardless of the vendor period token used
in the title. Enables cross-vendor filtering (e.g. `labels = Q3`).

Source: parser CSV filename quarter digit.

## L3 — Promo Type label

The Task's **Promo Type** (per `field-mapping.md` → Shared field derivations) as a
single **hyphenated** label — Jira labels cannot contain spaces:

| Promo Type field value | Label |
|---|---|
| `Manufacturer Free Goods` | `Manufacturer-Free-Goods` |
| `Manufacturer NLP` | `Manufacturer-NLP` |
| `Manufacturer Coupon` | `Manufacturer-Coupon` |
| `E-rebate` | `E-rebate` |
| `Buy In Promo` (Think-Tank only) | `Buy-In-Promo` |

The label always mirrors whatever Promo Type was set. If Promo Type is left unset
(self-funding — a coworker configures those), omit the third label and note it in the
run summary.

## Implementation notes

- Labels are an array of strings on the `labels` system field — set via the Atlassian
  MCP `createJiraIssue` / `editJiraIssue` `fields` parameter.
- Labels are **case-sensitive** and **cannot contain spaces** — emit exactly the Vendor
  display name, `Q1`–`Q4`, and the hyphenated Promo Type, with the casing shown.

## Example label sets

| Task | Labels |
|---|---|
| Milwaukee Q3 2026 NLP | `Milwaukee`, `Q3`, `Manufacturer-NLP` |
| DeWalt Q3 2026 kit (free battery) | `DeWalt`, `Q3`, `Manufacturer-Free-Goods` |
| Milwaukee Q3 2026 RSA kit | `Milwaukee`, `Q3`, `Manufacturer-Free-Goods` (RSA signaled by POS Redemption=Yes) |
| Makita Q3 2026 e-rebate | `Makita`, `Q3`, `E-rebate` |
| Crescent Q3 2026 coupon | `Crescent`, `Q3`, `Manufacturer-Coupon` |
| Milwaukee Q3 2026 BMSM | `Milwaukee`, `Q3`, `Manufacturer-Coupon` |
