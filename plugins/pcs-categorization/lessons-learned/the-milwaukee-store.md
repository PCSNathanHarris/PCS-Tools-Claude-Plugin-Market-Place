# the-milwaukee-store (RTS) — lessons

## 2026-06-30 — parallel category structures must ALL be tagged (rule 8c)
RTS runs three parallel structures, each with its own tag namespace; a product belongs in every one that
applies:
1. **Power Tools** tree — `Power Tools > Cutting > Saws` → tag `Saws` (+ `Power Tool Cutting`, `Power Tools`).
2. **Shop By Trade** tree — typed leaves with `SBTW …` (Woodworking) / `SBTM …` (Metal) / `SBTA …`
   (Automotive) tags, e.g. `SBTW Circular Saws`. These hang under grouping pages like **"Milwaukee Saws"**
   and "Milwaukee Carpentry Tools".
3. **Battery Platform** tree — M18 / M12 / MX FUEL.

**What went wrong (dry-run W27):** an M18 FUEL circular saw was tagged `SBTW Circular Saws` + `M18` only —
the Power-Tools `Saws` closure was missed because the "Milwaukee Saws" → "Milwaukee Circular Saws" link is a
template `collection-list` edge, which the build had treated as untrusted.

**Fixes (2026-06-30):**
- Build now **trusts a template edge whose parent is an in-nav node** ("Milwaukee Saws" is the nav Power-Tools
  "Saws" node), so the leaf inherits `Power Tool Cutting, Power Tools, Saws`. The off-nav "Milwaukee Carpentry
  Tools" stays untrusted, so its `carpentry-tools` handle tag is correctly NOT applied.
- Result: "Milwaukee Circular Saws" closure = `Power Tool Cutting, Power Tools, Saws, SBTW Circular Saws`;
  picking that node + the `M18` platform root tags the saw `M18, Power Tool Cutting, Power Tools, Saws,
  SBTW Circular Saws`. 28 RTS leaves (saw types, batteries/chargers) gained their structure closures.
- Where a structure is a genuinely separate node, use `category_gids` (list) to pick one node per structure.

**Heuristic:** RTS tag prefixes — `SBTW`/`SBTM`/`SBTA` = Shop-By-Trade (Woodworking/Metal/Automotive),
`SBT Automotive` = trade root. Plain product-type tags (`Saws`, `Grinders`, `Drills`) = Power Tools tree.
M18/M12/MX FUEL = platform. Confirm the closure in `tags_to_apply` spans every applicable namespace.
