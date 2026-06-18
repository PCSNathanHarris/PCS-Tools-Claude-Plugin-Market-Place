# Kit stage — DECODE round-trip + NS imports

The kit stage drives the real Kit Builder engine via the `kb` CLI. It uses the
session subfolders from `SKILL.md` Step 0:
- **parsed output dir** = `<session>/Promo Parsed Output/` — the parser CSVs
  (read the Promo-List from here).
- **NS imports dir** = `<session>/NetSuite Import Files/` — the NS export, the
  build CSVs, and `decode_blocks.txt` go here.
- **images dir** = `<session>/Images/` — the composite-image ZIP.

The prefix is `<vendor>_q<N>_<YYYY>` (lowercase, underscores — e.g.
`milwaukee_q3_2026`). **Quote every path — the folder names contain spaces.**

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
  --skus "<parsed output dir>/<Vendor>-<QN>-<YYYY>-Promo-List.csv" \
  --field vendorname \
  --out  "<NS imports dir>/decode_blocks.txt"
```
- `decode-formula` accepts the Promo-List CSV directly and pulls the unique
  vendor SKUs from it.
- Long SKU lists are split into multiple blocks (250 values each). **Present
  every block as a copy-paste artifact** (see "Presenting the DECODE" below);
  the operator pastes each into the **Formula (Numeric)** filter as separate
  criteria.
- Then prompt them to upload the NetSuite export (`.xls` SpreadsheetML or
  `.csv`); save it into the **NS imports dir**.

`decode_blocks.txt` is only for the operator's paste step — it is **not** an
input to `build-imports` (the build auto-derives what it needs from the NS
export itself).

## Presenting the DECODE (copy-paste artifact)

**Always** show the DECODE block(s) as a copy-paste artifact in chat — not just
as a file or an inline mention — so the operator can grab each block in one
click:

- Render with `mcp__visualize__show_widget` (HTML mode): **one selectable
  monospace code box per DECODE block**, each with its own **Copy** button
  (`navigator.clipboard.writeText`). Label the boxes `Block 1 of N`, … when
  there's more than one. Keep the explanatory text (where to paste, one block
  per Formula (Numeric) criterion) in your normal chat message — the widget
  holds only the block(s) + Copy buttons.
- **Also** keep `decode_blocks.txt` in the **NS imports dir** as a backup copy.
- **Fallback:** if the visualize widget tools aren't available, print each block
  as its own fenced ``` code block ``` in chat (still copy-pasteable) — never
  make the operator open the file to copy it.

This is the same "render an artifact in chat" convention as the upload widget
(`reference/upload-widget.md`), just for output the operator copies **out**
rather than files they drop **in**.

## Step 4 — Build NS imports

Run the build **always with `--blank-titles --no-images`** (Claude writes the
titles in Step 4b; images are composed locally in "Composing the kit images"
below — Cowork's sandbox cannot reach NetSuite's image host, so the build never
composes here):

```
kb build-imports \
  --promo-list "<parsed output dir>/<Vendor>-<QN>-<YYYY>-Promo-List.csv" \
  --ns-export  "<NS imports dir>/<uploaded NS export file>" \
  --out-dir    "<NS imports dir>" \
  --prefix     "<vendor>_q<N>_<YYYY>" \
  --blank-titles --no-images
```

Requires `kb >= 0.5.21`. `--blank-titles` leaves Page Title + Detailed
Description empty (you fill them in Step 4b); `--no-images` skips composition
(done locally — see below).

Outputs land in the **NS imports dir**:
- `<prefix>_kit_create.csv` — NEW kits to create in NetSuite.
- `<prefix>_kits_existing.csv` — already-existing kits to update.
- `<prefix>_kit_create_RSA.csv` / `<prefix>_kits_existing_RSA.csv` — present
  only when RSA kits are mixed in.
- `<prefix>_kit_images.zip` — composite images, produced by the local
  images-only step below **into the images dir** (not by this build).

## Surfacing the result

`build-imports` prints a summary block. Relay to the operator:
- New kits / Existing kits counts.
- The create/existing CSV paths.
- Images: `<N> composed` or `skipped (--no-images)`.
- Any `vendor SKU(s) not yet built in NetSuite` warning — these are SKUs the
  NS search didn't return (often not yet set up in NetSuite). List the first
  few so the operator can chase them.

## Composing the kit images (run locally — outside Cowork)

Building the image ZIP means downloading each member's product image from
NetSuite's image host and stitching them. **That download only works from the
operator's own machine — Cowork's sandbox proxy is rejected by NetSuite (403)** —
so the build above always uses `--no-images`, and the ZIP is produced by a
one-line command the operator runs in **their own terminal**, from the
**session folder**. It writes ONLY the ZIP (no CSVs), so the titles you authored
in Step 4b are never touched, and composite filenames stay keyed to each kit's
image source.

If the operator wants images, give them **both** the macOS and Windows forms,
filled in with this run's actual file names + prefix (don't leave the
placeholders). `cd` to the **session folder** so the relative subfolder paths
resolve, and the ZIP is written into `Images/`:

**macOS (Terminal):**
```
cd "<session dir>"
kb build-imports --promo-list "Promo Parsed Output/<Vendor>-<QN>-<YYYY>-Promo-List.csv" --ns-export "NetSuite Import Files/<NS export file>" --out-dir "Images" --prefix "<vendor>_q<N>_<YYYY>" --images-only
```

**Windows (PowerShell):**
```
cd "<session dir>"
kb build-imports --promo-list "Promo Parsed Output/<Vendor>-<QN>-<YYYY>-Promo-List.csv" --ns-export "NetSuite Import Files/<NS export file>" --out-dir "Images" --prefix "<vendor>_q<N>_<YYYY>" --images-only
```

Requires `kb >= 0.5.21`. Tell them to run it and come back; when
`<prefix>_kit_images.zip` appears in the **images dir**, **give them a link to
the ZIP** and report the composed/failed counts it printed. **Do not attempt to
compose images yourself in Cowork** — the fetch will 403.

## Step 4b — Write the Page Titles & Detailed Descriptions

Because the build ran with `--blank-titles`, the NS Create CSV's **Page Title**
and **Detailed Description** columns are empty. You now write them following
`reference/title-description-rules.md`, using the kit groupings (the create CSV
in the **NS imports dir**), the member source text (the NS export), and
free-vs-paid (the Promo-List in the **parsed output dir**).

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
values, then run a short generated script that loads
`<NS imports dir>/<prefix>_kit_create.csv`, sets Page Title + Detailed
Description on each **lead row** keyed by **CA Link**, and writes the file back
as **UTF-8 with BOM**, leaving every other cell exactly as the Kit Builder wrote
it. Do the same for `<prefix>_kit_create_RSA.csv` if it exists. (Existing-kits CSVs have no Page Title / Detailed Description columns —
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
