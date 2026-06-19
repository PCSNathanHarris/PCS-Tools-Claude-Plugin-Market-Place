# Prerequisites

This workflow chains three components. The two sibling skills are markdown and
ship in this marketplace; the Kit Builder is a separate Python CLI; Jira needs
the Atlassian MCP connector.

## 1. Kit Builder `kb` — prebuilt `kb.exe` binary (required for Steps 3–4)

The kit stage runs the real Kit Builder engine. As of **v0.5.22** it ships as a
**prebuilt headless Windows binary `kb.exe`** (attached to every Release next to
the GUI `PCSKitBuilderLite.exe`), so Windows operators need **no Python / pip /
Git**. The repo is private, so fetching `kb.exe` uses the `.env` GitHub token —
the full playbook is `reference/kb-binary.md`.

**Check (Step 0):**
```
.\kb.exe --version
```
- Need **>= 0.5.22**. If `.\kb.exe` is missing from the working folder, fetch it
  from the latest Release with the `.env` token (see `reference/kb-binary.md`),
  then re-check. (`kb.exe --version` is a real, supported check as of 0.5.22 —
  earlier versions had no `--version` flag.)
- `kb.exe` **does not auto-update** — re-fetch when a new tag ships; the Step-0
  `--version` gate is the trigger.

**Get / update `kb.exe` (offer only after a Y/N confirm — never silently):**
- **Primary (Windows):** Claude downloads `kb.exe` from the latest **private**
  Release via the GitHub REST API + the `.env` token (no Python/Git/pip). See
  `reference/kb-binary.md`. Manual fallback: download `kb.exe` from the Release
  page in a browser and drop it in the working folder.
- **Fallback (source / non-Windows):** where the Windows binary can't run (e.g. a
  non-Windows sandbox), install from source — `winget install Python.Python.3.12`
  then `pip install --upgrade git+https://github.com/PCSNathanHarris/pcs-kit-builder-lite.git`
  — and call `kb` (not `.\kb.exe`). Verify with `kb --version` ≥ 0.5.22.

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
