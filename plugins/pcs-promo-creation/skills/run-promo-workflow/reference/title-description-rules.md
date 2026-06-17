# Kit title & description rules (Claude-applied)

In this pipeline **you** write each kit's Page Title and Detailed Description —
the Kit Builder leaves them blank (`build-imports --blank-titles`). These are
the rules ported from the original Anglera prompts (the same ones the tool's
deterministic generators encode). Apply them with judgment: the point of moving
this to Claude is to fix the three things the rigid version got wrong —
**awkward/over-truncated titles, mislabeled free-vs-paid items, and
inconsistent brand/spec wording.**

## What you're filling, and the inputs

After `kb build-imports --blank-titles`, the run directory has
`<prefix>_kit_create.csv` (the NS Create CSV). Each **kit** is one **lead row**
(carries Page Title col + Detailed Description col, currently empty) followed by
`kit_size - 1` **detail rows**; all rows of a kit share the same **CA Link**.
The member's NetSuite id is in **Item ID**; quantity in **Item Qty**.

To write a good title/description you need three inputs from the run directory:

1. **`<prefix>_kit_create.csv`** — the kit groupings (CA Link → its Item IDs) and
   the two empty cells you will fill (lead row only).
2. **The NetSuite export** the operator uploaded — join on **Item ID / internal
   id** to get each member's **Name, Page Title, Detailed Description, Brand,
   Manufacturer, vendor SKU**. This is your source text.
3. **The `*-Promo-List.csv`** — to know **which members are FREE vs PAID**: a
   member whose Item Price is `0`/`0.00` is a **free good**; the others are
   paid **anchors**. (Map create-CSV Item ID → NS export `vendor_name` → the
   promo list SKU to read its price.)

Do not hand-edit hundreds of cells. Decide the title + description per kit
(the judgment part), then write them into the lead rows **by CA Link** with a
short generated script (read the CSV, set Page Title / Detailed Description on
each lead row, write it back UTF-8-with-BOM, leaving every other cell exactly
as-is). See `kit-stage.md`.

---

## TITLE rules

**Shape:**
```
{Brand} {Main SKU} {short descriptor}[, {qty} Pack] Kit[ W/ {additional(s)}]
```
- The **main item is the paid anchor** (highest-value paid member). Each
  additional is appended after `W/`, multiples joined with ` and `.
- A **free** additional is prefixed `FREE`: `… W/ FREE {SKU} {descriptor}`.
  PAID additionals get no marker. **Getting this right is one of the fixes** —
  never label a paid item FREE or drop the FREE marker from a free good.
- The literal word **"Kit" appears exactly once**, right after the main item
  (after any pack suffix). If a source title already contains "Kit", don't
  double it.
- `qty > 1` → append `, {qty} Pack` before "Kit" (e.g. `…, 2 Pack Kit`).

**Brand — normalize to the canonical name (consistency fix):**
```
milwaukee→Milwaukee  dewalt/de walt→DeWalt  makita→Makita  bosch→Bosch
gearwrench/gear wrench→GearWrench  ego/ego power/ego power+→EGO
flex/flex tools→Flex  crescent/apex tool→Crescent
```
Unknown brands → Title Case. Keep model numbers exactly as printed.

**Length: target ≤ 75 chars, hard max 80.** When over, **shorten intelligently
instead of truncating** (the truncation fix). Strip in this order, only as much
as needed, and **keep every SKU as long as possible**:
1. Always-strip cruft: `(Bare)`, `(Tool Only)`, trailing "with X battery/charger".
2. Platform/voltage filler: `M18 FUEL`, `M12 FUEL`, `XGT`, `LXT`, `FUEL`, `XR`,
   `ATOMIC`, `20V max`, `18V`, `Lithium-Ion`, etc.
3. Spec/marketing filler: chuck sizes, `Brushless`, `Cordless`, `Compact`,
   `Variable Speed`, amp-hours (`5.0Ah`), weights (`3.5 lb`), parenthetical
   sizes (`(1/4")`).
4. Sub-brand ALL-CAPS tokens (4+ chars) and a redundant trailing "Kit" on
   additionals; cap each additional's descriptor to its product noun.
5. **Only as a last resort** drop an additional's SKU (keep its descriptor),
   then hard-truncate at a word boundary.

**Cleanup:** remove empty parentheses (`( / )`), collapse double spaces, trim
orphan trailing `& / , ; :` and dangling `W/`. Strip any `[PCE …]` / promo
code from the title (it belongs only in NetSuite fields, not the title).

---

## DESCRIPTION rules

Emit this exact HTML structure (labels verbatim, with trailing colons):
```html
<p>{one-paragraph intro}</p>
<h3>KEY FEATURES:</h3>
<ul><li>…</li> … </ul>
<h3>INCLUDES:</h3>
<ul><li>({qty}) {SKU} {short descriptor}</li> … </ul>
```

**Intro** — one tight paragraph naming the brand, the main item, and what the
kit is for; mention the free good(s) as a bonus when present. Don't repeat the
title verbatim and don't list specs here.

**KEY FEATURES** — up to **5** bullets, drawn from the members' Detailed
Description source text (prefer the main paid item; pull from additionals if
the main yields fewer than ~3):
- Pull real product features only. **Never** include: the INCLUDES list items
  (`(1) …` qty-prefixed lines), section headers (`FEATURES:`, `SPECIFICATIONS:`,
  `WHAT'S IN THE BOX:`), warnings / CA Prop 65 / "see manual" / "made in" /
  country-of-origin boilerplate, or truncated `(more...)` fragments.
- Decode HTML entities, strip leading bullet characters, de-duplicate, and keep
  each bullet a clean standalone phrase (roughly 6–200 chars).
- If the source has no usable features, write a few accurate capability bullets
  for that kit type — never invent specs.

**INCLUDES** — one `<li>` per member in kit order (paid first, then free):
`({qty}) {vendor SKU} {short descriptor}`. Strip the brand prefix and a
redundant trailing "Kit" from the descriptor; re-prepend the vendor SKU. **No
"FREE" marker here** — FREE is a title-only distinction; quantity + position
carry it in the INCLUDES list.

**HTML-escape** all text content (`&`→`&amp;`, `<`, `>`). Keep it valid,
self-contained HTML (no `<html>`/`<body>` wrapper).

---

## Consistency across the run

Use the same brand spelling, the same descriptor for a repeated SKU, and the
same intro pattern for the same kit type across all kits in a run — don't let
two near-identical kits come out with different brand casing or wording.
