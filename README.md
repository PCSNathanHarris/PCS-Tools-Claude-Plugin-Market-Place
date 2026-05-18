# PCS Tools — Claude Code Plugin Marketplace

Single marketplace for all PCS Tools internal Claude Code plugins.

## Plugins

### pcs-promo-parser
Parses vendor promotional decks (Milwaukee, DeWalt, Makita, Bosch, EGO, Flex, GearWrench, Crescent) into the PCS Kit Builder Stage 1 CSVs — including Promo List, NLP Sheet, RSA Kits, RSA NLP, Needs Pricing, Non-Included, and Parser Audit.

**Skill:** `/parse-promo-deck`
**Source:** [plugins/pcs-promo-parser/](plugins/pcs-promo-parser/)

### pcs-map-updater
Merges a vendor MAP pricing sheet with a NetSuite ERP export, flags exceptions (missing match, MAP below purchase, promo MAP below purchase, keep-price review), and exports a review-ready Excel workbook for the monthly MAP update workflow.

**Skill:** `/map-price-update`
**Source:** [plugins/pcs-map-updater/](plugins/pcs-map-updater/)

### pcs-jira-task-builder *(beta — v0.1.0)*
Reads `pcs-promo-parser` Stage 1 CSVs and creates matching Jira Tasks in the PCS Promotions space. Hard PROM write-protection: always prompts for target Jira project, requires the literal phrase `WRITE TO PROM` to write to production. Defaults to PAT (test). Handles kit promos, NLPs, RSAs (with per-row review), per-vendor period naming (Milwaukee/DeWalt/Makita/Bosch/GearWrench `P1`/`P2`; EGO `H1`/`H2`; Flex `Q1`-`Q4`), auto-HERO detection, storefront link scaffolding (TUP/RTS/ATO/GWS/JPT/MTS), and PROM-style description templates.

Prerequisite: install the Atlassian MCP connector and authenticate against your Jira instance before invoking.

**Skill:** `/create-jira-promotions`
**Source:** [plugins/pcs-jira-task-builder/](plugins/pcs-jira-task-builder/)

## Installation

One marketplace, all three plugins:

```
/plugin marketplace add PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place
/plugin install pcs-promo-parser
/plugin install pcs-map-updater
/plugin install pcs-jira-task-builder
```

Then enable auto-update once: `/plugin` → **Marketplaces** → `pcs-tools` → toggle **Auto-update ON**.

Full setup instructions for first-time users: [docs/Team-Install-SOP.md](docs/Team-Install-SOP.md).

## Contributing

Adding your own plugin to this marketplace? See [CONTRIBUTING.md](CONTRIBUTING.md) for the full step-by-step guide.

When working in this repo with Claude Code, Claude will automatically read [CLAUDE.md](CLAUDE.md) to understand the conventions — you do not need to explain the project structure each time.

### Quick version
1. Create `plugins/<your-plugin-name>/` with a `.claude-plugin/plugin.json` and a `skills/<your-skill-name>/SKILL.md`.
2. Add a new entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<your-plugin-name>/"`.
3. Open a PR. Once merged, coworkers pick it up automatically on next `claude` start (if auto-update is on).
