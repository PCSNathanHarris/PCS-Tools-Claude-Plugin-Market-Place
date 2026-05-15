# Example — Milwaukee excluded page (spend-to-earn)

## What the page looks like

```
─────────────────────────────────────────────────────────────────────
            BUY $800 IN CONCRETE ACCESSORIES — GET 1 FREE
              Online Execution: 5/4/2026 - 8/2/2026
─────────────────────────────────────────────────────────────────────

QUALIFYING CATEGORY: Concrete Accessories

ELIGIBLE FREE GOODS (Choose 1):
  • 2962-22   M18 FUEL Hammer Drill
  • 2767-22   M18 FUEL Hex Impact

Spend threshold: $800 minimum order in Concrete Accessories category.
─────────────────────────────────────────────────────────────────────
```

## Classification

- The phrase **"Buy $800 in Concrete Accessories"** triggers
  `SPEND_TO_EARN_MARKER` (the `Buy \$N in <category>` variant requires
  2+ digit dollar amount + a category word — see
  `exclusion-markers.md#spend_to_earn_marker`).
- This is **case #4** in the decision tree.
- Higher-priority cases (#1 killed, #2 B&M, #3 SPIFF) did not match.

## Why it's NOT a kit

The customer must spend a category-wide dollar threshold to qualify.
There's no fixed paid+free pair — the "qualifying purchase" is a
basket of accessories totaling $800, not a single SKU. Each free-good
option could theoretically be paired with many different basket
combinations.

Emitting Cartesian rows here would produce hundreds of wrong "kit"
entries downstream. Hence the exclusion.

## Non-included emission

One row per affected SKU on the page (or one row with blank SKU if no
SKUs are extractable). For this page, the page lists two specific free
goods, so we emit one `non_included` row per free SKU:

```csv
Page,Reason,SKU,Deal Text,Detail
67,spend-to-earn,2962-22,Buy $800 in Concrete Accessories - Get 1 Free,SPEND_TO_EARN_MARKER: "Buy $800 in concrete"
67,spend-to-earn,2767-22,Buy $800 in Concrete Accessories - Get 1 Free,SPEND_TO_EARN_MARKER: "Buy $800 in concrete"
```

Alternative (if no SKUs are listed on the page — e.g. the page just
says "spend $800 to get a free tool"), emit one row with blank SKU:

```csv
67,spend-to-earn,,Buy $800 in Concrete Accessories - Get 1 Free,SPEND_TO_EARN_MARKER: "Buy $800"
```

## Audit impact

- `Excluded Pages`: +1
- `Non-Included Count`: +2 (or +1 if no SKUs listed)
- `Promo Rows`: unchanged
- `NLP Rows`: unchanged

## Contrast with related cases

- If the page said **"Buy 5 drills, save 10%"** → BMSM_MARKER, reason
  `buy-more-save-more` (case #5).
- If the page said **"Use code DRILL20 at checkout for 20% off"** →
  PROMO_CODE_MARKER, reason `promo-code-only` (case #6).
- If the page said **"Special Buy — 20% Off Permanent"** → NLP routing
  to `nlp_sheet.csv` (case #7), NOT exclusion.
