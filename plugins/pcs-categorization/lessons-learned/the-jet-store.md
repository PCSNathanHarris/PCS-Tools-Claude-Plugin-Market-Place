# the-jet-store — categorization lessons

_Read at the start of each run; appended at the end. Established heuristics float to the top._

## ⚠️ HOLD — do not mass-categorize yet
- **2026-07-28 (Nathan):** the-jet-store is being **repurposed into the "Guardian store," featuring fall
  protection.** Its category tree/vocabulary will change entirely. **HOLD ALL categorization here until Nathan
  writes in the new rules** for the Guardian/fall-protection catalog — do not classify or drain, even if the
  duplicate-creation issue looks resolved. Read this note at the start of every run; resume only after Nathan
  confirms the new rules are in place.
- Prior reason (still applies): the store had a **large number of DUPLICATE products** from an **ongoing
  product-creation error**; the `New Item V2` count (~2,851 as of 2026-06-26; 250 at W31) is **inflated by
  those duplicates**. Categorizing duplicates is wasted work and they will likely be deleted. Do not treat this
  count as real categorization demand. See [[project-automated-categorization]].

## Store shape
- (To be filled on the first real run once the duplicate issue is fixed.)

## 2026-07-07 (2026-W28) — ON HOLD, skipped (22 eligible, likely dup-inflated). No writes.

## 2026-07-13 (2026-W29) — ON HOLD, skipped (22 eligible, unchanged from W28, likely dup-inflated). No writes.

## 2026-07-20 (2026-W30) — ON HOLD, not drained
weekly_run reported eligible=26 (inflated by the duplicate-creation error). Per store-quirks, NOT drained. Read-only tree refresh only; no classification/writes/report. Resume once the duplicate-creation bug is fixed.

## 2026-07-28 (2026-W31) — ON HOLD, not drained
weekly_run reported eligible=250 (hit the `--max-items` cap; up sharply from W30's 26). This jump is consistent
with the still-unresolved duplicate-creation error continuing to generate items — NOT confirmed real demand. Per
store-quirks the store stays ON HOLD: read-only tree refresh only, no classification/writes/report. Tree-diff
+147 = vocabulary-rebuild artifact. **ACTION FOR NATHAN:** the eligible count is climbing (22→26→250); please
confirm the duplicate-creation bug status before we drain this store.

## 2026-08-03 (2026-W32) — ON HOLD, 0 classified (250 eligible, cap)
Refreshed read-only for visibility; **no classification, no writes**. Hold reasons: (1) the duplicate-creation
error still inflates the NIV2 count, (2) the store is being repurposed as the **Guardian fall-protection**
store and the new rules have not been written.
- **The tree diff is now hard evidence of the conversion:** category tags jumped **41 -> 188 (+147)** and the
  new nodes are overwhelmingly Guardian fall-protection collections (`Guardian 4 Way Plate Anchors`,
  `Guardian ATOMX SRLs`, …) plus a few generic tool nodes (`Air Tools`, `Air Tool Accessories`,
  `Specialty Tools`). The live navigation is being rebuilt around Guardian.
- Eligible count history: 22 -> 26 -> 250 (cap) -> 250 (cap). The cap makes it impossible to tell from
  `weekly_run` alone whether the true backlog is still growing — `weekly_run.py` records no total, only the
  capped count. Worth adding an uncapped count to the engine if the number matters.
- **Do not drain until:** the duplicate bug is confirmed fixed AND the Guardian-era category rules exist
  (which old Jet metalworking nodes survive, how the Guardian tree should be tagged).
