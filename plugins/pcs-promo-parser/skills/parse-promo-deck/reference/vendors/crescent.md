# Crescent

## Brand keywords

- `crescent`
- `apex tool` (Apex Tool Group, parent brand)

## SKU pattern

Regex: `\b(?:CTK|CRW|CCMT|CDW|C[A-Z]{2,4})\d+[A-Z0-9-]*\b`

Examples:
- `CTK170`, `CTK128MP` (tool kits)
- `CRW10` (ratcheting wrenches)
- `CCMT350` (combo sets)

The leading `C` is a heuristic; Crescent layouts vary.

## Promo code pattern

**None.** Crescent doesn't use per-page promo codes. Use deal title.

## Price label priority

1. `Promo IMAP`
2. `PMAP`
3. `Sugg. Retail`, `Sug Retail`
4. `MAP`
5. `IMAP`
6. `MSRP`

The first matching column wins, but Crescent decks vary so much that
you should **flag every page for review** if the price column is
ambiguous.

## Non-price labels

- `Description`

## Header signatures

- `SKU Part No Description MAP`
- `SKU Description IMAP MSRP`
- Variants without clear column headers (single-column price lists)

Signature tokens:
- `SKU`
- `Part No`, `Part No.`
- `Description`
- `MAP`, `IMAP`, `MSRP`

## Quirks — CRITICAL

**Crescent layouts vary significantly between decks.** The rule
parser's harness flags every Crescent deck for human review. As an AI
agent, before emitting rows, confirm with the user:

1. **Which column is the customer-facing price?** (`Promo IMAP`,
   `MAP`, `MSRP`, etc. — show them the header you found.)
2. **Are there any free goods, and how are they indicated?** (`FREE`
   marker? Strikethrough? Image-only panel?)
3. **Are multiple promo groups on the slide?** (Sometimes one page
   contains 3+ distinct promos.)
4. **What is the date format / label?** (Crescent uses varying
   labels — could be "Promo Window", "Execution", "Sale Dates", etc.)

If the user confirms, proceed. If they don't respond, still emit your
best-effort rows to their normal buckets **and** add a `for_review` row
(Review Class `low-confidence`, reason `crescent-layout-unconfirmed`) per
uncertain page, and set the run-level `Flags` field in `Parser-Audit.csv`
(e.g. `crescent-unconfirmed`). The For-Review workbook + chat table surface
these for the operator. See `reference/output-csvs.md#for-reviewxlsx`.

For consistently-formatted Crescent decks (rare), the standard
extraction works fine; the user just confirms once.
