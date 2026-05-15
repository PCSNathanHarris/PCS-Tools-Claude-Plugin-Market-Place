# Project context for Claude

This file is automatically read by Claude Code when working inside this repo. It tells you what this repo IS, the conventions to follow, and the most common tasks you'll be asked to do.

## What this repo is

This is the **PCS Tools Claude Code plugin marketplace** — a single GitHub repo that hosts multiple Claude Code plugins. Coworkers install this one marketplace and get all plugins inside it.

**Hosted at:** `https://github.com/PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place`
**Marketplace name (in `marketplace.json`):** `pcs-tools`

This is **NOT** a typical software project. There is no build step, no test runner, no compiled output. The contents of this repo are pure markdown + JSON. Plugins describe how Claude should behave when invoked — they are **instructions to you**, not code that runs alongside you.

## Repo layout

```
PCS-Tools-Claude-Plugin-Market-Place/
├── .claude-plugin/
│   └── marketplace.json          ← THE registry — one entry per plugin
├── plugins/
│   ├── pcs-promo-parser/         ← Plugin folders, one per plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json       ← Plugin manifest (name, version, description)
│   │   └── skills/
│   │       └── parse-promo-deck/
│   │           ├── SKILL.md      ← Entry point Claude reads first
│   │           └── reference/    ← Detailed docs SKILL.md links to
│   └── pcs-map-updater/
│       └── … (same shape)
├── docs/
│   └── Team-Install-SOP.md       ← End-user install instructions
├── CLAUDE.md                     ← This file (you are here)
├── CONTRIBUTING.md               ← Human-facing contributor guide
└── README.md                     ← User-facing overview
```

## Core invariants — DO NOT BREAK THESE

1. **`marketplace.json` is the source of truth.** Every plugin must have an entry there. If you add a plugin folder but skip the JSON entry, the plugin will not be installable.

2. **The `source` field in `marketplace.json` is always a relative path inside this repo** (e.g. `./plugins/<name>/`). Never use a GitHub URL, never use an absolute path, never reference another repo. Cross-repo source references are not supported by Claude Code and break the marketplace install.

3. **Plugin folder name, `plugin.json` `name`, and `marketplace.json` entry `name` must all match exactly.** A mismatch is the most common reason installs fail.

4. **Version is duplicated in two places per plugin.** When bumping a version, update **both**:
   - `plugins/<plugin-name>/.claude-plugin/plugin.json` → `version`
   - `.claude-plugin/marketplace.json` → matching plugin entry's `version`
   They must always agree. Mismatched versions cause auto-update to misbehave.

5. **Plugins are markdown only.** No `.py`, `.js`, `.ts`, `.exe`, no runtime code in the `plugins/` tree. If a skill needs to execute code, the `SKILL.md` instructs Claude to **generate and run** that code at execution time. Do not ship static scripts.

6. **No secrets in `plugins/`.** Plugins are distributed to all installers — anything checked in is public-to-the-team.

## How plugins work conceptually

A plugin is a directory tree containing one or more **skills**. A skill is a folder with a `SKILL.md` (and optional `reference/` subfolder). When a user types `/<skill-name>` in Claude Code, Claude reads `SKILL.md` and follows the instructions to complete the workflow.

`SKILL.md` is structured as a step-by-step playbook. Reference docs in `reference/` are loaded on demand when the SKILL.md links to them. This keeps the primary instruction lean and helps Claude focus.

The current plugins:
- **`pcs-promo-parser`** — parses vendor promo deck PDFs into Stage 1 CSVs for the Kit Builder workflow. Skill: `/parse-promo-deck`.
- **`pcs-map-updater`** — merges a vendor MAP sheet with the NetSuite ERP export and flags exceptions. Skill: `/map-price-update`.

## Common tasks Claude will be asked to do

### "Add a new plugin called X"

Follow the playbook in `CONTRIBUTING.md` § "Add a new plugin — step-by-step". The summary:

1. Decide the plugin name (lowercase kebab-case, prefixed `pcs-`) and skill name (verb-phrase, kebab-case).
2. Create `plugins/<plugin-name>/.claude-plugin/plugin.json` with `name`, `version: "1.0.0"`, `description`, `author`, `keywords`.
3. Create `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`. Use the existing plugins as templates.
4. Create `plugins/<plugin-name>/skills/<skill-name>/reference/<topic>.md` for any non-trivial detail (matching logic, output specs, edge cases).
5. Add a new entry to the `plugins` array in `.claude-plugin/marketplace.json` with `source: "./plugins/<plugin-name>/"`.
6. Commit to a feature branch, open a PR, merge.

**Before you start writing files, confirm the plugin name and the skill name with the user.** Don't invent them.

### "Update / fix / improve plugin X"

1. Find the relevant `SKILL.md` or `reference/` file under `plugins/<plugin-name>/`.
2. Make the edit.
3. **Always bump the version** in both `plugins/<plugin-name>/.claude-plugin/plugin.json` AND the matching `marketplace.json` entry. Follow semver:
   - PATCH (`1.0.0 → 1.0.1`) for typos, doc tweaks, clarifications
   - MINOR (`1.0.0 → 1.1.0`) for new behavior, additive features
   - MAJOR (`1.0.0 → 2.0.0`) for breaking changes (output format change, removed feature)
4. Commit + push. Auto-update delivers it.

### "Test the marketplace locally"

```
/plugin marketplace add file://<absolute-local-path-to-this-repo>
/plugin install <plugin-name>
```

After edits, run `/plugin marketplace update pcs-tools` to refresh.

### "What's in plugin X?"

Read in order:
1. `plugins/<plugin-name>/.claude-plugin/plugin.json` — name, version, one-line description
2. `plugins/<plugin-name>/skills/<skill-name>/SKILL.md` — the workflow
3. `plugins/<plugin-name>/skills/<skill-name>/reference/*.md` — detailed rules

## Writing good SKILL.md files

When you're asked to create or improve a skill, follow these patterns:

- **Start with a 1–2 sentence statement** of what the skill does.
- **Use numbered steps** (`## Step 1 — Collect inputs`, `## Step 2 — …`). Each step is one logical action.
- **Be explicit about inputs.** Tell Claude what to ask for, what's required vs optional, what to do if something is missing.
- **Cross-reference `reference/<topic>.md`** for detailed rules rather than cramming everything into SKILL.md.
- **End with a "Key rules" section** for cross-cutting constraints (things that apply to every step).
- **Specify output format precisely.** File names, column orders, summary report format — leave nothing ambiguous.

## Versioning rules summary

- Initial release: `1.0.0`
- Bump `plugin.json` AND `marketplace.json` together — never just one
- Use semver: PATCH for docs, MINOR for additive, MAJOR for breaking
- Don't bump versions for changes that don't affect plugin behavior (e.g. editing this file, fixing typos in `README.md`)

## What to do if you're unsure

- **Confirm intent with the user before generating files.** Plugin names, skill names, scope — these are decisions that belong to the human, not to you. Ask.
- **Look at the two existing plugins as templates.** They define the patterns this repo uses.
- **If the task involves the marketplace structure itself** (not just adding a plugin), pause and confirm before making changes. This file's invariants are non-negotiable for the marketplace to keep working.
