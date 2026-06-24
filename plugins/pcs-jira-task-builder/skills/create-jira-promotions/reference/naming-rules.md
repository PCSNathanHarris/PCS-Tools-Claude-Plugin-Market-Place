# Naming rules — Jira Task summary

Canonical rules for every Task title the skill generates. Numbered N1–N11 for cross-reference.

## N1 — Standard title template

```
<YYYY> <Period> - <Category>[ — <Specifics>][ [<ID>]]
```

Components:
- `<YYYY>` — 4-digit year (e.g. `2026`).
- `<Period>` — vendor-dependent (Rule N4 below).
- `<Category>` — controlled vocabulary token (Rule N5 below).
- `<Specifics>` — optional, **generalized title-cased phrase** describing the deal (e.g. `M18 Tool With a Free Battery`). Em-dash separator (`—`), not hyphen. **Never put raw SKUs, ALL-CAPS deck text, or `BUY (n)…GET (n)` phrasing here** (see N5/N6).
- `<ID>` — the deck's native promo identifier in the **last** position, bracketed (Rule N8): `[PCR: P-00208522]` / `[PCE: 262776]`. Omit when the page has none or the Task consolidates multiple IDs.

**No vendor-name prefix.** The title starts with `<YYYY> <Period>` — the vendor is carried by the parent Epic (and the platform token, e.g. `M18` / `20V` / `60V`, implies the brand). Never lead with `Milwaukee ` / `DeWalt ` / etc.

Example: `2026 P3 - M18 Tool With a Free Battery [PCE: 262776]`

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
| Milwaukee | `P<N>` | **P = the deck's quarter number** — Q1→P1, Q2→P2, Q3→P3, Q4→P4 |
| DeWalt | `P<N>` | Q1→P1, Q2→P2, Q3→P3, Q4→P4 |
| Makita | `P<N>` | Q1→P1, Q2→P2, Q3→P3, Q4→P4 |
| Bosch | `P<N>` | Q1→P1, Q2→P2, Q3→P3, Q4→P4 |
| GearWrench | `P<N>` | Q1→P1, Q2→P2, Q3→P3, Q4→P4 |
| EGO | `H1` / `H2` | Q1/Q2 → H1; Q3/Q4 → H2 (half-year — the exception) |
| Flex | `Q1` / `Q2` / `Q3` / `Q4` | Direct (no remap) |
| Crescent | n/a — uses Rule N2 (coupon-code) | n/a |
| SKIL (under OTHER BRANDS Epic) | Year-quarter-vendor compound | e.g. `2026 Q3 SKIL NLPs` |
| Fluke, JPW, Fondue Discounts, Specials/Self-Funded | Hand-managed | Skill never generates |

**`<Period>` = `P` + the deck's quarter digit for power-tool vendors (P1–P4); the deck
quarter is authoritative — never remap to a half-year.** (Confirmed against PROM: DeWalt /
Milwaukee Q3 promos read `2026 P3 - …`.) EGO/OPE is the only half-year exception (`H1`/`H2`);
Flex uses the quarter directly.

**Note on labels vs titles:** the labels field (Rule L1–L3 in
`labels.md`) always uses universal Q-notation (`Q<N>-<YYYY>`, e.g. `Q3-2026`) regardless
of vendor. The title field uses the vendor-specific period token
above. This is intentional — labels are queryable cross-vendor; titles
preserve PROM display convention.

## N5 — `<Category>` / `<Specifics>` — generalize to PROM style

`<Category>` (and any `<Specifics>`) carry a **short, title-cased, generalized human
phrase** — never deck-verbatim text and never SKUs. Map the deck's phrasing to a clean
phrase:

