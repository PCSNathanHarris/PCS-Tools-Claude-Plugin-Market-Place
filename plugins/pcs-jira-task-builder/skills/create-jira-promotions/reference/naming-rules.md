# Naming rules — Jira Task summary

Canonical rules for every Task title the skill generates. Numbered N1–N11 for cross-reference.

## N1 — Standard title template

```
<YYYY> <Period> - <Category>[ — <Specifics>]
```

Components:
- `<YYYY>` — 4-digit year (e.g. `2026`).
- `<Period>` — vendor-dependent (Rule N4 below).
- `<Category>` — controlled vocabulary token (Rule N5 below).
- `<Specifics>` — optional SKU-callout descriptor (e.g. `DCB205-2C + 2 Bare Tools @ $299`). Em-dash separator (`—`), not hyphen.

Example: `2026 P2 - Free Battery — M18 1852 + 2 Bare Tools @ $299`

## N2 — Coupon-code title format (v0.2.0)

```
<Vendor> <YYYY> Coupon Code - <CODE>
```

With a deck-supplied event:

```
<Vendor> <Event> <YYYY> Coupon Code - <CODE>
```

Holidays/events (Memorial Day, Black Friday) are PCS-internal — the
skill never invents them. Insert only if explicitly extracted from the
deck text. Coupon Tasks always parent to the `COUPON CODE PROMOS` Epic.

As of parser v1.2.0, coupon-code promos arrive in `Other-Promotions.csv`
(Promo Type `promo-code`), so this skill generates these titles automatically.
`<CODE>` is the `Promo Code` column — never a FLEX `SOT…` deal identifier.

## N3 — Standalone / hand-managed Tasks (skill never touches)

Tasks that don't come from parser output (e.g. `Knaack Weatherguard 40`,
`Werner SRLs 10%`, free-form one-offs) are out of the skill's scope.
**The skill never overwrites titles it didn't generate.** When the
dedupe check (Step 7 of SKILL.md) finds an existing Task with a
non-canonical title, leave it untouched.

## N4 — Per-vendor period format

Different vendors use different period markers. Map the parser's CSV
filename quarter to the right token per vendor:

| Vendor | Period format | Q → Period mapping |
|---|---|---|
| Milwaukee | `P1` / `P2` | Q1/Q2 → P1; Q3/Q4 → P2 (half-year periods) |
| DeWalt | `P1` / `P2` | Q1/Q2 → P1; Q3/Q4 → P2 |
| Makita | `P1` / `P2` | Q1/Q2 → P1; Q3/Q4 → P2 |
| Bosch | `P1` / `P2` | Q1/Q2 → P1; Q3/Q4 → P2 |
| GearWrench | `P1` / `P2` | Q1/Q2 → P1; Q3/Q4 → P2 |
| EGO | `H1` / `H2` | Q1/Q2 → H1; Q3/Q4 → H2 |
| Flex | `Q1` / `Q2` / `Q3` / `Q4` | Direct (no remap) |
| Crescent | n/a — uses Rule N2 (coupon-code) | n/a |
| SKIL (under OTHER BRANDS Epic) | Year-quarter-vendor compound | e.g. `2026 Q3 SKIL NLPs` |
| Fluke, JPW, Fondue Discounts, Specials/Self-Funded | Hand-managed | Skill never generates |

**Note on labels vs titles:** the labels field (Rule L1–L3 in
`labels.md`) always uses universal Q-notation (`Q1`–`Q4`) regardless
of vendor. The title field uses the vendor-specific period token
above. This is intentional — labels are queryable cross-vendor; titles
preserve PROM display convention.

**Open follow-up:** the P1/P2 half-year mapping is the team's
inferred convention. Confirm with team before bulk-running on a Q3
deck. If P1/P2 actually map differently (e.g. P1=Q1 alone), adjust the
table above.

## N5 — Controlled `<Category>` vocabulary

| Parser source → | `<Category>` token |
|---|---|
| NLP-Sheet rows, `Source Marker` = `nlp` OR `special-buy` | `NLPs` (Special Buys fold into NLPs — same title, same Promo Type, same fields) |
| Promo-List rows with paid + free SKU shape | Derive from row content: `Free Battery`, `Free Bare Tool`, `Free Tool Kit`, `Free Starter Kit`, `BOGOs`, `Free Cooler/Warmer`, etc. |
| Promo-List rows, multi-paid bundle (no free) | `Bundles` (or specific: `Lighting Bundles`, `Nailer Bundles`, `Concrete Tool Bundles`) |
| RSA-Kits rows | `RSAs` |
| RSA-NLP rows | `RSAs` |
| Needs-Pricing rows (out of scope) | `Needs Pricing` |
| Other-Promotions rows, Promo Type `e-rebate` | `E-Rebate` (N1 template) |
| Other-Promotions rows, Promo Type `buy-more-save-more` | `BMSM` (N1 template) |
| Other-Promotions rows, Promo Type `promo-code` | uses **Rule N2** title format, not a Category |

**When in doubt:** prompt the user before guessing a Category. Wrong
categories cost board-view clarity downstream.

## N6 — Auto-normalize spacing/punctuation

Every generated title must be normalized:

- Single space between tokens (kill double/triple spaces).
- `W/ Free X` with one space after `W/`, never `W/Free X`.
- Em-dash (`—`) between `<Category>` and `<Specifics>`, never a regular
  hyphen in that slot.
- No trailing whitespace.
- No apostrophes — write `NLPs`, not `NLP's`.

## N7 — (removed in v0.3.0)

HERO auto-marking was **removed in v0.3.0** — the plugin never appends ` (HERO)` to a
title and never sets Priority. (Rule number kept so later N-references don't shift.)

## N8 — PCE/PCR identifier handling

Parser emits `Promo Name` ending in `[PCE NNNNNN]` or `[PCR NNNNNN]`.
PROM Task titles don't use these.

**For v0.1.0:**
- Strip the bracketed identifier from the Jira Task title.
- Keep it in the Task description as a line: `Promo Identifier: PCE NNNNNN`.

**Future:**
- When the PCS team adds a dedicated `Promo Identifier` custom field to
  the Task issue type, switch to populating that field directly.
  (Tracked in the team's admin checklist.)

## N9 — Sub-task title format

When a Task has multiple distinct date windows:
```
MM/DD-MM/DD
```

No year. No wave labels. Single-date-window Tasks have no sub-tasks.

## N10 — Re-run / dedupe

On every group ready to create, search Jira:
```
project = <TARGET> AND summary = "<canonical>" AND parent = <EPIC_KEY>
```

If match found:
- Prompt `Update existing <TARGET>-NNN? (Y / Skip / Cancel)`.
- Per choice: update fields in place / leave existing alone / abort the
  entire run.

If no match: create.

Dedupe key is `(canonical title, parent Epic)` — dates are implicit in
the title.

## N11 — Project target

PAT default; PROM requires the literal-phrase gate in `safety.md`. Hard
constraint, no overrides.
