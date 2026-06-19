# Kit stage — DECODE round-trip + NS imports

The kit stage drives the real Kit Builder engine via the `kb.exe` CLI binary
(Windows; fetched per `reference/kb-binary.md`). It uses the
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
2. Operator opens the **Promo Kit Support** saved search —
   `https://855722.app.netsuite.com/app/common/search/search.nl?cu=T&e=T&id=16021`
   (saved search 16021) — pastes the DECODE in, runs it, exports the results.
3. Operator uploads that export; the Kit Builder consumes it.

## Step 3 — DECODE formula

```
.\kb.exe decode-formula \
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
- **Give them the saved-search link** so they don't have to hunt for it:
  [Promo Kit Support – Kit Builder](https://855722.app.netsuite.com/app/common/search/search.nl?cu=T&e=T&id=16021)
  (saved search 16021). Surface it in the chat message **and** inside the DECODE
  artifact (below).
- Then prompt them to upload the NetSuite export (`.xls` SpreadsheetML or
  `.csv`); save it into the **NS imports dir**.

`decode_blocks.txt` is only for the operator's paste step — it is **not** an
input to `build-imports` (the build auto-derives what it needs from the NS
export itself).

## Presenting the DECODE (copy-paste artifact)

**Always** show the DECODE block(s) as a copy-paste artifact in chat — not just
as a file or an inline mention — so the operator can grab each block in one
click:

- Render with `mcp__visualize__show_widget` (HTML mode). At the **top** of the
  widget put a clickable link to the saved search, above the blocks, so it rides
  with what the operator is copying:
  `<a href="https://855722.app.netsuite.com/app/common/search/search.nl?cu=T&amp;e=T&amp;id=16021" target="_blank" rel="noopener">Open Promo Kit Support search</a>`
  (escape `&` as `&amp;` in the href). Below it, render **one selectable monospace
  code box per DECODE block**, each with its own **Copy** button
  (`navigator.clipboard.writeText`). Label the boxes `Block 1 of N`, … when
  there's more than one. Keep the rest of the explanatory text (where to paste,
  one block per Formula (Numeric) criterion) in your normal chat message.
- **Also** keep `decode_blocks.txt` in the **NS imports dir** as a backup copy.
- **Fallback:** if the visualize widget tools aren't available, print each block
  as its own fenced ``` code block ``` in chat (still copy-pasteable) and include
  the saved-search link as a plain line —
  `https://855722.app.netsuite.com/app/common/search/search.nl?cu=T&e=T&id=16021`
  — never make the operator open the file to copy it.

This is the same "render an artifact in chat" convention as the upload widget
(`reference/upload-widget.md`), just for output the operator copies **out**
rather than files they drop **in**.

## Unbuilt SKUs — capture for later resume

The Step-3 coverage diff (validation Stage 2) lists Promo-List SKUs the NS export
didn't return — items **not yet built in NetSuite**. Those kits can't build now,
and building the items often takes a while and is picked up in a **separate, later
chat**. So don't just warn — save a self-contained "resume kit" to disk. When the
diff finds unbuilt SKUs, produce **all** of:

1. **Unbuilt-SKU list** — the SKUs to go build in NetSuite. Match the engine
   exactly: a member is unbuilt iff its Promo-List slot SKU (plain `.strip()`,
   **case-sensitive, hyphens/spaces preserved** — NOT the parser's
   uppercase/hyphen-stripping key) is **not** present in the NS export's
   **`Vendor Name`** column. Write the unique unbuilt SKUs, one per line, to
   `<NS imports dir>/<prefix>_unbuilt_skus.txt`.
2. **Unbuilt DECODE** — so the operator can re-query just those items once built:
   ```
   .\kb.exe decode-formula --skus "<NS imports dir>/<prefix>_unbuilt_skus.txt" \
     --field vendorname --out "<NS imports dir>/<prefix>_unbuilt_decode_blocks.txt"
   ```
   **Present it as a copy-paste artifact** (same widget as "Presenting the DECODE",
   with the Promo Kit Support saved-search link at the top). Note in chat that this
   DECODE returns **only** the newly-built items — to rebuild a kit you'll also need
   its already-built companion SKUs in the export (re-run the original
   `decode_blocks.txt`, or merge), since this list is intentionally just the unbuilt
   ones.
