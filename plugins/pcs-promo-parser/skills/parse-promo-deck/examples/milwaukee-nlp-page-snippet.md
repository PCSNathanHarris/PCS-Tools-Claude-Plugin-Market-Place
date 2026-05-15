# Example — Milwaukee NLP / Special-Buy page

## What the page looks like

```
─────────────────────────────────────────────────────────────────────
              MX FUEL™ CARRY-ON POWER SUPPLY — SPECIAL BUY
                              PCE 262776
              Online Execution: 5/4/2026 - 8/2/2026
              Permanent Price Change — see Online Execution
─────────────────────────────────────────────────────────────────────

ITEM #       DESCRIPTION                          IMAP     PROMO IMAP
MXF002-2XC   MX FUEL Carry-On Power Supply Kit    1599.00  1399.00
MXF002-1XC   MX FUEL Carry-On Power Supply        999.00   899.00
─────────────────────────────────────────────────────────────────────
```

## Classification

- The phrase **"Special Buy"** triggers `SPECIAL_BUY_MARKER`.
- Also "Permanent Price Change" is in the marker list.
- This is **case #7** in the decision tree — route to NLP Sheet, NOT
  `non_included`. The SKUs are real shelf-price-drop items the team
  wants in NetSuite.

## Extraction

- **Vendor**: Milwaukee (`MX FUEL` keyword).
- **Promo identifier**: `PCE 262776` → append `[PCE 262776]` to
  `promo_name`.
- **Deal title**: "MX FUEL Carry-On Power Supply — Special Buy".
- **Dates**: `5/4/2026 - 8/2/2026`.
- **Header detection**: same as kit pages — `ITEM #  DESCRIPTION
  IMAP  PROMO IMAP`.
- **Price column**: `Promo IMAP` (Milwaukee priority).
- **Source marker**: `special-buy` (SPECIAL_BUY_MARKER hit, not
  NLP_MARKER specifically).

## NLP Sheet emission

One row per SKU:

```csv
Promo Name,SKU,Promo Price,Online Execution Start,Online Execution End,Vendor,Page,Price Label,Source Marker
MX FUEL Carry-On Power Supply — Special Buy [PCE 262776],MXF002-2XC,1399.00,5/4/2026,8/2/2026,Milwaukee,33,Promo IMAP,special-buy
MX FUEL Carry-On Power Supply — Special Buy [PCE 262776],MXF002-1XC,899.00,5/4/2026,8/2/2026,Milwaukee,33,Promo IMAP,special-buy
```

Notes:
- `Promo Name` carries the deal title + bracketed PCE (matches the
  v0.5.9 NLP Sheet schema).
- `Price Label` records which column was matched.
- `Source Marker` is `special-buy` because `SPECIAL_BUY_MARKER` is
  what matched. If the page only said `NLP` or `New Lower Price`, this
  would be `nlp`.

## Audit impact

- `NLP Pages`: +1
- `NLP Rows`: +2
- `Promo Rows`: unchanged (no Cartesian emission for NLP pages).
- No `non_included` entry — NLP routing is preferred over exclusion.
