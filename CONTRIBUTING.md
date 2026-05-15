# Contributing to the PCS Tools Marketplace

This repo is the single Claude Code marketplace for all internal PCS Tools plugins. Adding a new plugin = creating a new subfolder under `plugins/` and registering it in one JSON file. No code is compiled or executed at the marketplace level — plugins are pure markdown that instructs Claude how to do a task.

## Before you start

You should have:
- A working Claude Code install (see [docs/Team-Install-SOP.md](docs/Team-Install-SOP.md))
- Push access to this repo (ask Nathan Harris)
- A clear, single-purpose task in mind for your plugin (one workflow per plugin)

## Repo architecture in 60 seconds

```
PCS-Tools-Claude-Plugin-Market-Place/
├── .claude-plugin/
│   └── marketplace.json          ← THE registry. One entry per plugin.
├── plugins/
│   ├── pcs-promo-parser/         ← Each plugin is a self-contained folder.
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json       ← Plugin manifest (name, version, description).
│   │   └── skills/
│   │       └── parse-promo-deck/
│   │           ├── SKILL.md      ← Entry point. What Claude reads first.
│   │           └── reference/    ← Detailed docs SKILL.md links to.
│   └── pcs-map-updater/
│       └── ... (same shape)
├── CLAUDE.md                     ← Instructions Claude reads when working in this repo.
├── CONTRIBUTING.md               ← This file.
└── README.md                     ← User-facing overview.
```

**Three rules to know:**

1. **One marketplace.json controls everything.** Coworkers add this repo once and see every plugin we add here, automatically.
2. **Plugins are markdown, not code.** Your `SKILL.md` is a set of instructions Claude follows. No build step, no compile, no test runner.
3. **The `source` field in `marketplace.json` is a relative path inside THIS repo.** Never point to another GitHub repo from `source` — that breaks the install.

## Add a new plugin — step-by-step

### Step 1 — Pick a name

Use lowercase, kebab-case, prefixed with `pcs-`:
- ✅ `pcs-pricing-checker`
- ✅ `pcs-vendor-reconciler`
- ❌ `MyAwesomeTool`, `pricing_checker`, `tool1`

The slash command Claude users will type is derived from your skill name, not the plugin name. Both should be intuitive.

### Step 2 — Create the folder structure

```
plugins/<your-plugin-name>/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── <your-skill-name>/
        ├── SKILL.md
        └── reference/          ← optional but recommended for anything non-trivial
            └── <topic>.md
```

Example for a fictional `pcs-invoice-checker`:
```
plugins/pcs-invoice-checker/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── check-invoice/
        ├── SKILL.md
        └── reference/
            └── validation-rules.md
```

### Step 3 — Write `plugin.json`

```json
{
  "name": "pcs-invoice-checker",
  "version": "1.0.0",
  "description": "One-sentence description of what your plugin does, who it's for, and what it produces.",
  "author": {
    "name": "PCS Tools"
  },
  "keywords": ["invoice", "validation", "netsuite"]
}
```

