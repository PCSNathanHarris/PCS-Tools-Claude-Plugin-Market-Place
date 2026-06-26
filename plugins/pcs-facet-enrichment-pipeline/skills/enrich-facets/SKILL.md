# Enrich Facets — Anglera → Gap Analysis → PDP Backfill → NetSuite

Take an Anglera **Faceted Search Backfill** export, find the coverage gaps, fill the
recoverable blanks with HIGH-confidence values read from each product's real source
PDP, and produce a **NetSuite-ready facet import**. Designed so a non-technical
operator only has to: drop in the export, name the brand, and double-click a runner
when prompted. Claude does everything else and pauses for a Yes/No at two gates.

---

## Step 0 — Locate the working files

Before starting, confirm these exist in the project folder. If one is missing, ask.

- **Anglera export** — the `Faceted Search Backfill ... .csv` the operator dropped in (REQUIRED).
- **Attribute master** — `attributes (15).csv` (or newest `attributes (NN).csv`). This is the **value authority**: per-attribute `Name`, `Type`, `Dropdown Values`, `Key`. (REQUIRED.)
- **Category tree (fallback)** — `TUP_Master_Facets_V2_export_cleaned_with_PT.csv` for L2 → linked-attribute mapping (used because the live linked-attributes export isn't available). (REQUIRED.)

Ask the operator for the **brand name** (e.g., "Guardian", "DeWalt"). It drives source-URL selection and is matched case-insensitively against the source URLs.

Read `reference/gap-analysis.md` and `reference/netsuite-format.md` now so you understand the value rules before touching data.

---

## Step 1 — Validate the export shape

Confirm the export has: `Input Product Name`, `Internal ID`, `Master Facet Category`,
`Source URL 1..N`, `Page Title`, `Detailed Description`, the `Facet 1..N` columns, and
(if present) the leftover `Safety Rating 1..10` / `Pack Quantity` raw columns.

Parse each `Facet N` cell as `Label: value`. Build, per SKU, the set of attribute
**keys** already filled (map label→key via `attributes (15).csv` `Name`↔`Key`).

---

## Step 2 — Gap analysis  *(Claude, automatic)*

Follow `reference/gap-analysis.md`. Produce:
- a coverage report (per-L2 × attribute RYG, per-attribute, per-L2, PT canonical adjusted), and
- a **backfill plan**: the prioritized list of `(L2, attribute)` blanks that are *recoverable* (tree-linked + diagnosed prompt-miss/PDP-quality; exclude wrong-attribute).

**The backfill plan is what the scraper is told to look for first.** It directly informs the scan: for each SKU, the scraper targets that SKU's L2 gap attributes (the diagnosed-recoverable ones) as its primary extraction list, ordered by how under-filled the attribute is brand-wide. This focuses the scan on what's actually missing instead of re-deriving everything.

Save the gap report to the project folder. **GATE 1 — show the headline numbers + the prioritized target list and ask the operator: proceed to the PDP scan? (Yes/No.)** Do not continue until Yes.

---

## Step 3 — Generate & configure the scraper  *(Claude, automatic)*

The marketplace is markdown-only, so **generate the script at run time** — do not expect a committed `.py`. Using `reference/pdp-backfill-script.md` and `reference/runner-bat.md`:

1. Write `pdp_backfill.py` into the project folder, configured for this run:
   - input = the Anglera export; authority = `attributes (15).csv`; tree = the cleaned tree;
   - **target only the backfill-plan attributes** (tree-linked, blank);
   - **brand-URL source selection:** for each SKU choose the source URL whose host/path contains the brand name (case-insensitive, normalized — e.g. "Guardian"→`guardianfall.com`); if none match, use the **first available** source URL;
   - enforce the value rules in Step 5.
2. Write `run_backfill.bat` (one-click: builds the Python env + installs Playwright/openpyxl on first run using the operator's installed Chrome/Edge, then runs `pdp_backfill.py`).

Tell the operator, in plain language, to **double-click `run_backfill.bat`** and wait for the live counter to finish. (One-time: it sets up the environment on first run.)

---

## Step 4 — Operator runs the scan  *(operator, one click)*

The runner renders each product's real PDP (JavaScript) and writes:
- `*_GapFill_PDP.xlsx` — the export in its original schema, recovered cells highlighted green;
- `*_GapFill_log.csv` — every value added + the source PDP URL;
- `*_dropdown_additions_needed.csv` — proposed dropdown additions: out-of-dropdown values that reasonably belong to an attribute AND appear on **> 5 products in the batch** (columns: Attribute, Proposed Value, Occurrences, Sample SKUs, Sample Source URL, Suggested Action ADD/NORMALIZE). Values seen ≤ 5 times, or that don't reasonably map to the attribute, are left blank and NOT proposed.

Wait for the operator to confirm the runner finished, then read those outputs back in.

---

## Step 5 — Value rules the scan must enforce (and you must verify)

- **Blanks only** — never overwrite a value Anglera already produced.
- **Tree-linked only** — only fill attributes linked to that SKU's L2 in the tree.
- **HIGH-confidence / explicit only** — the value must be stated on the page. No inference.
- **Single vs multi — fixed allowlist.** Only three attributes may hold multiple comma-joined values in one cell: **`safety_rating`, `drive_size`, `battery_compatibility`**. **Every other attribute is single-value** — even if `attributes (NN).csv` types it `MULTI_SELECT`, write only one value. This is enforced a second time at the NetSuite-format step (Step 7), which collapses any multi-value that Anglera already produced in a descriptive field (e.g. `For Use On`, `For Use With`, `For Joining`, `Material`) down to its first value.
- **Strict dropdown validation** — for `ENUM`/`MULTI_SELECT` attributes the written value MUST match a `Dropdown Values` entry in `attributes (15).csv` after normalization. Apply the standing **normalization map** first (strip ANSI year/edition suffixes e.g. `ANSI Z359.11-2021`→`ANSI Z359.11`; `csa`→`CSA Certified`; `Telecoms`→`Telecom`; `Self-Retracting`→`Self-Retracting (SRL)`). If it still doesn't match, **never write it.**
- **Frequency-gated dropdown discovery** — track each out-of-dropdown value that reasonably belongs to its attribute. If one appears on **> 5 products in the batch**, add it to `dropdown_additions_needed.csv` (with occurrence count + sample SKUs/source) as a proposed addition for operator approval — still NOT written to the output this run. Below the threshold, leave blank and don't propose.
- **application must be specific** — map the stated use / Industries to the most specific valid dropdown value; never default to "Construction" when something more specific is stated.
- **Do not add `connection_type` on harness L2s** (redundant with D-ring config).
- **Facet label = the attribute `Name`** from `attributes (15).csv`.
- **Sources:** read the full rendered HTML + embedded `__NEXT_DATA__` JSON for Compliance→`safety_rating` and Industries→`application`; read clean visible text for description-based attributes.

---

## Step 6 — QA / before-after  *(Claude, automatic)*

Compare the filled file to the original export: overall coverage lift, per-attribute deltas, count recovered (HIGH), count still blank with reason, and the dropdown-additions list. Save a short comparison report to the project folder.

---

## Step 7 — NetSuite format  *(Claude)*

**GATE 2 — confirm with the operator before generating the NetSuite file.** Then follow `reference/netsuite-format.md`:

- Output columns: `Input Product Name`, `Internal ID`, then `Facet 1 … Facet N`.
- `N` = the max facet count of any included row after backfill (trim trailing empties).
- Each facet cell = `Label: value`; multi-value comma-joined in one quoted cell.
- **Product Type is Facet 1**; remaining facets keep Anglera order; gaps compacted out.
- **Trim** Source URLs, Page Title, Detailed Description, Master Facet Category, and the leftover `Safety Rating 1..10` / `Pack Quantity` raw columns (their facet versions already exist as Facet cells).
- **Include only rows with ≥ 1 facet.**
- Pass `Input Product Name` through unchanged (brand prefix + spacing). Write UTF-8 (BOM) CSV named **`Facet Backfill NS Import - <Vendor/Category>.csv`**.

---

## Step 7b — Deliver the NS import to Google Drive

Upload **only the final NetSuite import file** to the shared Drive "NS import folder" (anyone-with-link) via the Google Drive connector. **Do not change any sharing/permissions** — the folder already grants access; uploaded files inherit it.

- **Exactly one file goes to Drive:** `Facet Backfill NS Import - <Vendor>.csv`. Nothing else is uploaded.
- Folder ID: `1IB4PzPFoUMWDQmYBzo6cV56tviXVXcgK`
- Use `create_file` with `parentId` = that folder ID, `title = "Facet Backfill NS Import - <Vendor>"`, `contentMimeType = text/csv`, `disableConversionToGoogleType = true` (keep a real CSV, not a Google Sheet).
- Capture the returned Drive link to report in Step 8.

**Everything else stays local.** The gap report, `backfill_plan.csv`, the PDP-filled `*_GapFill_PDP.xlsx` + `*_GapFill_log.csv`, the QA/before-after summary, and `*_dropdown_additions_needed.csv` all remain in the operator's working folder and are **not** uploaded. Report their local paths in Step 8.

---

## Step 8 — Report

Print: coverage before→after, # values recovered (HIGH), # rows in the NetSuite import, # dropdown additions flagged, the **local output paths** for every file (gap report, backfill plan, PDP-filled xlsx + log, QA summary, dropdown-additions list), and the single **Google Drive link** to the uploaded `Facet Backfill NS Import - <Vendor>.csv`. Offer to open the (local) dropdown-additions list for review.

---

## Key rules

- **Two gates only** (after gap report; before NetSuite output) — otherwise run unattended.
- **Markdown-only plugin:** generate `pdp_backfill.py` + `run_backfill.bat` at run time; never rely on committed code.
- **`attributes (15).csv` is the single source of truth** for attribute Name, Type (single/multi), and valid dropdown values. When a newer `attributes (NN).csv` is present, use the newest.
- **Never inject a value that fails dropdown validation** — flag it instead.
- **No secrets** in any generated/committed file.
- Detailed rules live in `reference/` — read the relevant doc before each step rather than guessing.
