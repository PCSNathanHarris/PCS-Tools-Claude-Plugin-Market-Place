# Stage validation (AI QA at every major stage)

Before each main gate you run a **validation pass** over that stage's inputs and
outputs: scan them, **auto-correct the safe/mechanical issues**, and **flag the
judgment calls** for the operator. The validation report is shown as part of the
gate so the operator decides with eyes open.

## How to run a pass

- **Mechanical checks → generated script.** Schema/column counts, row counts,
  set diffs, length caps, date parsing, HTML validity, encoding — write and run
  a short throwaway script (Python) so these are exact and scale to thousands of
  rows. Don't eyeball large CSVs.
- **Semantic checks → your judgment.** "Does this title read right", "is this
  kit sensible", "is this exclusion wrong" — read a representative sample and
  reason about it.

## Correction policy — what you may fix vs must flag

**Auto-correct (safe — fix silently, then list what you fixed):**
- Your *own* generated text (kit titles/descriptions): a title over 95 chars
  (shorten per the reduction order in `title-description-rules.md` — never drop a
  SKU), a free/paid mislabel, an empty-paren artifact `( / )`, inconsistent brand
  casing, broken/missing HTML escaping or a missing `KEY FEATURES:` / `INCLUDES:`
  section.
- Pure formatting: stray whitespace, encoding artifacts (mojibake from CP1252),
  trailing separators, doubled spaces.

**Always flag, never silently change (these touch money or external systems):**
- Prices, quantities, SKUs, credits.
- Vendor / quarter / dates.
- Which items are excluded (Non-Included / Needs-Pricing).
- Create-vs-existing kit classification.
- Anything Jira (project target, epic, task identity).

When in doubt, flag — don't fix.

## Report format (show before the stage's gate)

```
Validation — Stage <name>
  ✅ <n> checks passed
  🔧 Auto-corrected (<n>): <one line each>
  ⚠️ Needs your attention (<n>): <one line each, with the file + row>
```
If anything is in ⚠️, fold it into the gate prompt so the operator weighs it
before answering Y/N.

---

## Stage 1 — Parse (validate the Promo-List + sibling CSVs)

**Inputs:** deck, cheat sheet. **Outputs** (in the **parsed output dir**; each
written only when non-empty, except `*-Parser-Audit.csv` which is always
present): `*-Promo-List.csv`, `*-NLP-Sheet.csv`, `*-RSA-Kits.csv`,
`*-RSA-NLP.csv`, `*-Other-Promotions.csv`, `*-Non-Included.csv`,
`*-Needs-Pricing.csv`, `*-Parser-Audit.csv`, and (only when there are review
items) `*-For-Review.xlsx`.

Mechanical:
- Promo-List has the 27 canonical headers in order; every row has 27 fields.
- **$0-kit failsafe:** no row has a SKU in a slot whose Qty or Price is blank
  (free goods must be an explicit `0`/`0.00`, not empty). Flag any.
- Dates parse as non-padded `M/D/YYYY`; Start ≤ End on every row.
- Parser-Audit counts reconcile with the actual row counts of each file that is
  present. **A file's absence = zero rows of that type** (empty outputs aren't
  written) — verify against the Parser-Audit counts; only flag a missing file if
  the audit says it should have rows.
- `Other-Promotions.csv` (when present): 16 canonical headers; every `Promo
  Type` is `buy-more-save-more` / `e-rebate` / `promo-code`; **no `Promo Code`
  cell holds a FLEX `SOT…` / `FLX…` identifier** (that's a deal id, not a
  checkout code).
- `Non-Included.csv` (when present): the retired reasons `e-rebate`,
  `buy-more-save-more`, `promo-code-only` must NOT appear (their presence means a
  stale parser — flag it).
- Files decode cleanly (UTF-8/BOM); no mojibake.
- No exact-duplicate rows.
- **Verification gate (v1.3.0) — independently re-ground; don't just trust the
  parser's own gate:**
  - **Vendor-regex re-match:** with a generated script, load the matched vendor's
    SKU regex (the first `Regex:` under `## SKU pattern`) and assert **every** SKU
    in **every** slot of `*-Promo-List.csv`, `*-NLP-Sheet.csv`, `*-RSA-Kits.csv`,
    `*-RSA-NLP.csv`, `*-Other-Promotions.csv` matches. Any non-match ⇒ ⚠️ (a
    hallucinated SKU that slipped the gate).
  - **No held SKU was emitted:** read `*-For-Review.xlsx`, collect the SKUs on
    `unverified` rows, and assert **none** appears in any emit output. A leak ⇒ hard ⚠️.
  - **`SKUs Held` reconcile:** assert `Parser-Audit.SKUs Held` == the count of
    withheld-emit `unverified` For-Review rows (exclude `missed-on-page`). Mismatch ⇒ ⚠️.
  - **`SKUs Verified` sanity:** assert `Parser-Audit.SKUs Verified` ≈ total filled
    SKU slots across the five emit outputs; a large gap ⇒ ⚠️.

