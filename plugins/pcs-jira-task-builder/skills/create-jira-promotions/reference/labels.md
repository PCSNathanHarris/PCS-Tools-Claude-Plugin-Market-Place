# Labels

Every plugin-generated Task gets a `labels` field = **Vendor**, **Quarter-Year**, and
**one or more promo-type labels** (plus `RSA` when applicable). **No HERO auto-detection
and no Priority bump** — the plugin never marks a Task HERO and never sets Priority.

These promo-type labels are **independent of the Promo Type custom field**
(`field-mapping.md` → the field is `Manufacturer Free Goods` / `Manufacturer NLP` /
`Manufacturer Coupon` / `E-rebate`). The labels here are the short tokens.

## L1 — Vendor label

The vendor display name: `Milwaukee`, `DeWalt`, `Makita`, `Bosch`, `EGO`, `Flex`,
`GearWrench`, `Crescent` (sub-brands inherit their parent — Stiletto / Empire →
`Milwaukee`). Source: parser CSV filename.

## L2 — Quarter-Year label

`Q<N>-<YYYY>` — e.g. **`Q3-2026`**. Universal Q-notation (regardless of the vendor
period token used in titles), with the year appended. Source: parser CSV filename
`<Vendor>-Q<N>-<YYYY>-*.csv`.

## L3 — Promo-type label(s)

| Parser source | Label(s) |
|---|---|
| `Promo-List.csv` (kit) | `Kit-Promo` |
| `RSA-Kits.csv` | `Kit-Promo` **+ `RSA`** |
| `NLP-Sheet.csv` (incl. special-buy) | `NLP` |
| `RSA-NLP.csv` | `NLP` **+ `RSA`** |
| `Other-Promotions.csv`, Promo Type `promo-code` | `Coupon` |
| `Other-Promotions.csv`, Promo Type `buy-more-save-more` | `Coupon` **+ `BMSM`** |
| `Other-Promotions.csv`, Promo Type `e-rebate` | `E-Rebate` |

- **BMSM:** when you detect a Buy-More-Save-More (Other-Promotions Promo Type
  `buy-more-save-more`), add **both** `Coupon` **and** `BMSM`.
- **RSA:** add `RSA` to any RSA / credit-bearing promo (from `RSA-Kits.csv` /
  `RSA-NLP.csv`), **alongside** its base type label.
- Most Tasks get **one** type label (so 3 labels total); BMSM and RSA Tasks get **two**
  type labels (4 total).

## Implementation notes

- Labels are an array of strings on the `labels` system field — set via the Atlassian
  MCP `createJiraIssue` / `editJiraIssue` `fields` parameter.
- Labels are **case-sensitive** and **cannot contain spaces** — emit exactly the Vendor
  display name, `Q<N>-<YYYY>`, and `Kit-Promo` / `NLP` / `Coupon` / `E-Rebate` / `BMSM` /
  `RSA` with the casing shown.

## Example label sets

| Task | Labels |
|---|---|
| Milwaukee Q3 2026 NLP | `Milwaukee`, `Q3-2026`, `NLP` |
| DeWalt Q3 2026 kit (free battery) | `DeWalt`, `Q3-2026`, `Kit-Promo` |
| Milwaukee Q3 2026 RSA kit | `Milwaukee`, `Q3-2026`, `Kit-Promo`, `RSA` |
| Makita Q3 2026 e-rebate | `Makita`, `Q3-2026`, `E-Rebate` |
| Crescent Q3 2026 coupon | `Crescent`, `Q3-2026`, `Coupon` |
| Milwaukee Q3 2026 BMSM | `Milwaukee`, `Q3-2026`, `Coupon`, `BMSM` |
