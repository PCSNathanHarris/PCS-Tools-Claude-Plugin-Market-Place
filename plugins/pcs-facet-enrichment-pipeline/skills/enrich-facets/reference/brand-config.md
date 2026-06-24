# Reference — Brand Config & Source Selection

No per-brand vendor-domain table is maintained. Brand handling is derived at run
time from the brand name the operator gives + the export's own Source URLs.

## Source-URL selection (per SKU)
1. Normalize the brand name to a token: lowercase, strip spaces/punctuation (e.g. "Guardian" → `guardian`, "GearWrench" → `gearwrench`).
2. Among the SKU's `Source URL 1..N`, pick the **first URL whose host or path contains the brand token** (case-insensitive). That's the manufacturer/vendor PDP (e.g. `guardianfall.com` contains `guardian`; `dewalt.com` contains `dewalt`).
3. If none contain the brand token, use the **first available** Source URL.
4. Retailer URLs (the non-brand ones) are used only as a **fallback for PDP-quality attributes** (weight_capacity, color, lengths) when the vendor page didn't yield them.

## Standing normalization map (applied before dropdown validation)
Resolves common variants to the existing v15 dropdown value so they aren't proposed as new:
- Strip ANSI edition/year suffix: `ANSI Z359.11-2021` → `ANSI Z359.11`, `ANSI Z359.3-17` → `ANSI Z359.3`.
- `csa` / `CSA` → `CSA Certified`.
- `Telecoms` → `Telecom`.
- `Self-Retracting` → `Self-Retracting (SRL)`.
- Hyphen/case folding for near-exact matches (e.g. `Shock Absorbing` ↔ `Shock-Absorbing`).
This map is extended over time as new brands surface variants; keep it data-driven at the top of the generated script.

## Optional brand color default
Most attributes must come from the PDP. `color` is the exception where a brand may
have a house default for bare hardware — but only apply a default if the team has
explicitly set one for that brand. Otherwise leave `color` blank when not stated.
(Guardian uses many colors → no single default.)

## Per-brand dropdown additions
Each brand/vertical surfaces its own out-of-dropdown values (see frequency-gated
discovery in SKILL.md Step 5). The Guardian baseline is in
`Guardian_dropdown_additions_needed.csv`. These are proposals for the operator to
approve into `attributes (NN).csv`; the pipeline never writes unapproved values.