**Rules:**
- `name` must match the folder name and the entry you'll add to `marketplace.json`.
- `version` follows [semver](https://semver.org/): MAJOR.MINOR.PATCH. Start at `1.0.0` for first release.
- `description` shows up in the `/plugin` menu — be specific.

### Step 4 — Write `SKILL.md`

This is the instruction set Claude follows when a user invokes your skill. Look at `plugins/pcs-promo-parser/skills/parse-promo-deck/SKILL.md` and `plugins/pcs-map-updater/skills/map-price-update/SKILL.md` as templates.

Good `SKILL.md` structure:

```markdown
# <Skill Title>

Brief 1-2 sentence statement of what this skill does.

---

## Step 1 — Collect inputs

What does Claude need from the user before it can start?
- List each input
- Specify file paths, formats, optional vs required
- Tell Claude what to do if something is missing (ask, default, abort)

---

## Step 2 — <First action>

Concrete instructions. Reference detailed rules in `reference/<topic>.md`
instead of cramming everything into SKILL.md.

---

## Step 3 — <Next action>

…

---

## Step N — Report results

Tell Claude what to print at the end.

---

## Key rules

- Constraints Claude must always honor
- Common pitfalls to avoid
- Cross-references to reference docs
```

**Why split into `reference/`:** SKILL.md is what Claude reads first to plan the work. Reference docs are loaded on demand when a specific topic comes up. This keeps the main instruction lean and helps Claude focus.

### Step 5 — Register in `marketplace.json`

Open `.claude-plugin/marketplace.json` at the repo root and add a new entry to the `plugins` array:

```json
{
  "name": "pcs-invoice-checker",
  "version": "1.0.0",
  "source": "./plugins/pcs-invoice-checker/",
  "description": "One-sentence description — should match plugin.json."
}
```

**Critical:**
- `name` matches `plugin.json` and the folder name.
- `version` matches `plugin.json`. Bump both together on future releases.
- `source` is `./plugins/<your-plugin-name>/` — always relative to this repo.

### Step 6 — Test locally before pushing

In a Claude Code session:

```
/plugin marketplace add file://<absolute-local-path-to-this-repo>
/plugin install pcs-invoice-checker
```

Then run your skill (e.g. `/check-invoice`) and verify it does what you expect on a realistic input.

If it doesn't work as expected, edit the SKILL.md, re-run `/plugin marketplace update pcs-tools`, and try again. Iterate locally — don't push until it works.

### Step 7 — Commit and push

```bash
git checkout -b add-pcs-invoice-checker
git add plugins/pcs-invoice-checker/ .claude-plugin/marketplace.json
git commit -m "feat: add pcs-invoice-checker plugin v1.0.0"
git push origin add-pcs-invoice-checker
```

Open a PR. Once merged to `main`, coworkers will pick up the new plugin automatically the next time they start `claude` (if they have auto-update enabled).

## Updating an existing plugin

For a real change (new feature, bug fix, behavior change):

1. Edit the skill files inside `plugins/<plugin-name>/skills/<skill-name>/`.
2. Bump `version` in **both** `plugins/<plugin-name>/.claude-plugin/plugin.json` AND the matching entry in `.claude-plugin/marketplace.json`.
3. Follow semver:
   - `1.0.0 → 1.0.1` for a typo, doc tweak, small clarification
   - `1.0.0 → 1.1.0` for new behavior, new flags, additive features
   - `1.0.0 → 2.0.0` for a breaking change (output format change, removed feature)
4. Add a changelog line to the plugin's `README.md` (if it has one) or to the main `README.md`.
5. Commit, PR, merge. Auto-update delivers it to the team.

## Conventions

### Plugin naming
- Prefix: `pcs-`
- Style: lowercase kebab-case
- Be descriptive: `pcs-vendor-reconciler` beats `pcs-vr`

### Skill naming
- Style: lowercase kebab-case (becomes the `/skill-name` command)
- Reads as a verb-phrase: `parse-promo-deck`, `check-invoice`, `reconcile-vendor`

### File encoding
- All `.md` files: UTF-8, LF line endings (git will warn on commit if Windows changes them to CRLF — that's fine, git's normalization handles it).

### What NOT to do
- ❌ Don't put runtime code (`.py`, `.js`) inside skills. Plugins are markdown only. If your skill needs to run a script, the SKILL.md tells Claude to **generate and run** that script at execution time — don't ship a static script in the repo.
- ❌ Don't reference plugins in other GitHub repos via `source`. The `source` field only supports relative paths inside this repo.
- ❌ Don't ship secrets, API keys, or customer data in any file under `plugins/`. Plugins are public-facing once installed.
- ❌ Don't skip the version bump when changing behavior. Without it, auto-update can't detect the change.

## Help

Stuck? Check:
- The two existing plugins (`pcs-promo-parser`, `pcs-map-updater`) — they're working templates.
- [CLAUDE.md](CLAUDE.md) — the AI context file, also useful for humans skimming the structure.
- Nathan Harris (nathan.harris@pcstools.com) — slack/email for anything ambiguous.
