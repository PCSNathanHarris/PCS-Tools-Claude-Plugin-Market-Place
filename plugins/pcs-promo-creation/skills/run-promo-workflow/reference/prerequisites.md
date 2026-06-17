# Prerequisites

This workflow chains three components. The two sibling skills are markdown and
ship in this marketplace; the Kit Builder is a separate Python CLI; Jira needs
the Atlassian MCP connector.

## 1. Kit Builder `kb` CLI (required for Steps 3–4)

The kit stage runs the real Kit Builder engine via its command line. The
released **`.exe` is GUI-only and does NOT provide `kb`** — the CLI comes from
the Python package.

**Check (Step 0):**
```
kb --version
```
- Need **>= 0.5.17** (that version added the `--no-images` flag the image gate
  uses).
- If `kb` is missing or the version is older, show the install/upgrade below.

**Install / upgrade (offer to run only after a Y/N confirm):**
```
# Python 3.10+ required first (one time):
winget install Python.Python.3.12

# Install (or upgrade) the Kit Builder CLI:
pip install --upgrade git+https://github.com/PCSNathanHarris/pcs-kit-builder-lite.git
```
Then re-check `kb --version`.

- The `kb` CLI **does not auto-update** like the plugins. Updating is a manual
  `pip install --upgrade …`. Re-check the version at Step 0 each run.
- Never install silently — the operator confirms first.

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

## Operator profile

This full pipeline is meant for a few semi-technical operators. The one-time
`kb` install is the only developer-style step; the rest is plugin installs and
an Atlassian login. See the Team-Install-SOP for the step-by-step.
