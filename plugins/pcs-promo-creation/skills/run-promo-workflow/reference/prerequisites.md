# Prerequisites

This workflow chains three components. The two sibling skills are markdown and
ship in this marketplace; the Kit Builder is a separate Python CLI; Jira needs
the Atlassian MCP connector.

## 1. Kit Builder `kb` — prebuilt `kb.exe` binary (kit stages, Steps 3–5)

The kit stage runs the real Kit Builder engine. As of **v0.5.22** it ships as a
**prebuilt headless Windows binary `kb.exe`** (attached to every Release next to
the GUI `PCSKitBuilderLite.exe`), so Windows operators need **no Python / pip /
Git**. The repo is private, so fetching `kb.exe` uses the `.env` GitHub token —
the full playbook is `reference/kb-binary.md`.

**Settle this at Step 0, before parsing** — don't defer the install to the kit
stage. Resolve the **kit capability** in this order:

1. **`.\kb.exe` already present** → `.\kb.exe --version`; if **≥ 0.5.22**, kit
   stages are **ENABLED** (no token needed). (`kb.exe --version` is a real check
   as of 0.5.22 — earlier versions had no `--version` flag.) If older, treat as
   missing and go to step 2.
2. **Missing/old AND a `.env` token is in the folder** → **fetch `kb.exe` now**
   via the GitHub REST API + the `.env` token (`reference/kb-binary.md`). The
   token's presence is the go-ahead — **fetch it immediately, no Y/N** — then
   re-check `--version`. Kit stages **ENABLED**. Manual fallback: download
   `kb.exe` from the Release page in a browser and drop it in the folder.
3. **Missing/old AND no `.env`/token** → don't stop the run. Tell the operator to
   ask their admin for the GitHub token `.env` file (drop it in this folder and
   re-run) **if** they want kit building, and offer to **continue without it** —
   deck parsing and the Jira tasks still work; the kit stages (Steps 3–5) are
   skipped. This is **Gate 0** (`reference/pipeline-and-gates.md`).
4. **Non-Windows execution environment** (the binary can't run, e.g. a Linux
   sandbox) → install from source instead — `winget install Python.Python.3.12`
   then `pip install --upgrade git+https://github.com/PCSNathanHarris/pcs-kit-builder-lite.git`
   — and call `kb` (not `.\kb.exe`). Verify with `kb --version` ≥ 0.5.22.

`kb.exe` **does not auto-update** — re-fetch when a new tag ships; the Step-0
`--version` gate is the trigger.

## 2. Sibling plugins (required for Steps 1 and 6)

- **`pcs-promo-parser`** — provides the `parse-promo-deck` skill (Step 1).
- **`pcs-jira-task-builder`** — provides the `create-jira-promotions` skill
  (Step 6).

Both ship in the `pcs-tools` marketplace, so a teammate who added the
marketplace can `/plugin install` them. Confirm they're installed; if not,
point the operator to the Team-Install-SOP.

## 3. Atlassian MCP connector (required for Step 6 only)

The Jira stage creates Tasks only through the user's installed **Atlassian MCP
connector** (tools like `getVisibleJiraProjects`, `createJiraIssue`). It must
be configured and authenticated against the PCS Jira instance. You do **not**
need it until Step 6, so don't block the earlier stages on it — but warn early
if it's obviously absent so the operator can set it up before they get there.

## 4. Drag-and-drop upload artifact (preferred, not required)

The doc-request steps surface the inline **drag-and-drop file-upload artifact**
via the Imagine/visualize widget tools (`mcp__visualize__read_me` +
`mcp__visualize__show_widget`) — standard in the Cowork chat. If those tools
aren't available in the session, the workflow falls back to a plain-text upload
request, so this is preferred, not a hard requirement. See
`reference/upload-widget.md`.

## Operator profile

This full pipeline is meant for a few semi-technical operators. The one-time
`kb` install is the only developer-style step; the rest is plugin installs and
an Atlassian login. See the Team-Install-SOP for the step-by-step.
