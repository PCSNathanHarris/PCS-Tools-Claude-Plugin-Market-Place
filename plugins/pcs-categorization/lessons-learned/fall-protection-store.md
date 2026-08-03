# fall-protection-store — lessons

## 2026-07-07 (2026-W28) — 2 brand-only / 3 review / 2 NIV2 removed
- **SafeWaze anchor-install consumables/tools** (bulb rivets pack; hand rivet tool for installing 019-4006 roof anchors) → no category exists (store has anchors/harnesses/lanyards/lifelines/jobsite-safety but no fastener/tool/anchor-accessory bucket). Placed brand-only via `Shop By Brand > SafeWaze 93836214326` (fallback ladder last resort), NIV2 removed. Better than review since we know exactly what they are.
- **3 out-of-place items → REVIEW** (no category AND no brand fallback node): WeatherGuard truck-rack ratchet strap (weatherguard vendor, `Truck and Van Equipment`), Wright Tool torque wrench (`Hand Tools/Ratchets/Sockets` — no hand-tool tree here), Ergodyne hammer holster (`Tool Belts and Pouches` — no pouch category here). These look cross-listed from other stores' catalogs; a human should confirm whether they belong in the fall-protection store at all. Review Doc uploaded to Drive.
- **Store shape note:** fall-protection-store is a fall-protection specialty catalog (anchors, harnesses, lanyards, lifelines, retractables, jobsite safety, hard hats, PPE) with Shop-By-Brand nodes folded into categories (3M/DBI-Sala, Guardian, Werner, SafeWaze, etc.). It has NO hand-tool / fastener / tool-storage categories, so stray hand tools land in review.

## 2026-07-13 (2026-W29) — 0 classified / 0 NIV2 removed / 3 review (recurring)
- Same 3 cross-listed items as W28 resurfaced (they retain NIV2 by design): WeatherGuard truck-rack ratchet
  strap, Wright Tool torque wrench, Ergodyne hammer holster. Unchanged store shape → no category, no brand
  fallback for these vendors → review again. **These will resurface every run until a human either removes
  them from this store or a fitting category/brand node is added.** Recommend Nathan confirm they were
  cross-listed in error (belong in weather-guard-store / a hand-tool store / a tool-storage store).
- Review Doc re-uploaded to Drive. No tag writes (add-only; review items untouched, keep NIV2).

## 2026-07-20 (2026-W30) — 0 classified / 0 NIV2 removed / 3 review (recurring, 3rd week)
- Same 3 cross-listed items resurfaced AGAIN (WeatherGuard truck-rack ratchet strap `8306471207132`, Wright Tool
  torque wrench `8306470060252`, Ergodyne hammer holster `8306465865948`). Store shape unchanged → no category,
  no brand fallback → review. **3rd consecutive run (W28/W29/W30).** Review Doc uploaded to Drive. No tag writes.
  **ACTION FOR NATHAN:** almost certainly cross-listing errors — recommend removing them from fall-protection-store
  (or moving to weather-guard-store / a hand-tool store / a tool-storage store) so they stop recurring.

## 2026-07-28 (2026-W31) — 0 classified / 0 NIV2 removed / 3 review (recurring, 4th week)
- Same 3 cross-listed items resurfaced AGAIN (WeatherGuard truck-rack ratchet strap `8306471207132`, Wright Tool
  torque wrench `8306470060252`, Ergodyne hammer holster `8306465865948`). Store shape unchanged → no category,
  no brand fallback → review. **4th consecutive run (W28/W29/W30/W31).** Review Doc uploaded to Drive. No tag
  writes. **ACTION FOR NATHAN (repeat):** these are cross-listing errors — remove from fall-protection-store so
  they stop recurring every week.

## 2026-08-03 (2026-W32) — 0 classified / 0 NIV2 removed / 3 review  (5th consecutive week)
Same three cross-listed items as W28-W31: WeatherGuard 1057-52-01 ratchet straps (8306471207132), Wright Tool
3478 torque wrench (8306470060252), Ergodyne 13662 Arsenal hammer holster (8306465865948).
Tree diff +32 (vocabulary-build expansion); nothing created.
- **Confirmed structural cause:** all three have `fallback_brand_gid: None` — weatherguard, Wright Tool and
  Ergodyne have **no brand collection on this store**, so the no-zero-tags fallback ladder has no bottom rung
  and `apply_run` routes them to review by construction. This is not a classification failure; it is a
  catalog-scope mismatch that only a human can fix (delist, or add a node).
- **Store vocabulary is strictly fall protection + jobsite safety**: Harnesses, Lanyards, Anchors,
  Retractables, Lifeline Systems, Ladders, Guardrails, Netting, Rescue, Tool Tethers, Carabiners, plus PPE
  (hard hats, gloves, glasses, hearing, respiratory) and per-brand mirrors (3M/DBI Sala, Guardian, Safewaze,
  Werner, FallTech, Pyramex, Proto). There is **no hand-tool, truck-equipment, or tool-storage category at all.**
- **`Jobsite Safety > Tool Tethers` (`425428123868`) is NOT a home for holsters/pouches.** A tether prevents a
  drop; a holster carries a tool. Using it would apply a tag the product does not belong to (universal rule 3).
  The Ergodyne Arsenal line *is* dropped-object-prevention gear, so the right fix is a new
  **Tool Belts & Pouches** / **Dropped Object Prevention** collection, not a stretch into Tool Tethers.
- **Escalate rather than force-place.** Five weeks of identical review entries is the signal that the
  pipeline is working correctly and the backlog item is a human decision.
