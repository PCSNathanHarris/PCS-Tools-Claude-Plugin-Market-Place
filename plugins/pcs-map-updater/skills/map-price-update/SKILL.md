# MAP Price Update

You are executing the PCS MAP Price Update workflow. This skill merges a
vendor manufacturer MAP sheet with a NetSuite ERP export, validates each
row against purchase pricing and keep-price flags, and produces a
review-ready Excel workbook ready for the monthly MAP update process.

---

## Step 1 — Collect inputs

Ask the user for the following if not already provided:

1. **Manufacturer MAP sheet** — full file path to a CSV, XLS, or XLSX.
   Must contain at minimum a SKU column and a MAP price column.
2. **ERP export** — full file path to a CSV, XLS, or XLSX.
   Must contain `Internal ID`, at least one of `Vendor Name` / `MPN`,
   `Purchase Price`, and `Keep Sales Price`.
3. **Manufacturer primary SKU column** — which column holds the main
   model number / SKU (e.g. `Model #`). Auto-suggest from the file
   headers; default to the best match from:
   `Model #`, `Model#`, `Model`, `SKU`, `MPN`, `Item Number`, `Vendor Name`.
4. **Manufacturer SKU column 2** (optional backup) — a second SKU column
   to try if the primary doesn't match.
5. **Manufacturer SKU column 3** (optional backup) — a third SKU column.
6. **Manufacturer MAP column** — which column holds the MAP price for
   this run. Auto-suggest; default to best match from:
   `Minimum Advertised Price`, `MAP`, `MAP Price`,
   `Minimum Advertised Promo Price`.

Do not proceed until items 1–4 and 6 are confirmed.

---

## Step 2 — Verify dependencies

Before generating the script, check that `pandas` and `openpyxl` are
available:

```bash
python -c "import pandas, openpyxl; print('OK')"
```

If the check fails, install them:

```bash
pip install pandas openpyxl
```

---

## Step 3 — Generate and run the merge script

Write a Python script (`map_price_update.py` in the same directory as
the manufacturer file) that implements the full logic documented in
`reference/column-mapping.md` and `reference/output-spec.md`.

The script must:

1. Read both input files with `pandas` (support CSV, XLS, XLSX).
   - Strip leading/trailing whitespace from all column headers.
   - Use `dtype=str` on read so no values are silently converted.

2. Build ERP lookup maps as described in
   `reference/column-mapping.md#erp-lookup-maps`.

3. For each manufacturer row, run the match cascade in the order
   specified in `reference/column-mapping.md#match-cascade`.

4. Compute all validation flags per
   `reference/column-mapping.md#validation-flags`.

5. Build output rows per the column list in
   `reference/output-spec.md#output-columns`.

6. Write the Excel workbook with the four sheets in
   `reference/output-spec.md#workbook-sheets`.

7. Name the output file per `reference/output-spec.md#file-naming`.

8. Print the summary report defined in
   `reference/output-spec.md#summary-report`.

Run the script with:

```bash
python map_price_update.py
```

---

## Step 4 — Report results

After the script exits successfully, relay the printed summary to the
user and state the full path of the output workbook.

If the script errors, diagnose the issue (column not found, file not
readable, import error, etc.), fix the script, and re-run. Do not ask
the user to intervene unless the input files are genuinely malformed.

---

## Key rules

- Never treat `Dealer`, `Platinum`, `M1`, `M2`, `M3`, or `List Price`
  as a MAP price, even if the user selects them. Warn the user if one
  of those column names is chosen for the MAP field.
- SKU normalization is case-insensitive: always compare uppercase values
  and strip leading apostrophes added by Excel. See
  `reference/column-mapping.md#sku-normalization` for the full rule.
- If both ERP match columns (`Vendor Name` and `MPN`) are absent from
  the ERP file, abort and tell the user which columns are missing.
- Emit the output workbook even if every row is unmatched — the user
  still needs the exceptions sheet.
