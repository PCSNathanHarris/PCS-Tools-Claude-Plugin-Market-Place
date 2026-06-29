"""
sync_repo.py — commit + push lessons-learned and a dated change report to the marketplace repo.

GATELESS, scoped, fail-safe. Runs at the END of a weekly run (SKILL step 2), after all scanning and
classification, so the lessons reflect everything found. The ONLY repo writes are
`plugins/pcs-categorization/lessons-learned/` and `.../change-reports/` — NEVER code. If the repo isn't
present (a machine without it cloned) or any git step fails, it logs and returns cleanly so the
categorization run never breaks. `--dry-run` reports what would change and writes nothing.

Autonomous-run write scope (no human gate — see reference/write-scope.md):
  * Shopify : product TAG operations only (handled in SKILL step 1e).
  * Git     : THIS script — lessons-learned/ + change-reports/ only.
  * Drive   : the report workbook to the project folder (build_report.py).
  Everything else is strictly read-only.
"""

import argparse
import datetime
import filecmp
import shutil
import subprocess
from pathlib import Path

import config

PLUGIN_SUBDIR = Path("plugins/pcs-categorization")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default=None)
    ap.add_argument("--note", default="", help="optional one-line summary of what was learned (from the SKILL)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    today = datetime.date.today().isoformat()
    src = config.data_dir() / "lessons-learned"
    repo = config.repo_dir()
    dst = repo / PLUGIN_SUBDIR / "lessons-learned"
    reports = repo / PLUGIN_SUBDIR / "change-reports"

    if not src.exists() or not any(src.glob("*.md")):
        print(f"[sync] no lessons at {src} — nothing to sync.")
        return
    if not (repo / ".git").exists():
        print(f"[sync] repo not found at {repo} (set PCS_PLUGIN_REPO). Skipping push — lessons stay local at {src}.")
        return

    # which lesson files are new or changed?
    changed = []
    for f in sorted(src.glob("*.md")):
        d = dst / f.name
        if (not d.exists()) or (not filecmp.cmp(f, d, shallow=False)):
            changed.append(f.name)
    if not changed:
        print("[sync] lessons already up to date in the repo — nothing to commit.")
        return

    print(f"[sync] lesson files to update ({len(changed)}): {', '.join(changed)}")
    if a.dry_run:
        print("[sync] --dry-run: no files written, no commit, no push.")
        return

    # 1) copy the changed lessons into the repo
    dst.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    for name in changed:
        shutil.copy2(src / name, dst / name)

    # 2) stage ONLY the lessons dir, capture its diffstat for the change report
    git(repo, "add", (PLUGIN_SUBDIR / "lessons-learned").as_posix())
    stat = (git(repo, "diff", "--cached", "--stat").stdout or "").strip()
    branch = (git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout or "main").strip()

    # 3) write the dated change report (what changed in the repo this run)
    report = reports / f"{today}-weekly.txt"
    lines = ["PCS Categorization — weekly repo change report",
             f"Run date: {today}    Week: {a.week or '(current)'}    Branch: {branch}",
             "",
             f"Lessons updated ({len(changed)}):"]
    lines += [f"  - lessons-learned/{n}" for n in changed]
    if a.note:
        lines += ["", f"Summary: {a.note}"]
    lines += ["", "Diffstat (staged lesson changes):", (stat or "  (none)"),
              "", "Scope: lessons-learned/ + change-reports/ only. No code, no other files."]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 4) stage the report too, then commit (scoped — other dirty files are NOT included)
    git(repo, "add", (PLUGIN_SUBDIR / "change-reports").as_posix())
    msg = f"chore(pcs-categorization): weekly lessons sync {today}"
    c = git(repo, "commit", "-m", msg)
    if c.returncode != 0:
        print("[sync] nothing committed / commit failed:\n" + (c.stdout or "")[-400:] + (c.stderr or "")[-400:])
        return
    print(f"[sync] committed: {msg}")

    # 5) rebase on remote, then push — fail-safe (commit stays local if either fails)
    pull = git(repo, "pull", "--rebase", "origin", branch)
    if pull.returncode != 0:
        git(repo, "rebase", "--abort")
        print("[sync] pull --rebase failed; leaving commit local (pushes next run / by hand):\n" + (pull.stderr or "")[-400:])
        return
    push = git(repo, "push", "origin", branch)
    if push.returncode != 0:
        print("[sync] push failed; commit is local:\n" + (push.stderr or "")[-400:])
        return
    print(f"[sync] pushed lessons + change report to origin/{branch}. Report: change-reports/{today}-weekly.txt")


if __name__ == "__main__":
    main()