Semantic:
- Vendor + quarter/year match the deck.
- Sample ~5–10 kit rows against the deck pages: paid/free pairing and prices
  look right.
- Scan Non-Included / Needs-Pricing for rows that look like real kits wrongly
  excluded (flag).
- Cheat-sheet fill: every Needs-Pricing SKU is either filled or listed as
  unresolved (no silent gaps).
- **For-Review:** if `*-For-Review.xlsx` exists, relay the parser's table
  (`PCE/Identifier | Page # | Reason(s) | SKUs`) + the workbook link and fold a
  ⚠️ into Gate 2. **Call out verification-held items specifically** — state the
  `SKUs Held` count and that those SKUs/prices were blocked from the Promo-List by
  the grounding gate (Review Class `unverified`), so the operator reviews them
  before continuing.

Auto-correct: whitespace/encoding/date-format only. Flag: missing prices,
suspicious exclusions, vendor/quarter mismatch.

---

## Stage 2 — DECODE + NetSuite round-trip

**Inputs:** Promo-List. **Outputs:** `decode_blocks.txt`, the uploaded NS export.

Mechanical:
- DECODE covers the full unique SKU set from the Promo-List (count **and** set
  match — list any SKU missing from the DECODE).
- DECODE shape: each block ≤ 250 values, balanced parentheses, `vendorname`
  field.
- NS export parses (**read `utf-8-sig` first**, CP1252 only as a fallback — the export is
  UTF-8; reading it as CP1252 produces `â€¢` mojibake) and has the Promo Kit Support columns
  (Internal ID, Vendor Name, etc.).
- **Coverage diff:** SKUs we asked for vs SKUs the NS export returned → list the
  **missing** ones (not yet built in NetSuite) and any extras.

Semantic:
- Judge whether the missing SKUs are expected (genuinely not built) or signal a
  paste/search mistake worth re-running before building.

Flag: missing-SKU list (these become single-member drops downstream), wrong/empty
export. Nothing to auto-correct here.

---

## Stage 3/4 — Kit build + titles/descriptions

**Inputs:** Promo-List (parsed output dir), NS export (NS imports dir).
**Outputs** (NS imports dir): `<prefix>_kit_create.csv`,
`<prefix>_kits_existing.csv` (+ `_RSA`); image ZIP in the images dir.

Mechanical:
- NS Create CSV has the 17 headers; each kit = 1 lead row + (kit_size − 1) detail
  rows; detail rows carry CA Link + Item ID + Item Qty.
- new + existing counts reconcile with the build summary.
- **After Step 4b:** every lead row has a non-empty Page Title (≤ 90 chars, hard
  max 95) and a Detailed Description containing `KEY FEATURES:` and `INCLUDES:`;
  the HTML is valid and escaped; no leftover blank titles.
- Display Name bracket rule: regular kits `(start-end)`, RSA kits `[start-end]`.
- Split integrity: no CA Link appears in both create and existing.
- Single-member drops listed and cross-checked against Stage 2's missing-SKU
  list (a drop with a missing companion SKU is explained, not a bug).

Semantic (QA of your own Step 4b output — second pass):
- Titles read naturally, anchor + free goods combined correctly, FREE marker only
  on free items, brand spelling consistent across the run.
- Descriptions: no duplicated boilerplate, no INCLUDES rows leaking into KEY
  FEATURES, features actually belong to the kit's members.

Auto-correct: your own title/description defects (length, mislabel, HTML, brand
casing) — re-write and re-inject by CA Link. Flag: unexpected single-member
drops, create/existing anomalies, kit-size mismatches.

---

## Stage 6 — Jira (validate task fields BEFORE any write)

**Inputs:** parser CSVs (parsed output dir). **Outputs:** Jira tasks (human-gated).

Checks (before the final write gate — `create-jira-promotions` owns the PROM /
per-row gates; this is an extra pre-write scan):
- Each task summary matches the naming template; labels per `labels.md` (Vendor +
  `Q<N>-<YYYY>` + promo-type token(s), incl. `RSA` / `BMSM` where applicable); dates
  valid; parent Epic resolved for the target project. (No HERO / Priority auto-set as
  of jira v0.3.0.)
- Target project is what the operator chose (PAT vs PROM) and field IDs match it.
- Dedupe: no task unexpectedly collides with an existing one.
- Task count reconciles with the promo groups (Promo-List + NLP + RSA +
  Other-Promotions).

**Never auto-create or auto-edit Jira.** Jira writes stay fully human-gated —
this pass only surfaces problems into the WRITE gate.

---

## Key rules

- Validation runs **before** each stage's Yes/No gate; its ⚠️ items feed the gate
  prompt.
- Mechanical checks use generated scripts; semantic checks use judgment.
- Auto-correct only your own generated text + formatting. **Never** silently
  change prices, SKUs, quantities, exclusions, classifications, or Jira targets.
- A failed mechanical check that you cannot safely correct is a ⚠️ — surface it;
  let the operator decide whether to stop or proceed.
