# Pipeline and gates

The workflow is a straight line with a human Yes/No before each main stage.
You never advance without an explicit affirmative typed by the operator. `N`
(or any non-affirmative answer) ends the run **cleanly**: keep every file
produced so far, print the session folder, and stop.

A **validation pass** (`reference/validation.md`) runs immediately before each
gate — its `⚠️` findings are folded into that gate's prompt so the operator
decides with full information. Validation auto-corrects only safe things and
never answers a gate itself.

## Gate sequence

| # | Where | Prompt (ask verbatim, fill the `<…>`) | On `N` |
|---|-------|----------------------------------------|--------|
| 0 | Step 0, only if `kb` must be installed/upgraded | `kb <version?> needs installing/upgrading to >= 0.5.19. Run the pip install now? (Y/N)` | Stop; show manual install steps and exit. |
| 4b-scale | Step 4b, only if > ~300 kits | `That's <N> kits to title — generate all, do the first <K>, or stop? (All / First N / Stop)` | Stop, or title only the first N, per the answer. |
| 1 | Step 1, after uploads | `Parse this <vendor?> deck now? (Y/N)` | Stop; nothing parsed. |
| 2 | Step 2, after parse + cheat-sheet fill | `Promo list looks right — continue to the Kit Builder? (Y/N)` | Stop; parser CSVs remain in `Promo Parsed Output/`. |
| 3 | Step 3, after the NetSuite export is uploaded | `Got the NetSuite export — build the NS imports now? (Y/N)` | Stop; DECODE + parser CSVs remain. |
| img | Step 4, before building | `Compose kit images now? This can take many minutes on a large deck. (Y/N)` | Build with `--no-images` (NS CSVs only, no ZIP). This gate does **not** end the run — it only toggles image composition. |
| 4 | Step 5, after the kit build | `NS imports are ready. Continue to Jira task creation? (Y/N)` | Stop; NS CSVs ready to import; Jira can be run later. |
| Jira project | Step 6 (owned by `create-jira-promotions`) | Its own numbered project picker; **PAT** default | — |
| PROM | Step 6 (owned by `create-jira-promotions`) | Type `WRITE TO PROM` to target production | Aborts the Jira writes. |
| 5 | Step 6, just before any Jira writes | `Create <N> Jira task(s) in <PROJECT>? (Y/N)` | Abort writes; no Tasks created. |

## Rules

- The `img` gate is the only one whose `N` does not stop the run — it just
  passes `--no-images`.
- Gates 1–5 are sequential hard stops. Treat "maybe", silence, or anything
  that isn't a clear yes as **No**.
- The Jira **project picker** and **`WRITE TO PROM`** gates belong to the
  `create-jira-promotions` skill. Do not duplicate, pre-answer, or weaken
  them. Gate 5 is an *additional* orchestrator confirmation layered on top,
  not a replacement.
- On any stop, print: `Stopped at <stage>. Session folder: <path>. Re-run
  /run-promo-workflow to continue, or pick up the outputs manually.`
