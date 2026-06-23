# Prerequisites

This workflow chains three components. The two sibling skills are markdown and
ship in this marketplace; the Kit Builder is a separate Python CLI; Jira needs
the Atlassian MCP connector.

## 1. Kit Builder `kb` — prebuilt CLI binary (`kb.exe` / `kb-macos`) (kit stages, Steps 3–5)

The kit stage runs the real Kit Builder engine. It ships as a **prebuilt headless
binary** — **`kb.exe`** (Windows, v0.5.22+) and **`kb-macos`** (macOS, v0.5.24+) —
attached to every Release next to the GUI `PCSKitBuilderLite.exe`, so operators need
**no Python / pip / Git**. The repo is private, so fetching uses the GitHub token —
the full playbook is `reference/kb-binary.md`.

**Settle this at Step 0, before parsing** — don't defer the install to the kit
stage. Resolve the **kit capability** in this order:

1. **The platform binary already present** (`.\kb.exe` on Windows / `./kb-macos` on
   macOS) → run `--version`; if **≥ 0.5.24**, kit stages are **ENABLED** (no token
   needed). If older/missing, go to step 2.
2. **Missing/old AND a token file is in the folder** → **fetch the platform binary
   now** — `kb.exe` (Windows) or `kb-macos` (macOS; then `chmod +x` + clear
   quarantine) — via the GitHub REST API + token (`reference/kb-binary.md`). The
   token's presence is the go-ahead — **fetch immediately, no Y/N** — then re-check
   `--version`. Kit stages **ENABLED**. Manual fallback: download it from the Release
   page and drop it in the folder.
3. **Missing/old AND no `.env`/token** → don't stop the run. Tell the operator to
   ask their admin for the GitHub token `.env` file (drop it in this folder and
   re-run) **if** they want kit building, and offer to **continue without it** —
   deck parsing and the Jira tasks still work; the kit stages (Steps 3–5) are
   skipped. This is **Gate 0** (`reference/pipeline-and-gates.md`).
4. **macOS** → fetch the **`kb-macos`** binary (same token flow as `kb.exe`; then
   `chmod +x` + `xattr -dr com.apple.quarantine`), and call `./kb-macos`. See
   `reference/kb-binary.md` → "macOS". (Intel Macs: the binary is arm64 — use the
   source install in step 5 instead.)
5. **Linux execution environment** (Claude's sandbox — no binary) → install from
   source. Python 3 is normally already present (else `apt-get install -y python3
   python3-pip`). The repo is **private**, so **inject the token** (per
   `reference/kb-binary.md` → *Find + read the token*) — the public-form URL 404s:
   ```bash
   pip install --upgrade "git+https://${tok}@github.com/PCSNathanHarris/pcs-kit-builder-lite.git"
   # add --break-system-packages if pip refuses (PEP 668); redact pip's output so the
   # token embedded in the URL is never printed
   ```
   Then call `kb` (lands on PATH, e.g. `~/.local/bin/kb`). Verify `kb --version` ≥ 0.5.24.
   (The Cowork sandbox is usually Linux **without poppler** — the parser's PyMuPDF
   fallback renders PDFs there.)

The binaries **do not auto-update** — re-fetch when a new tag ships; the Step-0
`--version` gate is the trigger. **v0.5.24** adds the macOS `kb-macos` binary;
**v0.5.23** fixed duplicate kits from "choose N" multi-pick promos — the Step-0
≥ 0.5.24 gate re-fetches an operator who's behind.

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
