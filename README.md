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

## Installation

One marketplace, both plugins:

```
/plugin marketplace add PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place
/plugin install pcs-promo-parser
/plugin install pcs-map-updater
```

Then enable auto-update once: `/plugin` → **Marketplaces** → `pcs-tools` → toggle **Auto-update ON**.

Full setup instructions for first-time users: [docs/Team-Install-SOP.md](docs/Team-Install-SOP.md).

## Adding a new plugin

1. Create `plugins/<your-plugin-name>/` with a `.claude-plugin/plugin.json` and a `skills/` directory.
2. Add a new entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<your-plugin-name>/"`.
3. Commit and push. Coworkers pick it up automatically on next `claude` start (if auto-update is on).
