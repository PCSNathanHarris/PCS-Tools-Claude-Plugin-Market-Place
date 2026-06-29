# Lessons & repo sync

## Two lesson docs
- **`<data_dir>/lessons-learned/<store-key>.md`** — store-specific: keyword→category mappings, that store's
  quirks, ambiguous calls and how they were resolved.
- **`<data_dir>/lessons-learned/PROJECT-LESSONS.md`** — project-wide / cross-store lessons (things that
  generalize). Canonical *rules* still live in `universal-rules.md`; this is the running log.

## Form them AFTER the run
Lessons are written/updated at the **end** of a store's work (SKILL step 1h) and the project log at step 2 —
**after** all scanning and classification, so issues surfaced during the run are captured. Update the store md
every run; append to `PROJECT-LESSONS.md` only when a lesson is genuinely cross-store.

## Auto-sync to the repo (weekly, gateless)
Step 2 runs **`python sync_repo.py --week <week> [--note "<one-line summary>"]`**. It:
1. Finds the marketplace repo via `config.repo_dir()` (`PCS_PLUGIN_REPO`). Absent → logs + skips (lessons
   stay local); never errors.
2. Copies changed lesson `.md` files into `plugins/pcs-categorization/lessons-learned/`.
3. If anything changed, writes **`change-reports/<YYYY-MM-DD>-weekly.txt`** (run date · changed files ·
   diffstat), then **scoped** `git add` of `lessons-learned/` + `change-reports/` **only** → commit →
   `pull --rebase` → push. **Never stages code or any other path.**
4. Any git failure → logged, commit left local, run continues (fail-safe).

This is the **only** git write the pipeline makes (see `write-scope.md`). It is gateless — no prompt, no
approval. Review the pushed change reports after the fact.

`--dry-run` reports which lesson files would change and writes nothing — use it to preview.
