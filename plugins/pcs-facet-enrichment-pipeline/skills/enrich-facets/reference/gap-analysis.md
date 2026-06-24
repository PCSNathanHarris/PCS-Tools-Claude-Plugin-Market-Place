# Reference — Gap Analysis (drives the scraper)

Runs against the Anglera export to (a) report coverage and (b) emit the **backfill
plan** that tells the scraper what to look for first.

## Inputs
- Anglera export CSV.
- `attributes (15).csv` (newest) — Name, Type, Dropdown Values, Key (the value authority).
- `TUP_Master_Facets_V2_export_cleaned_with_PT.csv` — L2 → linked attributes (Attr 1..9) + canonical PT (External ID). Fallback for linkage.

## Coverage scoring (per L2 × tree-linked attribute)
Fill % across the SKUs in that L2:

| Color | Fill % |
|---|---|
| 🟢 GREEN | ≥ 70% |
| 🟡 YELLOW | 50–69.9% |
| 🔴 RED | < 50% |

Also compute brand-wide per-attribute fill %, per-L2 average, and **PT canonical (adjusted)** — PT output that equals the L2 name (or a by-design Set/Kit value on a multi-item SKU) counts as a match; everything else is drift. Skip L2s with < 3 SKUs from scored coverage.

Parse facet cells as `Label: value`; map label→key via `attributes(15)` `Name`↔`Key`. A SKU "has" an attribute if a Facet cell (or, legacy, a dedicated column) is filled.

## Gap diagnosis (3 buckets)
For each RED/YELLOW (L2 × attribute) gap, classify:
- **Prompt-miss** — data is on the PDP but wasn't captured (e.g., Compliance→safety_rating, Industries→application). → recoverable, high priority for the scraper.
- **PDP-quality** — not on the vendor PDP at all (e.g., weight_capacity, bolt_diameter). → recoverable only from retailer source/title; lower priority.
- **Wrong-attribute / misassignment** — attribute doesn't apply, or SKU is mis-binned. → NOT a scrape target; flag as a tree/assignment issue.

## Output — the backfill plan (drives the scan)
Write `backfill_plan.csv`:

```
L2, Attribute (key), Attribute (Name), Coverage %, Status (RED/YELLOW), Bucket, Priority
```

- Include only **prompt-miss** and **PDP-quality** gaps (exclude wrong-attribute).
- Priority = lowest coverage first, brand-wide. The scraper uses this per-SKU: for each SKU it targets that SKU's L2 gap attributes in priority order.

Also emit the human gap report (xlsx, the coverage-gap-analyzer tabs) and a short headline (overall coverage, PT canonical adjusted, # red/yellow gaps) for **Gate 1**.

## Notes
- This logic mirrors the standalone `facet-coverage-gap-analyzer` skill; reuse its scripts if installed. The difference here is the machine-readable `backfill_plan.csv` output that feeds Step 3.
- Coverage is always computed against the **current** tree + newest attributes file. Never an older tree.
