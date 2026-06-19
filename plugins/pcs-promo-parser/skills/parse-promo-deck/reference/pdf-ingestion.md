# Ingesting the deck (PDF → text layer + page images)

How to load a deck's pages before classification/extraction. Two goals:
**never stall on a missing rasteriser**, and **don't spend a full-resolution
vision read on pages that have no promo data**. Accuracy is unchanged — every
page that might hold data still gets a full vision read, and the page **image
stays authority** for SKU/price tables (see SKILL.md "Image vs text authority").

## A. Pull the text layer once (always)

Dump per-page text to `deck_text/p001.txt …` with a small script — it feeds both
the Step 5.5 grounding grep (`reference/verification.md` Layer B) and the page
triage in §C. Use `pypdf` (fallback `pdfminer.six`); PyMuPDF's `page.get_text()`
also works if it's already installed for rendering. **PNG/JPG inputs have no text
layer** — skip this and treat every page as vision-only.

## B. Get page images — robust ladder (stop at the first that works)

1. **Native `Read` (preferred).** Probe once: `Read(file_path=<deck>, pages="1-1")`.
   If it returns the page, use the native tool for the whole deck in **20-page
   chunks** (`"1-20"`, `"21-40"`, …) — it returns the text layer **and** the
   rendered page image together, with no extra rasteriser cost.
2. **PyMuPDF fallback (sandbox-safe).** If the native Read errors (e.g.
   `pdftoppm failed: Command 'pdftoppm' not found` — common in the Cowork **Linux
   sandbox**), render with **PyMuPDF**, which rasterises **in-process with no
   poppler / no system deps**:
   ```bash
   pip install --quiet pymupdf        # or: pip install --break-system-packages --quiet pymupdf
   ```
   ```python
   import fitz                                  # PyMuPDF
   doc = fitz.open(deck_path)
   for i in pages_to_render:                    # 0-indexed; only the pages you need
       pix = doc[i].get_pixmap(dpi=150)         # 150 dpi reads SKUs/prices cleanly
       pix.save(f"deck_pages/p{i+1:03d}.png")
   ```
   Then `Read` the PNGs (Read handles `.png` with no rasteriser). PyMuPDF is fast
   and in-process — render in **one loop**. **Do NOT** revert to the old per-batch
   `pdftoppm` shell workaround (rendering all pages at once there timed out at the
   45 s shell limit and had to be split into page ranges — pure wasted work). If a
   render loop is ever long-running, run it in the **background**, don't fight the
   timeout.
3. **poppler `pdftoppm` (last resort)** only if PyMuPDF cannot be installed.

## C. Triage — skip the full-res read on non-data pages (the token win)

Before the expensive full-resolution vision read, decide per page whether it can
hold promo data, using the **text dump from §A** (and a cheap low-res thumbnail
when the text is too sparse to tell). **Skip the full read only for pages you can
confidently place in a non-data class** per `reference/page-classification.md`:
cover / title, table-of-contents, section dividers, pure brand-marketing,
dealer-info, terms-&-conditions / legal, and blank/empty pages (case #8).

A page is a **skip candidate** only when **all** of these hold:
- no vendor SKU-pattern hits in its text (`reference/vendors/<vendor>.md`),
- no price-table header tokens (e.g. `ITEM #`, `IMAP`, `PROMO IMAP`, `DESCRIPTION`),
- no promo / PCE / date markers (`PCE`, `Online Execution`, `FREE`, `% Off`, and the
  NLP / BMSM / rebate / RSA phrases in `exclusion-markers.md`).

**When in doubt, read it.** A weak text layer is common — SKUs may sit in the text
while the PCE code and dates are baked into the page image — so sparse text must
**never** cause a data page to be skipped. If the text is sparse **and** a low-res
thumbnail shows a table / SKU panel / price grid, treat it as a data page and
full-res read it. Skipping is reserved for pages that are *clearly* non-data.

Every page that survives triage — promo / NLP / RSA / Other-Promotions / ambiguous
— gets the **full vision read**. This is the Balanced policy: cut wasted reads, not
vision on real data. (The image remains authority for the tables you read.)

## D. Record what you skipped

List the triaged-out pages (page number + non-data class) in the run's process
notes, and keep counting **every** page toward `Total Pages` in `Parser-Audit.csv`.
Coverage stays auditable — a reviewer can see exactly which pages were not
vision-read and why. Never silently drop a page that might hold data.
