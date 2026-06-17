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

After the image gate (`reference/pipeline-and-gates.md`), run — always with
`--blank-titles` (Claude writes the titles/descriptions in Step 4b), and with
`--no-images` when the operator answered **N** to images:

```
kb build-imports \
  --promo-list "<run dir>/<Vendor>-<QN>-<YYYY>-Promo-List.csv" \
  --ns-export  "<run dir>/<uploaded NS export file>" \
  --out-dir    "<run dir>" \
  --prefix     "<vendor>_q<N>_<YYYY>" \
  --blank-titles \
  [--no-images]
```

`--blank-titles` leaves the NS Create CSV's **Page Title** and **Detailed
Description** columns empty — you fill them in Step 4b. Requires `kb >= 0.5.18`.

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

## Step 4b — Write the Page Titles & Detailed Descriptions

Because the build ran with `--blank-titles`, the NS Create CSV's **Page Title**
and **Detailed Description** columns are empty. You now write them following
`reference/title-description-rules.md`, using the kit groupings (create CSV),
the member source text (NS export), and free-vs-paid (promo list).

**Scale gate (always do this first).** Count the kits (lead rows) in the create
CSV. Writing a title + description for every kit is real work, so:
- **≤ ~300 kits:** proceed.
- **> ~300 kits:** stop and tell the operator the count, and ask:
  `That's <N> kits to title — generate all, do the first <K>, or stop? (All / First N / Stop)`.
  A very high count (thousands) usually means the deck over-expanded upstream —
  flag that too, since it may be worth fixing the promo list before titling.

**Then, per kit:** decide the Page Title and Detailed Description with judgment
per the rules. Keep brand spelling and repeated-SKU descriptors consistent
across the run.

**Write them back in place.** Don't hand-edit cells one by one — decide the
values, then run a short generated script that loads `<prefix>_kit_create.csv`,
sets Page Title + Detailed Description on each **lead row** keyed by **CA Link**,
and writes the file back as **UTF-8 with BOM**, leaving every other cell exactly
as the Kit Builder wrote it. Do the same for `<prefix>_kit_create_RSA.csv` if it
exists. (Existing-kits CSVs have no Page Title / Detailed Description columns —
leave them alone.)

**Self-check** before Gate 4: every lead row now has a non-empty Page Title
(≤ 80 chars) and a Detailed Description containing the `KEY FEATURES:` and
`INCLUDES:` sections; no FREE/paid mislabels; valid HTML.

## Notes

- `--no-images` writes the NS CSVs and **no** ZIP — it does not change the
  CSVs in any way. Use it whenever the operator declines the (slow,
  network-bound) image composition.
- `--blank-titles` skips only the title/description generation; the kit
  assembly, create-vs-existing split, and all other columns are unchanged.
- The Kit Builder already filters image composition to NEW kits only, so
  composing is proportional to new-kit count, not total kits.
- Do not hand-compute the NS CSV structure — the CLI is the source of truth.
  You only author the two title/description columns.
