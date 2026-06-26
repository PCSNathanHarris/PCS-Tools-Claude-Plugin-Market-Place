# Confidence & the Drive review queue

## Be decisive
The routine is autonomous — **try hard to place every item yourself**. Most products are placeable from
vendor + title + description. Only send an item to review when you genuinely cannot pick a correct category.

## Confidence levels (set in `decisions.json`)
- **high** — title/description clearly name the category or an unambiguous synonym. Write it.
- **medium** — strong inference from description/vendor even if the exact word isn't present. Write it.
- **low** — you're guessing, or torn between categories in *different* subtrees with no deciding evidence.
  Treat as review (set `confidence: "low"` or `review: true`).

## What lands in the review queue
`apply_run.py` routes an item to `review-queue.json` when **any** of:
- `review: true`, or `confidence: "low"`, or no `category_tag` given;
- the chosen `category_tag` is **not** in the store's category tree (typo / invented / wrong store).

Review items are **not written** — they retain `New Item V2` and reappear in the next run (e.g. after a new
category is added, or the lessons file improves placement).

## Drive upload (step 1f) — as a Google Doc
Upload a copy of the review queue to the shared Drive folder so a human can resolve the hard cases.
- **Tool**: `mcp__310c6af1-2764-468c-99d5-8035b95250e6__create_file`
- **`parentId`**: `1xteTZd7A1GRIHOq5dABz4BECgOk6LHuW`  (the review folder)
- **`title`**: **`<store-key>-<YYYY-MM-DD>-review`** — store + run date (e.g. `weather-guard-store-2026-06-26-review`)
- **`contentMimeType`**: `text/plain`, and **omit** `disableConversionToGoogleType` so Drive converts the
  upload into a **Google Doc** (the deliverable must be a Doc, not a `.md`/`.txt` file).
- **`textContent`**: a clean, readable list (no markdown tables) — per item: product title, id, vendor, and the
  reason it couldn't be placed. Group by reason where helpful.

Skip the upload when there are **0** review items (just note "0 to review" in the summary).

## Local backup (always)
`review-queue.json` in the run dir is the canonical local backup and is written regardless. **If the Drive
MCP is unavailable or `create_file` fails: do not retry endlessly and do not route around it** — keep the
local backup, note "Drive upload failed — local backup at <path>" in the run summary, and continue. The
Drive copy is a convenience for humans; the local file is the source of truth.