| Parser source → | Generalized title text |
|---|---|
| NLP-Sheet rows, `Source Marker` = `nlp` OR `special-buy` | fold into the single `NLPs` parent (Special Buys included — same title, same Promo Type, same fields) |
| Promo-List, `BUY (1) BARE TOOL, GET (1) <battery>` | `20V Bare Tool With a Free Battery` (use the platform — `20V`/`M18`/`60V` — not the SKU) |
| Promo-List, `… GET (1) <starter kit>` | `Bare Tool With a Free Starter Kit` |
| Promo-List, paid + free SKU shape (general) | `<Platform> Tool With a Free <short noun>` / `Buy <Kit> Get a Free <short noun>` |
| Promo-List, multi-paid bundle (no free) | `Kit + Bare Tool Bundle` / `<Category> Bundle` (or specific: `Lighting Bundle`, `Nailer Bundle`) |
| RSA-Kits rows | `RSA Kits` |
| RSA-NLP rows | `RSA NLPs` |
| Needs-Pricing rows (out of scope) | `Needs Pricing` |
| Other-Promotions rows, Promo Type `e-rebate` | `E-Rebate` (N1 template) |
| Other-Promotions rows, Promo Type `buy-more-save-more` | `<Category> BMSM` (N1 template) |
| Other-Promotions rows, Promo Type `promo-code` | uses **Rule N2** title format, not a Category |

Rules:
- **No SKUs in the title.** SKUs live only in the description SKU table; the only code-like
  token allowed is the trailing `[<ID>]` bracket (N8).
- **No deck SHOUTING / `BUY (n)…GET (n)` boilerplate** — title-case and rephrase (N6).
- Lead with the platform (`20V`, `M18`, `60V`) where it identifies the line; it implies the brand.

**When in doubt:** prompt the user before guessing a Category. Wrong
categories cost board-view clarity downstream.

## N6 — Auto-normalize spacing/punctuation + de-SHOUT

Every generated title must be normalized:

- Single space between tokens (kill double/triple spaces).
- `W/ Free X` with one space after `W/`, never `W/Free X`.
- Em-dash (`—`) between `<Category>` and `<Specifics>`, never a regular
  hyphen in that slot.
- No trailing whitespace.
- No apostrophes — write `NLPs`, not `NLP's`.
- **De-SHOUT:** title-case any ALL-CAPS deck text (e.g. `20V BARE TOOL BOGO` → `20V Bare Tool`);
  keep genuine acronyms / platform tokens (`M18`, `20V`, `RSA`, `NLP`, `BMSM`, `BOGO`) as-is.
- **Strip `BUY (n)` / `GET (n)` boilerplate** — rephrase as a generalized deal (N5), e.g.
  `BUY (1) BARE TOOL, GET (1) DCB2104-2` → `Bare Tool With a Free Battery`.
- **No SKUs** anywhere in the title except the trailing `[<ID>]` bracket (N8).

## N7 — (removed in v0.3.0)

HERO auto-marking was **removed in v0.3.0** — the plugin never appends ` (HERO)` to a
title and never sets Priority. (Rule number kept so later N-references don't shift.)

## N8 — PCE/PCR identifier handling — keep it in the title (v0.4.0)

Parser emits `Promo Name` ending in `[PCE NNNNNN]` or `[PCR NNNNNN]`
(DeWalt prints `P-########` / `PCR ######`; Milwaukee prints `PCE ######`).

**Keep the identifier in the title, at the very end, bracketed with a colon:**
```
<YYYY> <Period> - <generalized deal> [<ID>]
```
- Milwaukee: `[PCE: 262776]`
- DeWalt: `[PCR: P-00208522]`
- If the page has **no** identifier → omit the bracket entirely (never invent one).
- **Consolidated / multi-ID Tasks** (e.g. the single NLP parent that spans 8 different
  P-numbers) → **omit the bracket** — never force one wrong ID onto a multi-promo parent.

**Also keep** the `Promo Identifier: <ID>` line in the Task description (belt-and-suspenders)
until a dedicated `Promo Identifier` custom field exists on the Task issue type — then switch
to populating that field directly (tracked in the team's admin checklist).

Examples:
- `2026 P3 - 20V Bare Tool With a Free Battery [PCR: P-00208522]`
- `2026 P3 - Combo Kit + Miter Saw Bundle [PCR: P-00211134]`
- `2026 P3 - NLPs` (consolidated parent — no bracket)

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
