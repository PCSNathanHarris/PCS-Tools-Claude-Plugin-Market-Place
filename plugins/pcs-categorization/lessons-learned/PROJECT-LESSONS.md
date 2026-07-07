# Project-wide categorization lessons

Cross-store lessons that apply beyond any single store. The per-store `<store-key>.md` files hold
store-specific detail; this file holds what generalizes. **Formed/updated at the END of a run** (after all
scanning, so issues found during the run inform it). Synced to the plugin repo each weekly run by
`sync_repo.py`. Canonical rules live in `reference/universal-rules.md`; this is the running log of how we
got there and what to watch.

## 2026-06-29 — baseline (MTS supervised batch 1)
- **Add-only is absolute.** The only tag ever removed is `New Item V2`. Never change/rewrite/delete any
  other existing tag on any store. (universal-rules rule 10.)
- **Existing tags first.** Most `New Item V2` items are already partially categorized — confirm/complete
  their tags rather than classifying from scratch; correct an anchor only when the product contradicts it.
- **Verify the whole ancestor closure** before applying a node — a leaf can sit under the wrong department
  (e.g. a hand tool under a "Specialty Tools → Power Tools" node; plain apparel under "Apparel → Cordless
  Tools"). Never apply a department tag the product contradicts. (rule 3.)
- **Three non-exclusive trees on dual-tree stores:** Shop-by-Category + Shop-by-Brand + Battery-Platform.
  A product can get all three. Platform pick must match the product's type or use the clean platform root.
- **No zero tags, ever** — fallback ladder: specific category → general high-level category → trade →
  vendor brand-root. `review` is only for genuine ambiguity.
- **Reports** are colored `.xlsx` delivered via the Google-Drive-for-Desktop synced folder, NOT the MCP
  connector (binary/size/no-tabs/no-colors). Confidence is a 0–100 score → red/yellow/green.
- **Backlog reality:** MTS is the genuine backlog (~2,737 NIV2). Single-OEM superstores (Pro Work Supply/3M,
  Total Fastening/Simpson) were mostly categorized at launch — finalize, don't re-classify. the-jet-store is
  ON HOLD (duplicate-creation error inflates its count).

## 2026-06-30 — fallback ladder: safe generic category beats a bare brand page (batch 2, 500)
- When no specific category leaf matches anchors/facet, **match the title to a leaf** ("Drywall Circle Cutter"
  -> Drywall Tools; "...Ladder" -> Step Ladders; "drop-in anchor" -> Anchors). The leaf often exists even when
  the product has no category tag yet.
- If still none, place in a **safe generic** that's confidently correct (manual tool -> bare Hand Tools node;
  fastener -> Fasteners; part/blade -> Replacement Parts/Accessories). A correct generic beats brand-only.
- **Never use a generic that adds a wrong ancestor** (rule 3): MTS "Specialty Tools" carries Power Tools/Cordless,
  so it's NOT safe for a hand tool -> use Hand Tools.
- **Prefer branded sub-categories** (e.g. Marshalltown Drywall Tools) over the top-level brand page.
- Brand-only (top-level brand collection) is the **absolute** last resort — genuinely rare (e.g. a powder-actuated
  fastening tool with no tool category).

## 2026-06-30 — dual-tree: always BOTH trees where possible (batch 2)
- Multi-brand/dual-tree stores (e.g. MTS) must populate BOTH Shop-by-Category AND Shop-by-Brand for
  every product where a node exists. If no specific brand node fits, use the vendor's top-level brand
  collection (fallback_brand_gid) — never leave the brand side empty.
- Enforced in the engine: apply_run auto-adds the vendor brand-root on dual-tree when a category pick
  has no resolved brand node; build_report mirrors it. Only a no-possible-category item is brand-only.

## 2026-06-30 — parallel category structures: tag in ALL of them (rule 8c + multi-category schema)
- Brand stores run **several parallel category trees at once**, each with its own tag namespace, and a
  product belongs in **every** applicable one: **Power Tools** (`Power Tools > Cutting > Saws` -> `Saws`),
  **Shop By Trade** (`SBTW …`/`SBTM …`/`SBTA …`, e.g. `SBTW Circular Saws`), and **Battery Platform**
  (M18/M12/MX FUEL; 20V MAX/FLEXVOLT; LXT/XGT/CXT). Tagging `SBTW Circular Saws` + `M18` was NOT enough —
  the Power-Tools `Saws`/`Power Tools` closure was missed.
- **Two mechanisms now deliver full coverage:**
  1. **Build fix (RTS-style):** a template `collection-list` edge is now **trusted when its parent is an
     in-nav node** (a real structure like Power Tools "Milwaukee Saws"), so a Shop-By-Trade leaf inherits
     its Power-Tools ancestors. Template parents that are OFF-nav (e.g. "Milwaukee Carpentry Tools" ->
     `carpentry-tools`) stay untrusted, so copy/paste noise is still excluded. After the fix, "Milwaukee
     Circular Saws" closure = `Power Tool Cutting, Power Tools, Saws, SBTW Circular Saws`.
  2. **Multi-category schema:** `decisions.json` now takes **`category_gids`** (a list) — pick one node per
     structure; apply_run unions all closures (+ brand + platform). Use this on stores where the structures
     are separate trusted nodes (e.g. **ATO/DeWalt, JPT/Makita** have NO template->in-nav edges, so the build
     fix doesn't touch them — the schema is how you place into each structure there).
- **Reports:** a multi-store run now produces **ONE workbook with one tab per store**
  (`categorization-weekly-<date>.xlsx`); per-store files are not delivered separately.

## 2026-07-07 (2026-W28) — tree-diff "new categories" spike is a vocabulary-build artifact
On the first W28 run several stores' `weekly_run` tree-diff reports a large "NEW since last run" count
(Milwaukee: 202→356, +154). This is the full nav+floating collection vocabulary being surfaced (including
promo-code collections like BF##/ACCY15/FLASH20 that are never valid targets), **not** that many new merchant
collections. Treat large diffs as vocabulary expansion: log in the run summary, create nothing, and only call
out genuinely novel *product-category* nodes. The engine strips promo/operational collections as targets.

## 2026-07-07 (2026-W28) — two reusable classification techniques (proven on MTS 250-item batch)
1. **Confirm-by-anchor via subset-match.** For already-partly-categorized NIV2 items, pick the deepest category
   node whose FULL closure ⊆ the product's existing `current_category_tags`. This confirms the placement while
   staying strictly add-only (never introduces a wrong department, satisfying universal rule 3 automatically).
   On dual-tree stores, ALSO require the **vendor token to appear in the brand node's path** before accepting a
   brand node — a pure subset match can cross brands (a Pacific Laser Systems part matched brand "Fluke Other").
   When the vendor-gated brand match fails, leave brand_gid unset and let the engine's dual-tree guarantee add
   the correct vendor brand root.
2. **`review:true` is overridden on dual-tree stores.** apply_run's dual-tree guarantee converts a no-category /
   review decision into a vendor brand-root fallback (tags the item with just its brand, removes NIV2, adds
   CL-categorized). This is correct per universal rule 7 (review = genuine ambiguity, NOT "no category found").
   So for a category-less item on a dual-tree store, expect a brand-only placement, not a review-queue entry.
   Reserve `review:true` for items a human must actually disambiguate.
