# Connector Setup Guide (non-technical users)

For each source the user's tier enables: FIRST test whether it already works (a harmless
read call). Only walk them through connecting if it fails. All connecting happens in
claude.ai -> Settings -> Connectors (or the Connectors section in the desktop app) — give
click-path instructions, never terminal commands.

## Claude sessions (every tier — no connector)
Auto-discover transcript roots on their machine and record them in config:
- `%USERPROFILE%\.claude\projects\` (Claude Code sessions — one folder per project)
- `%APPDATA%\Claude\local-agent-mode-sessions\` (Cowork sessions, if present)
Ask which folders on disk hold their working files (their equivalent of project folders)
and record those too.

## Gmail (Standard+)
Test: `search_threads` with `newer_than:1d`, pageSize 1. If unavailable: Settings ->
Connectors -> add/enable **Gmail**, sign in with the WORK account (confirm it matches the
identity email in config — a personal Gmail here would leak personal mail into reports).

## Google Drive (Standard+)
Test: `list_recent_files` pageSize 1. Connect the same way if missing.
Also check for **Google Drive for Desktop**: does `G:\My Drive\` exist? If yes, reports
write straight to their Drive (primary delivery). If no, offer to help install it later;
until then local delivery is primary. The connector alone canNOT create the folder tree
reliably (it can create files but not manage folders well) — the mounted drive is the
dependable path.

## Jira / Atlassian (Full)
Test: `atlassianUserInfo`. If unavailable: Settings -> Connectors -> **Atlassian** ->
sign in with their work Atlassian account.
Then `getVisibleJiraProjects` and present THEIR visible boards as a numbered list — the
user picks which to track. Record project keys in config. If **PROM** is visible, say:
"PROM is write-protected company-wide — this system only ever reads it." (That rule is
absolute for every PCS tool.)

## Google Chat (Full, opt-in after warning)
See `google-chat-setup.md` — always give the warning and get an explicit yes first.

## General rules
- Every verification call must be read-only and trivially harmless.
- If a connector needs OAuth the user must click through it themselves — never ask them
  to paste codes or tokens into chat.
- Record in config which sources ended up ENABLED — the report prompt only includes
  sections for enabled sources, and the report's provenance line lists exactly what it saw.