3. **Unbuilt-SKU Promo-List** — the kits to redo. Filter the Promo-List to **every
   row whose `Promo Name` group contains at least one unbuilt slot SKU** (keep whole
   kits; all 27 columns; `utf-8-sig` + CRLF) and write it to
   `<parsed output dir>/<Vendor>-<QN>-<YYYY>-Unbuilt-Promo-List.csv`. It's a valid
   Promo-List, so a later run feeds it straight to `build-imports --promo-list …`.
4. **Resume README** — write `<session dir>/Unbuilt-SKUs-README.txt` so a cold
   future session needs nothing from this chat. Include: the unbuilt SKU count +
   list; the saved-search link
   (`https://855722.app.netsuite.com/app/common/search/search.nl?cu=T&e=T&id=16021`);
   and the resume steps — *(1) build these SKUs in NetSuite; (2) paste
   `<prefix>_unbuilt_decode_blocks.txt` into the Promo Kit Support search to
   confirm/fetch them (plus the original `decode_blocks.txt` for their companions);
   (3) export; (4) re-run the kit build against the `…-Unbuilt-Promo-List.csv`*, e.g.
   `kb.exe build-imports --promo-list "<…Unbuilt-Promo-List.csv>" --ns-export "<new export>" --out-dir "<dir>" --prefix "<prefix>_unbuilt" --blank-titles --no-images`.

Surface a one-line summary in chat and the run report (unbuilt SKU + kit counts and
the saved file paths). **If the diff found no unbuilt SKUs, skip this whole section.**

## Step 4 — Build NS imports

Run the build **always with `--blank-titles --no-images`** (Claude writes the
titles in Step 4b; images are composed locally in "Composing the kit images"
below — Cowork's sandbox cannot reach NetSuite's image host, so the build never
composes here):

```
.\kb.exe build-imports \
  --promo-list "<parsed output dir>/<Vendor>-<QN>-<YYYY>-Promo-List.csv" \
  --ns-export  "<NS imports dir>/<uploaded NS export file>" \
  --out-dir    "<NS imports dir>" \
  --prefix     "<vendor>_q<N>_<YYYY>" \
  --blank-titles --no-images
```

Requires `kb.exe >= 0.5.22`. `--blank-titles` leaves Page Title + Detailed
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

If the operator wants images, give them the form for their OS, filled in with
this run's actual file names + prefix (don't leave the placeholders). `cd` to the
**session folder** so the relative subfolder paths resolve, and the ZIP is
written into `Images/`:

**Windows (PowerShell)** — uses the prebuilt `kb.exe` in the session folder (no Python):
```
cd "<session dir>"
.\kb.exe build-imports --promo-list "Promo Parsed Output/<Vendor>-<QN>-<YYYY>-Promo-List.csv" --ns-export "NetSuite Import Files/<NS export file>" --out-dir "Images" --prefix "<vendor>_q<N>_<YYYY>" --images-only
```

**macOS (Terminal)** — there is **no `kb.exe` on Mac**; use the source `kb`
(install per `reference/prerequisites.md` §1 fallback):
```
cd "<session dir>"
kb build-imports --promo-list "Promo Parsed Output/<Vendor>-<QN>-<YYYY>-Promo-List.csv" --ns-export "NetSuite Import Files/<NS export file>" --out-dir "Images" --prefix "<vendor>_q<N>_<YYYY>" --images-only
```

Requires `kb.exe >= 0.5.22` (Windows) or source `kb >= 0.5.22` (macOS). Tell them to run it and come back; when
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

**Self-check** before Gate 4 (full list in `reference/title-description-rules.md`
→ "Title self-check"): every lead row now has a non-empty Page Title that is
**≤ 90 chars (hard max 95)**, leads with Brand + main paid SKU, uses a specific
product noun, carries every member SKU with `FREE` on each free good only, and has
no `(Bare)` / `Tool Only` / `[PCE …]` / empty-paren artifacts; and a Detailed
Description containing the `KEY FEATURES:` and `INCLUDES:` sections; valid HTML.

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
