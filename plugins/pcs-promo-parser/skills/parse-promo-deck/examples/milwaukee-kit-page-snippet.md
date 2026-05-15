# Example — Milwaukee kit page (B1G1 Cartesian)

## What the page looks like

```
─────────────────────────────────────────────────────────────────────
                  M18 FUEL™ HAMMER DRILL + FREE BATTERY
                              PCE 252601
              Online Execution: 5/4/2026 - 8/2/2026
─────────────────────────────────────────────────────────────────────

QUALIFYING ITEMS                                           FREE GOOD
─────────────────────────────────────────────────────────────────────

ITEM #     DESCRIPTION                IMAP    PROMO IMAP
2962-22    M18 FUEL™ 1/2" Hammer Drill 599.00  499.00
2767-22    M18 FUEL™ 1/4" Hex Impact   649.00  549.00

ITEM #     DESCRIPTION                IMAP    PROMO IMAP
48-11-1850 M18 REDLITHIUM XC5.0 Battery  149.00  FREE
48-11-2440 M18 REDLITHIUM HD9.0 Battery  199.00  FREE
─────────────────────────────────────────────────────────────────────
```

## Classification

- Page-level: **kit page** (case #9 in `page-classification.md`).
- No exclusion markers hit.
- Two qualifying paid SKUs (2962-22, 2767-22) and two free SKUs
  (48-11-1850, 48-11-2440).

## Extraction

- **Vendor**: Milwaukee (multiple `M18 FUEL` keyword hits).
- **Promo identifier**: `PCE 252601` → append `[PCE 252601]` to
  `promo_name`.
- **Deal title**: "M18 FUEL Hammer Drill + Free Battery".
- **Dates**: `Online Execution: 5/4/2026 - 8/2/2026` → start `5/4/2026`,
  end `8/2/2026`.
- **Header detection**: line containing `ITEM #  DESCRIPTION  IMAP
  PROMO IMAP` qualifies (2 signature hits + 1 price label). The
  `QUALIFYING ITEMS / FREE GOOD` banner above it is NOT a header.
- **Price column**: `Promo IMAP` (priority #1 in Milwaukee vendor file).
- **Free goods**: identified by `FREE` token in the `Promo IMAP` column
  for the second header section.

## Cartesian emission

2 paid × 2 free = 4 rows:

```csv
M18 FUEL Hammer Drill + Free Battery [PCE 252601],5/4/2026,8/2/2026,2962-22,1,499.00,,48-11-1850,1,0.00,,,,,,,,,,,,,,,,,,,
M18 FUEL Hammer Drill + Free Battery [PCE 252601],5/4/2026,8/2/2026,2962-22,1,499.00,,48-11-2440,1,0.00,,,,,,,,,,,,,,,,,,,
M18 FUEL Hammer Drill + Free Battery [PCE 252601],5/4/2026,8/2/2026,2767-22,1,549.00,,48-11-1850,1,0.00,,,,,,,,,,,,,,,,,,,
M18 FUEL Hammer Drill + Free Battery [PCE 252601],5/4/2026,8/2/2026,2767-22,1,549.00,,48-11-2440,1,0.00,,,,,,,,,,,,,,,,,,,
```

All four share the same `Promo Name` (with bracketed PCE) + dates.
Each row has one paid SKU in slot 1 (with the Promo IMAP price) and
one free SKU in slot 2 (price `0.00`).

## Audit impact

- `Kit Pages`: +1
- `Promo Rows`: +4
- No `non_included` or `nlp_rows` entries from this page.
