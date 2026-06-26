# Per-store lessons protocol

Each store has a lessons file that **grows over time** and makes future runs smarter. It is the memory of
how this store's catalog maps to its category tree.

- **Path**: `<data_dir>/lessons-learned/<store-key>.md` (use the **key**, e.g. `the-milwaukee-store.md`,
  `knaack-store.md`, `toolup-my-tool-store.md`).
- **Read** it at the start of each store's run (step 1a) and apply what it says.
- **Append** to it at the end (step 1g). Append-only — never delete prior lessons; refine by adding a newer,
  more specific note if an old heuristic proved wrong.

## What to record (concise, high-signal)
- **Run header**: `## <week> (<date>)` then a one-line count summary
  (`classified=N, NIV2 removed=N, review=N, new categories=N`).
- **Keyword → category mappings** you relied on — the reusable ones, e.g.
  `"impact driver" / "impact wrench" → Impact Drivers`, `"hole saw" → Hole Saws (under Drilling)`.
- **Vendor/title quirks** specific to this store — e.g. a vendor whose titles omit the tool type, a series
  name that implies a category, a line of products that looks like one category but belongs in another.
- **Ambiguous calls + how you resolved them** — so the next run is consistent (e.g. "bare-tool vs kit wording
  doesn't change category here"; "X always goes under Y not Z because …").
- **Review reasons** that recur — if many items fail for the same missing category, note it (a human may add
  the collection, after which they'll auto-place).

## What NOT to put here
- No product dumps or full candidate lists (those live in `runs/<week>/<slug>/`).
- No secrets, tokens, or PII.
- Keep it readable — this file is loaded into context every run, so favor durable heuristics over noise.
  If it grows large, consolidate older run headers into a compact "established heuristics" section at top.
