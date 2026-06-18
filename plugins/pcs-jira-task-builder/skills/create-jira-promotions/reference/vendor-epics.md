# Vendor → Epic lookup

Every parser CSV's vendor maps to a parent Epic in the target Jira
project. Each created Task is parented to the right Epic.

## PAT (test) — Promotions Automation Testing

| Vendor | Epic key |
|---|---|
| Milwaukee | `PAT-29` |
| DeWalt | `PAT-30` |
| Makita | `PAT-72` |
| Bosch | `PAT-112` |
| EGO | `PAT-113` |
| Flex | `PAT-114` |
| Fluke | `PAT-115` (hand-managed; parser doesn't produce Fluke output today) |
| JPW | `PAT-116` (hand-managed; parser doesn't produce JPW output today) |
| GearWrench | `PAT-110` |
| Crescent | `PAT-117` (COUPON CODE PROMOS — Crescent doesn't have its own Epic) |
| SKIL | `PAT-119` (OTHER BRANDS) |
| Specials / Self-Funded (cross-vendor) | `PAT-111` |
| Fondue Discounts (program-specific) | `PAT-118` |
| Coupon-code promos (any vendor) | `PAT-117` |

## PROM (production) — TU - Promotions

| Vendor | Epic key |
|---|---|
| Milwaukee | `PROM-354` |
| DeWalt | `PROM-357` |
| Makita | `PROM-356` |
| Bosch | `PROM-359` |
| EGO | `PROM-360` |
| Flex | `PROM-361` |
| Fluke | `PROM-362` |
| JPW | `PROM-363` |
| GearWrench | `PROM-355` |
| Crescent | `PROM-364` (COUPON CODE PROMOS) |
| SKIL | `PROM-710` (OTHER BRANDS) |
| Specials / Self-Funded | `PROM-358` |
| Fondue Discounts | `PROM-432` |
| Coupon-code promos | `PROM-364` |

## Resolving the right Epic

1. Read the parser CSV filename's `<Vendor>` segment.
2. Map to the canonical vendor name (case-normalize).
3. Look up the row in the table for whichever project is the
   resolved target from SKILL.md Step 1 (PAT or PROM).
4. **Other-Promotions (v0.2.0):** `promo-code` rows parent to the **Coupon-code
   promos** Epic (`PAT-117` / `PROM-364`). `e-rebate` and `buy-more-save-more`
   rows have no dedicated Epic — parent them to the **vendor** Epic (same as that
   vendor's kit / NLP Tasks).

## Validation before write

These Epic keys are baked into this reference file. Before creating
Tasks, do a quick sanity check by fetching the Epic from Jira (via
`getJiraIssue`) and confirming:
- `issuetype.name == "Epic"`
- `summary` matches the vendor name (case-insensitive)

If a mismatch is found, abort with a clear error. The Epic structure
in PAT/PROM should not change without a deliberate plugin update.

## When the parser ships a vendor not in this table

If the parser emits a CSV for a vendor not listed above (e.g. a new
vendor PCS just onboarded), the skill should:
1. Log the gap loudly in the console summary.
2. Prompt the user: `No Epic mapping for vendor <X>. Provide the Epic key or skip these rows?`
3. Either accept a user-provided Epic key and proceed, or skip every
   row for that vendor.

Don't guess. A wrong parent Epic puts the Task in the wrong board
column and disrupts triage.

## Stiletto / Empire (Milwaukee sub-brands)

Tasks for Stiletto or Empire promos inherit Milwaukee's Epic (and
storefront mapping from `description-spec.md`). The skill detects
these via Promo Name substring match (`stiletto` / `empire` /
`empire packout`) — when matched, treat as Milwaukee for Epic
purposes but keep the sub-brand name in the Task Specifics field
if the title needs it (per `naming-rules.md` Rule N1).
