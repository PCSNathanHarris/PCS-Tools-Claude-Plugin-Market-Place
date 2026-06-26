# Store order & scope

Run stores **in this order**. `--store` takes the **key**; file paths use the **slug** (same as the key
except where noted). All 17 in-scope stores already have a built tree under `<data_dir>/maps/<slug>/`.

## Order
1. **`the-milwaukee-store`** — RTS (always first)
2. **`the-dewalt-store`** — ATO (always second)
3. then the rest, any order:
   - `knaack-store` — JTB *(slug: `jtb`)*
   - `toolup-my-tool-store` — MTS *(slug: `mts`)*
   - `the-klein-store` — **nav-less** (see below)
   - `occidentalleatheroutlet`
   - `the-makita-store`
   - `the-ridgid-store`
   - `the-jet-store`
   - `the-sumner-store`
   - `the-pls-store`
   - `gearwrench-shop`
   - `greenlee-store`
   - `fall-protection-store`
   - `fasteners-store`
   - `weather-guard-store`
   - `wood-shop-outlet`

## Excluded — do NOT run
- **`toolupstore`** — the main Toolup.com store (TUP). It uses NetSuite-driven / manual collections and is
  categorized outside this system. **Never** run the routine against it. (No tree is built for it.)

> ⚠️ **`toolup-my-tool-store` is NOT the excluded store.** Despite the "toolup" prefix, MTS ("My Tool Store")
> is a separate Shopify store and **is in scope**. The only excluded key is `toolupstore`.

## Key → slug
Only two keys differ from their slug: `knaack-store` → `jtb`, `toolup-my-tool-store` → `mts`. For every
other store the slug equals the key. The engine resolves this automatically (`STORE_SLUG`); always pass the
**key** to `--store` and to the `shopify_*` MCP `store` param.

## Klein (nav-less)
`the-klein-store`'s app lacks the navigation read scope, so its tree is built from collections only via a
curated hierarchy. `weekly_run.py` detects `--store the-klein-store` and runs `build_klein.py` instead of
`build_category_map.py` automatically — no special handling needed in the skill.
