# Kit stage — DECODE round-trip + NS imports

The kit stage drives the real Kit Builder engine via the `kb` CLI. Run the
commands from the run directory (or pass absolute paths). All paths below use
`<run dir>` = the parser's dated output folder and the prefix
`<vendor>_q<N>_<YYYY>` (lowercase, underscores — e.g. `milwaukee_q3_2026`).

## Why there's a NetSuite round-trip

The Kit Builder needs NetSuite's record for each SKU (internal IDs, links,
descriptions). You get those by running a saved search in NetSuite, filtered
to exactly the promo's SKUs. The **DECODE formula** is how you tell NetSuite
which SKUs to return. So the order is:

1. Generate the DECODE from the parsed Promo-List.
2. Operator pastes it into the NS "Promo Kit Support" saved search, runs it,
   exports the results.
3. Operator uploads that export; the Kit Builder consumes it.

## Step 3 — DECODE formula

```
kb decode-formula \
  --skus "<run dir>/<Vendor>-<QN>-<YYYY>-Promo-List.csv" \
  --field vendorname \
  --out  "<run dir>/decode_blocks.txt"
```
- `decode-formula` accepts the Promo-List CSV directly and pulls the unique
  vendor SKUs from it.
- Long SKU lists are split into multiple blocks (250 values each). Show every
  block; tell the operator to paste each into the **Formula (Numeric)** filter
  as separate criteria.
- Then prompt them to upload the NetSuite export (`.xls` SpreadsheetML or
  `.csv`) into the run directory.

`decode_blocks.txt` is only for the operator's paste step — it is **not** an
input to `build-imports` (the build auto-derives what it needs from the NS
export itself).

## Step 4 — Build NS imports

After the image gate (`reference/pipeline-and-gates.md`), run — appending
`--no-images` when the operator answered **N** to images:

```
kb build-imports \
  --promo-list "<run dir>/<Vendor>-<QN>-<YYYY>-Promo-List.csv" \
  --ns-export  "<run dir>/<uploaded NS export file>" \
  --out-dir    "<run dir>" \
  --prefix     "<vendor>_q<N>_<YYYY>" \
  [--no-images]
```

Outputs land in the run directory:
- `<prefix>_kit_create.csv` — NEW kits to create in NetSuite.
- `<prefix>_kits_existing.csv` — already-existing kits to update.
- `<prefix>_kit_create_RSA.csv` / `<prefix>_kits_existing_RSA.csv` — present
  only when RSA kits are mixed in.
- `<prefix>_kit_images.zip` — composite images (omitted when `--no-images`).

## Surfacing the result

`build-imports` prints a summary block. Relay to the operator:
- New kits / Existing kits counts.
- The create/existing CSV paths.
- Images: `<N> composed` or `skipped (--no-images)`.
- Any `vendor SKU(s) not yet built in NetSuite` warning — these are SKUs the
  NS search didn't return (often not yet set up in NetSuite). List the first
  few so the operator can chase them.

## Notes

- `--no-images` writes the NS CSVs and **no** ZIP — it does not change the
  CSVs in any way. Use it whenever the operator declines the (slow,
  network-bound) image composition.
- The Kit Builder already filters image composition to NEW kits only, so
  composing is proportional to new-kit count, not total kits.
- Do not hand-compute any of these outputs. The CLI is the source of truth.
