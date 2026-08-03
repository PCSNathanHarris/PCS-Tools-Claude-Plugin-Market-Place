---
name: setup-meeting-reports
description: One-time guided setup for personalized automated meeting notes. Interviews the user (access tier, connectors, meetings and reporting windows, output locations, privacy exclusions), connects each source with the user's own accounts, and creates the scheduled tasks that generate Detailed + Quickfire meeting reports. Use when someone wants to set up meeting notes, standup summaries, automated work reports, or says "set up my meeting reports" / "I want what Nathan has for standup notes".
---

# Setup Meeting Reports — Guided Wizard

You are setting up **automated, personalized meeting notes** for this user. When finished, scheduled tasks will run before each of their recurring meetings and produce two Word documents summarizing **their own work** across the sources they connect: a comprehensive **Detailed** report and a one-page bullet **Quickfire** version.

**Audience calibration: assume the user is NOT technical.** Never ask them to run terminal commands — you run everything. Explain each step in one plain sentence before doing it. Ask questions in plain numbered text (not widgets), one small batch at a time.

Reference docs (read as needed during setup): `reference/report-prompt-template.md` (the scheduled-task prompt you will personalize), `reference/connector-setup.md`, `reference/google-chat-setup.md`, `reference/source-mechanics.md`, `reference/output-format.md`, `reference/privacy-rules.md`.

## Step 0 — Welcome and prerequisites

Explain in 3-4 sentences what will be set up and that everything is read-only (this system never sends messages, never edits their email/Jira/chat, and only ever writes the report files). Then check silently:

1. Scheduled-task capability: the `create_scheduled_task` tool must be available (Claude desktop app). If missing, stop and explain they need the Claude desktop app.
2. Python: run `python --version`. If missing, install it for them (Windows: `winget install -e --id Python.Python.3.12 --scope user`, then verify). Never use `python3` on Windows.
3. Install packages quietly now (needed later): `python -m pip install --user --quiet python-docx google-auth google-auth-oauthlib google-api-python-client`.
4. Create the user's config directory: `%USERPROFILE%\.claude\pcs-meeting-notes\`. All personal config, tokens, and exclusion lists live HERE — never inside the plugin folder (plugin folders are read-only caches and get replaced on update).

## Step 1 — Identity

Ask for (or confirm if discoverable): their **name** and **work email address**. These drive the "your work only" filtering everywhere. Store in config.

## Step 2 — Access tier ("how much should the reports see?")

Present the three tiers in plain language and ask which they want. More connectors = richer notes; each tier is a superset:

1. **Minimal** — Claude work only: everything they did in Claude sessions and their project files. Zero connector setup.
2. **Standard** — Minimal **plus Gmail** (summaries of email threads THEY sent messages in) **plus Google Drive** (files they created/edited). Needs the Gmail and Drive connectors.
3. **Full** — Standard **plus Jira** (tasks they created/commented/edited on boards they choose) **plus Google Chat** (what they said and did in work chats). Jira needs the Atlassian connector; **Google Chat needs a one-time extra setup — give the warning from `reference/google-chat-setup.md` (it is more involved: a Google Cloud sign-in approval, ~2-10 minutes one time), briefly explain the process, and ASK if they want to proceed.** If they decline chat, set them up as Full-minus-chat and note they can add it later by re-running this skill.

## Step 3 — Connect the sources (only what their tier needs)

Work through `reference/connector-setup.md` for each enabled source, checking whether each connector already responds before walking them through connecting it (claude.ai Settings -> Connectors, plain click-path instructions):

- **Claude sessions**: auto-discover both transcript locations on their machine (`%USERPROFILE%\.claude\projects\` and `%APPDATA%\Claude\local-agent-mode-sessions\` if present) plus ask which project folders hold their work files. No connector needed.
- **Gmail**: verify with a harmless `search_threads` call on their account.
- **Google Drive**: verify the connector, then check for Google Drive for Desktop (a mounted `G:\My Drive`). If not mounted, reports fall back to connector reads + local-only delivery.
- **Jira**: verify the Atlassian connector, then call `getVisibleJiraProjects` and present the list of boards THEIR account can see. Ask which projects to track. **If PROM is among them, state that PROM is write-protected company-wide and this system only ever reads it.**
- **Google Chat** (only if they accepted the warning): follow `reference/google-chat-setup.md` — copy `scripts/chat_pull.py` from the plugin into their config dir, get the OAuth client file in place, have them click the consent screen with their own Google account, run a small test pull, and confirm message counts look right.

## Step 4 — Meetings and reporting windows

Ask: how many recurring meetings need reports? For EACH meeting collect:

1. Meeting name (used in filenames — e.g. "Monday Standup", "Team Sync").
2. Meeting day and time, and their timezone.
3. When the report should generate (recommend 1-2 hours before the meeting).
4. **The reporting window — the user defines this themselves**: what day/time the window STARTS and ENDS (end defaults to generation time). Offer the house example as illustration only: a Monday-noon standup report covering previous-Wednesday-11am through Monday-noon, and a Wednesday boardroom report covering the full Wednesday-to-Wednesday week — windows that tile with no gap or double-count. Help them design windows that tile if they have multiple meetings, but their choice wins.

## Step 5 — Output preferences

1. **Versions**: default is BOTH Detailed and Quickfire per meeting — confirm, or let them pick one.
2. **Delivery**: primary = their Google Drive at `G:\My Drive\Work Summaries\<YYYY>\<Monday date> to <Sunday date>\` (create the folders). **Always also keep a local backup copy** — ask where (default `%USERPROFILE%\Documents\Work Summaries\` with the same year/week structure). If they have no Drive mount, local becomes primary and say so.

## Step 6 — Privacy pass (mandatory, every user)

Read `reference/privacy-rules.md` and walk it with them:

1. Ask which **chat spaces are personal** and must never be read or reported — write these to `excluded_spaces.json` in their config dir (excluded BEFORE fetch, content never touches disk).
2. Ask if any email addresses/threads or folders should be skipped.
3. State the non-negotiable built-ins out loud: reports cover **their own work only**; every source is **read-only**; this system **never sends messages** anywhere; old reports are **never modified or deleted**; credentials/tokens stay in their local config dir and are never echoed.

## Step 7 — Write config and create the scheduled tasks

1. Write `%USERPROFILE%\.claude\pcs-meeting-notes\config.json` capturing everything: identity, tier, enabled sources, transcript paths, project folders, Jira projects, meetings (name/cron/window definitions/timezone), output paths, version preference. Show them a plain-language summary and get a final "yes".
2. For each meeting, build the task prompt from `reference/report-prompt-template.md` — replace every `{{PLACEHOLDER}}` with their config values and DELETE the source sections their tier doesn't include. The filled prompt must be fully self-contained (future runs have no memory of this conversation).
3. Create one scheduled task per meeting via `create_scheduled_task` (kebab-case taskId like `monday-standup-report-<firstname>`, cron from their schedule in LOCAL time, notifyOnCompletion true).
4. Tell them: tasks run while the Claude desktop app is open — if it's closed at report time, the report generates at next launch.

## Step 8 — Test run

Strongly recommend clicking **Run now** on one task from the Scheduled sidebar while you're together: the run will ask for a handful of permissions (file reads, the connectors, writing the report files) and **approvals granted during a run stick to the task forever** — after this one supervised run, every future report generates hands-off. Review the first report with them and adjust tone/detail in the task prompt if they want changes.

Finish with a short summary: what was connected, the meetings and windows, where reports land, and how to change things later (re-run this skill; it reads the existing config and edits rather than starting over).
