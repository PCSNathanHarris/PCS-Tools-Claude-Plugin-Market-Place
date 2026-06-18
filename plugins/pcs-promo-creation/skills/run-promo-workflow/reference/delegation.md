# Delegation — running the sibling skills

This skill is an orchestrator. The parse and Jira stages are owned by their
own skills, which ship in this same marketplace and are installed alongside
this one. **Run them; don't re-implement them.** Their `reference/*.md` files
are the source of truth for their behavior — defer to them, don't duplicate
their rules here.

## Stage 1 — `parse-promo-deck` (plugin `pcs-promo-parser`)

Execute the `parse-promo-deck` workflow for the uploaded deck:

- Let it own **vendor detection, quarter/year determination, page
  classification, and its own per-page prompts** (e.g. Crescent confirmation).
- Have it write into the working directory; it creates the session folder
  `./Parsed Decks/<Vendor>/<Vendor>-<QN>-<YYYY>-<MM-DD>[_NN]/` with a
  `Promo Parsed Output/` subfolder. **Capture the session dir and the parsed
  output dir** (`<session>/Promo Parsed Output/`) — those are the run paths for
  every later stage.
- Layer the **cheat-sheet price fallback** on top per `reference/cheat-sheet.md`
  (consult the cheat sheet whenever the deck yields no price for a paid SKU).
- Do not pre-empt its vendor/quarter logic with your own guesses; if you need
  the vendor for a prompt before it's detected, say "this deck" until the
  parser reports it.

After it finishes, the **parsed output dir** holds the Stage 1 outputs (each
written **only when it has rows**; `*-Parser-Audit.csv` is always present and
lists the counts):
`*-Promo-List.csv`, `*-NLP-Sheet.csv`, `*-RSA-Kits.csv`, `*-RSA-NLP.csv`,
`*-Needs-Pricing.csv`, `*-Other-Promotions.csv`, `*-Non-Included.csv`,
`*-Parser-Audit.csv`, and (when there are review items) `*-For-Review.xlsx`.

## Stage 3 — `create-jira-promotions` (plugin `pcs-jira-task-builder`)

Execute the `create-jira-promotions` workflow pointed at the **parsed output
dir** (`<session>/Promo Parsed Output/`) — that's exactly the "parser output
directory" that skill asks for.

Its gates are authoritative and must run exactly as it defines them:

- **Project target first**, PAT default.
- **PROM requires the literal `WRITE TO PROM`** typed by the human. Never
  pre-answer, soften, or bypass it on any file's behalf.
- **Per-row RSA / Non-Included / Other-Promotions review** stays as that skill
  defines it (v0.2.0 adds per-promo review of `*-Other-Promotions.csv`).
- It reads the parser CSVs (hyphen-named, e.g. `Milwaukee-Q3-2026-Promo-List.csv`)
  from the `Promo Parsed Output/` subfolder. The Kit Builder's outputs live in
  the sibling `NetSuite Import Files/` folder (underscore-named,
  `milwaukee_q3_2026_kit_create.csv`), so they aren't even in the directory its
  globs scan.

The **only** thing this orchestrator adds is a final confirmation immediately
before any writes (Gate 5 in `reference/pipeline-and-gates.md`):
`Create <N> Jira task(s) in <PROJECT>? (Y/N)`. That is an extra safety layer,
never a replacement for the skill's own gates.

## If a sibling skill isn't installed

Stop and tell the operator which plugin is missing and how to install it
(`/plugin install pcs-promo-parser` or `/plugin install pcs-jira-task-builder`
from the `pcs-tools` marketplace). Do not attempt to reproduce the missing
stage by hand.
