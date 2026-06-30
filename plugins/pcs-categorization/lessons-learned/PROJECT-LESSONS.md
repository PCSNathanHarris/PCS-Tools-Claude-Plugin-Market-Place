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
