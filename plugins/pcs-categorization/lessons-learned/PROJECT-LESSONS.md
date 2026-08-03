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

## 2026-07-20 (2026-W30) — cross-store patterns from the DeWalt cordless wave
- **A vendor Shop-by-Brand FALLBACK root can have a POLLUTED closure.** On MTS the DeWalt brand fallback
  (`421689524477`) resolves to a "DeWalt" collection whose closure is `[Core Bits, DeWalt]` — letting the
  dual-tree guarantee auto-apply it injects a wrong `Core Bits` tag on every DeWalt tool. **Before relying on
  any auto brand fallback, check its closure; set an explicit typed brand_gid when the fallback is dirty.**
- **"60V MAX" is not auto-detected as FLEXVOLT by the platform detector.** DeWalt 60V MAX tools are FLEXVOLT,
  but the engine left `platform_tags` empty on 60V circular/worm-drive/miter saws (only "FLEXVOLT"/"20V/60V"
  strings are caught). Add the FLEXVOLT platform/brand by hand for 60V tools. FLEXVOLT also has NO clean
  platform root on MTS/ATO — use a typed FLEXVOLT node (e.g. FLEXVOLT Saws).
- **Cut-off tools + die grinders + angle grinders all live under "Grinders"** on both ATO and MTS — there is no
  dedicated Cut-Off-Tool node (the "Concrete Tools > Cut-Off Saws" node is for large concrete saws only).
- **A store may group all saw types under one "Saws" leaf** (ATO, MTS) — miter/circular/reciprocating saws
  share it; don't hunt for a per-type saw node that isn't there.
- **Subset-match anchor-confirm scales the backlog drain:** the deepest node whose full closure ⊆ the
  product's existing category tags is a safe pure-add confirm (mostly no-op) that lets NIV2 be removed; only
  items with empty/partial anchors need manual classification. On MTS W30, 172/250 were anchor-confirmed.

## 2026-07-28 (2026-W31) — cross-store patterns
- **⚠ `classify_run.py` (engine helper) is UNSAFE in the current version — verify or discard its node picks.**
  On MTS this run it matched on a PARTIAL anchor and proposed deeper leaves whose closure INJECTS tags the
  product does not have: a deburring-tool replacement cutter → "Conduit Bending"; a nut driver → "Drywall
  Screw Guns" (adds `Cordless Tools`); MaxiFlex gloves → "Left Handed Products"; a strap-wrench replacement
  strap → "Lifting Straps"; a cutter extension chain → "Chain Hoists". Applying these would violate add-only
  and universal rule 3. **Use the full-closure subset-match to author decisions instead** (deepest node whose
  FULL closure ⊆ the product's existing tags) — it is both add-only-safe AND produces the correct node for
  pre-tagged items. Always run a pre-write scan for forbidden/promo tags in every chosen closure.
- **When a backlog wave is fully pre-tagged, apply_run's add-batches are provable no-ops.** If every chosen
  closure ⊆ the product's existing tags, the only state change is `CL-categorized` + `New Item V2` removal.
  Verify (tag ∉ product.all_tags for 0 pairs) and you may skip the vacuous add-batch calls, running just the
  chunked CL/remove writes — a large MCP-call saving with no behavioral difference. (MTS W31: 41/41 add-batches
  vacuous; only 9 CL + 9 remove chunks needed.)
- **A replacement part is only placeable when it names/implies its parent tool or line.** A bare generic part
  (e.g. Ridgid "Plunger Knob", no parent named) on a store with no generic "Replacement Parts" bucket → review;
  do not guess a product line. Parts that name their parent (e.g. "ram for 258/258XL pipe cutters") place fine.
- **Recurring cross-listed items keep resurfacing** (fall-protection-store: same 3 WeatherGuard/Wright/Ergodyne
  items now 4 weeks running). They have no category and no brand fallback in that store → review every run until
  a human removes them or adds a fitting node. Flag for human action rather than force-placing them.

## 2026-08-03 (2026-W32) — cross-store patterns

### Engine / mechanics
- **`category_gids` (plural) is NOT supported by the installed `apply_run.py`.** The schema is exactly three
  slots: `category_gid`, `brand_gid`, `platform_gid`, unioned. Earlier lessons referencing a `category_gids`
  list describe an intent the installed engine does not implement — do not rely on it.
- **On a NON-dual-tree store the `brand_gid` slot is free, and `apply_run` resolves any node by gid** (the
  `brands` list is empty there, so every node is category-kind). Use it as a **second category slot** to place
  into a store's parallel structures. Used this run on RTS (`Recip Blades`, `SBTA Impact Wrenches`, `quik-lok`,
  `PACKOUT Accessories`) and gearwrench-shop (`Specialty Tool Sets` alongside `Diagnostic Scan Tools`).
