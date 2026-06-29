# Report format & delivery

Every run produces a **report workbook** via `build_report.py` (step 1f; weekly combined at step 2).

## Columns (one row per classified product)
`Store · Shopify ID · Shopify Handle · Variant SKU · Title · Vendor · Category Tree Logic · Proposed Tags Applied · Confidence (0-100)`
- **Category Tree Logic** — the chosen nodes' closures, grouped by tree: `Cat: A > B > C; Brand: X > Y; Platform: …`.
- **Proposed Tags Applied** — the flat union of all tags written to the product (what the closures add up to).
- **Confidence (0-100)** — cell **color-filled**: **red 0–33 · yellow 34–66 · green 67–100**.

## Confidence score
The classifier sets `confidence` (0–100) per product in `decisions.json`, on this scale:
anchor-confirmed deep leaf **90–100** · strong single structured signal (facet/spec) **75–89** ·
inferred from title/description **50–74** · fallback placement **25–49** · review **<25**.
If absent, `build_report.py` computes a deterministic proxy (existing-anchor overlap + facet + fallback flag).

## One workbook per run
- **Targeted run** (`build_report.py --store <key>`): one tab, filename `<store>-<YYYY-MM-DD>-categorization.xlsx`.
- **Weekly run** (`build_report.py --week <week>`, no `--store`): one workbook, **one tab per store**,
  filename `categorization-weekly-<YYYY-MM-DD>.xlsx`.

## Delivery — Drive for Desktop, NOT the MCP connector
The engine **writes the `.xlsx` into the Google-Drive-for-Desktop synced folder** and Drive uploads it.
Path = `config.report_dir()` → env `PCS_REPORT_DIR`, default `G:\My Drive\Claude Shopify Categorization Reviews`
(Drive folder id `1xteTZd7A1GRIHOq5dABz4BECgOk6LHuW`). An audit copy is also written under `runs/<week>/`.
Drive for Desktop (installed at `C:\Program Files\Google\Drive File Stream`) **must be running** for the
cron/weekly run; if the folder is missing, the script keeps the audit copy and prints how to deliver it.

**Do not route the workbook through the MCP Drive connector.** Proven limits (2026-06-29): `create_file` is
inline-only — a binary `.xlsx` is ~96k tokens of base64 (far over the per-message ceiling), a full multi-row
sheet as text is ~67k tokens (also over), and the connector **cannot create tabs or cell colors** at all. The
connector is only for *small text* (e.g. the review-queue Doc).

## Dependency
`build_report.py` needs **`xlsxwriter`** (for colors/tabs). If it's missing, the script degrades to a single
stacked CSV (no colors, no tabs) and says so — install `xlsxwriter` to restore the real workbook.
