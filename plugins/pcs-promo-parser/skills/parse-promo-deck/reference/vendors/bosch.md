# Bosch

## Brand keywords

- `bosch`
- `profactor`
- `bulldog` (jackhammer / SDS line)

## SKU pattern

Regex: `\b(?:GBH|GSB|GWS|GBA|GAL|GXL|GTM|GBM|GBX|GLM|GIS|GSA|GST|GDS|GDX|GDE|GHO|GKF|GOP|GBL|GCM|GMC|GTS|GLT|GLR|GLI|GFC|GMS|GXS|HDC|FCE|FOM|HC|RA|XC)\s*[A-Z0-9-]+\b` (case-insensitive)

Examples:
- `GBH18V-26K`, `GSB18V-1300`, `GWS18V-13PC` (cordless rotary hammers / drills / grinders)
- `GBA18V40-2PK` (batteries)
- `RA1180`, `HC2154` (accessories)

## Promo code pattern

**None reliable.** Bosch decks do NOT use per-page promo identifiers
consistently. Use deal title as `promo_name`; do not invent a code.

## Price label priority

1. `Sug Retail`
2. `Sugg Retail`
3. `Suggested Retail`
4. `Special Buy`
5. `Hot Buy`
6. `Special Price`
7. `MSRP`

`Sug Retail` is the customer price when shown; `MSRP` is the regular
fallback. `Special Buy` and `Hot Buy` are temporary promo overrides.

## Non-price labels (CRITICAL — NEVER treat as price)

- **`Tier 1`**, **`Tier1`** — dealer cost tier
- **`Tier 2`**, **`Tier2`** — dealer cost tier
- `BIM` (Bosch Internal Margin reference)
- `Description`

`TIER 1` / `TIER 2` are dealer cost columns. NEVER pick them as the
customer price.

## Header signatures

Common headers:
- `MODEL # DESCRIPTION MSRP TIER 1 TIER 2 SPECIAL BUY`
- `MODEL # DESCRIPTION MSRP TIER 1 TIER 2 HOT BUY`
- `MODEL # DESCRIPTION MSRP TIER 1 TIER 2 FREE GOOD`

Signature tokens:
- `MODEL`, `MODEL #`
- `DESCRIPTION`
- `MSRP`
- `TIER 1`, `TIER 2`
- `SPECIAL BUY`, `HOT BUY`, `FREE GOOD`
- `SUG RETAIL`, `SUGG RETAIL`
- `BIM`

## Quirks

- **No separate Promo IMAP**: Bosch often falls back to `MSRP` as the
  only customer-facing price. That's correct — emit the MSRP value.
- **B1G1 phrasing**: "BUY: (X) Tool Kits (Mix & Match) RECEIVE: FREE
  [SKU] Per Each Purchased". Treat as B1G1 with `qty=1` on both paid
  and free; each eligible bought option gets its own row in the
  Cartesian.
- **Written-month date ranges** are very common on Bosch:
  - `August 1 - October 31, 2025` → start `8/1/2025`, end `10/31/2025`
  - `Aug 1 – Oct 31, 2025` → same
  - `January 15, 2026 to March 31, 2026` → same
  When only the second month carries a year, use it for both.
- **Date label**: `Advertised Sell Through` is the customer window.
- **Multi-promo per page**: Bosch flyers often stack two distinct
  promos vertically. See
  `edge-cases.md#multi-promo-per-page`.
