# How to register & push `pcs-facet-enrichment-pipeline`

Repo: https://github.com/PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place (branch `main`)

## 1. Copy the plugin folder into the repo
Place this entire folder at:
```
PCS-Tools-Claude-Plugin-Market-Place/plugins/pcs-facet-enrichment-pipeline/
```
(It already has the required `.claude-plugin/plugin.json` + `skills/enrich-facets/SKILL.md` + `reference/` shape.)

## 2. Add this entry to `.claude-plugin/marketplace.json` (in the `plugins` array)
```json
{
  "name": "pcs-facet-enrichment-pipeline",
  "version": "1.0.0",
  "source": "./plugins/pcs-facet-enrichment-pipeline/",
  "description": "Anglera Faceted Search Backfill -> coverage gap analysis -> HIGH-confidence PDP backfill (real source PDPs, strict v15 dropdown validation, frequency-gated dropdown-addition proposals) -> NetSuite-ready facet import. Operator drops the export, names the brand, and double-clicks a one-click runner; Claude automates gap analysis, scraper config, QA, and NetSuite formatting."
}
```
Name + version must match `plugin.json` exactly.

## 3. (Optional) README.md plugin entry
```
### pcs-facet-enrichment-pipeline
Takes an Anglera Faceted Search Backfill export, runs a coverage gap analysis, back-fills blank attributes with HIGH-confidence values scanned from the products' real source PDPs (strict dropdown validation), and outputs a NetSuite-ready facet import.
**Skill:** `/enrich-facets`  ·  **Source:** [plugins/pcs-facet-enrichment-pipeline/](plugins/pcs-facet-enrichment-pipeline/)
```

## 4. Test locally, then push
```bash
# from the repo root, after copying the folder + editing marketplace.json
/plugin marketplace add file://<absolute-path-to-repo>
/plugin install pcs-facet-enrichment-pipeline
/enrich-facets        # smoke-test the flow on a small export

git checkout -b add-pcs-facet-enrichment-pipeline
git add plugins/pcs-facet-enrichment-pipeline/ .claude-plugin/marketplace.json README.md
git commit -m "feat: add pcs-facet-enrichment-pipeline plugin v1.0.0"
git push origin add-pcs-facet-enrichment-pipeline
# open a PR -> merge to main -> team auto-updates
```

## Auth note
The `git push` needs your GitHub credentials. Either run step 4 yourself, or approve
using the existing PCS GitHub token (the same one the other PCS plugins use) and I'll
push to the branch for you. The plugin ships markdown only — no scripts/secrets.