- **⚠ `apply_run.py` does NOT chunk `add_cl_categorized.json` / `remove_niv2.json`.** On a 250-item run each
  holds 250 pairs — far over `shopify_bulk_apply_tags`' 30-pair ceiling. **Chunk them to <=30 yourself.**
  (MTS needed 9 + 9 chunks.) Recommend Adam add chunking to the engine.
- **`weekly_run.py` records no uncapped eligible total** — with `--max-items 250` the log only ever shows 250,
  so a capped store's true backlog can't be read from the run output. Affects MTS and the-jet-store.
- **Vacuous-batch skipping generalizes.** Compare each resolved (product, tag) pair against the product's
  `all_tags`: pairs already present add nothing. On MTS 1070/1121 pairs were vacuous, so 41 engine add-batches
  collapsed into 4 real calls. Always verify against `all_tags` before skipping.

### Classification
- **A vacuous brand/category match can look wrong and still be harmless.** Klein 50400 *Cable Bender*
  subset-matched the brand node `Klein Tools Bolt Cutters` because the product already carries a (merchant-set)
  `Bolt Cutters` tag. Since the closure is a subset of existing tags, applying it changes nothing — add-only
  makes the mismatch inert. Don't "fix" the merchant's tag (rule 10); just set the other tree correctly.
- **Check a platform-typed nav node's closure for a WRONG platform, not just a wrong department.** RTS's
  `Power Tools > Drilling & Fastening > Impact Wrenches` (`189687558`) carries **M12**, so it is wrong for an
  M18 tool. The clean fix is the matching platform node (`M18 > Drilling & Fastening > Impact Wrenches`) plus a
  Shop-By-Trade node for the trade structure. Rule 3 covers wrong *platforms* as much as wrong departments.
- **Attachment-system products** (Milwaukee QUIK-LOK pole saw / hedge trimmer / bristle brush) get the
  attachment's **own type leaf** where one exists, else the generic Outdoor-Tools parent, **plus** the
  attachment-system collection (`quik-lok`) **plus** the platform's outdoor node. Don't file a pole saw under
  Chainsaws — a pole saw is a distinct type, and the store keeps them separate.
- **Cutting media follows its tool family.** A chainsaw *chain* files with Saw Blades (it is the saw's cutting
  element); an *edger* blade files with Replacement Parts (not a saw). Match the medium to the tool, not to the
  word "blade".
- **"Holder" is ambiguous — read what it holds.** A belt-mounted tape-measure/hammer/knife/pliers holder →
  Tool Holsters (belt gear). A screwdriver replacement **bit** holder → Bit Holders (a tool accessory). Same
  word, different trees.
- **A generic Replacement Parts bucket is the difference between placement and review.** MTS has one
  (`80711876708`, `[Replacement Parts, Tool Accessories]`), so bare Greenlee pins / o-rings / screws placed
  cleanly. the-ridgid-store has none — only type-specific accessory nodes — so its bare plunger knob went to
  review for a 2nd week. **Recommend adding a generic Replacement Parts collection wherever it's missing;** it
  retires a whole recurring review class.
- **A store with no brand collection for a vendor has no bottom rung on the fallback ladder.** On
  fall-protection-store all three recurring items have `fallback_brand_gid: None`, so `apply_run` routes them to
  review by construction. That is the ladder working as designed, not a classification failure — escalate to a
  human (delist or add a node) instead of stretching an unrelated node to fit.
- **Recurring review entries are a signal, not a defect.** fall-protection-store's three cross-listed items are
  now on week 5. Report the streak explicitly each run so it reads as an open human action item.

### Tree-diff reading
- The routine "+N new categories" line stays a vocabulary-rebuild artifact on the mature stores (RTS +153,
  ATO +73 for the 5th week running). **But two diffs this week look genuine and deserve human eyes:**
  - **wood-shop-outlet: 239 -> 869 (+630)**, all named 3M product families (tapes, adhesives, filters,
    wound-care dressings). Looks like a real 3M catalog build-out; eligible was 0 so no impact yet, but these
    become valid targets next run.
  - **the-jet-store: 41 -> 188 (+147)**, overwhelmingly Guardian fall-protection collections. Independent
    confirmation that the Jet -> Guardian conversion is live in the store's navigation.
  Rule of thumb: a diff whose new names are **coherent product families for a different catalog** is a real
  merchant change; a diff full of promo-code handles and re-surfaced floating collections is the artifact.
