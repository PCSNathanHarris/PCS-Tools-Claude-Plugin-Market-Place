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
- Have it write into the working directory; it creates
  `./parsed-output/<vendor>_<YYYY-MM-DD>/`. **Capture that path** — it is the
  run directory for every later stage.
- Layer the **cheat-sheet price fallback** on top per `reference/cheat-sheet.md`
  (consult the cheat sheet whenever the deck yields no price for a paid SKU).
- Do not pre-empt its vendor/quarter logic with your own guesses; if you need
  the vendor for a prompt before it's detected, say "this deck" until the
  parser reports it.

After it finishes, the run directory holds the Stage 1 CSVs:
`*-Promo-List.csv`, `*-NLP-Sheet.csv`, `*-RSA-Kits.csv`, `*-RSA-NLP.csv`,
`*-Needs-Pricing.csv`, `*-Non-Included.csv`, `*-Parser-Audit.csv`.

## Stage 3 — `create-jira-promotions` (plugin `pcs-jira-task-builder`)

Execute the `create-jira-promotions` workflow pointed at the **run directory**
(the same folder the parser wrote — that's exactly the "parser output
directory" that skill asks for).

Its gates are authoritative and must run exactly as it defines them:

- **Project target first**, PAT default.
- **PROM requires the literal `WRITE TO PROM`** typed by the human. Never
  pre-answer, soften, or bypass it on any file's behalf.
- **Per-row RSA / Non-Included review** stays as that skill defines it.
- It reads the parser CSVs (hyphen-named, e.g. `Milwaukee-Q3-2026-Promo-List.csv`).
  The Kit Builder's outputs in the same folder are underscore-named
  (`milwaukee_q3_2026_kit_create.csv`) and won't collide with its globs.

The **only** thing this orchestrator adds is a final confirmation immediately
before any writes (Gate 5 in `reference/pipeline-and-gates.md`):
`Create <N> Jira task(s) in <PROJECT>? (Y/N)`. That is an extra safety layer,
never a replacement for the skill's own gates.

## If a sibling skill isn't installed

Stop and tell the operator which plugin is missing and how to install it
(`/plugin install pcs-promo-parser` or `/plugin install pcs-jira-task-builder`
from the `pcs-tools` marketplace). Do not attempt to reproduce the missing
stage by hand.
