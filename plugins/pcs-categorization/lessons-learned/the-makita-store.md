# the-makita-store — lessons

## 2026-07-07 (2026-W28) — 8 classified / 8 NIV2 removed / 0 review
- All 8 were fresh cordless tools (no anchors), all on a platform (XGT x6, LXT x2).
- **Makita category tree carries platform-typed nodes** whose closure is `[Type, Platform]` — e.g. `40V XGT > Cutting > Grinders 445030662461` = `[Grinders, XGT]`, `18V LXT > Drilling & Driving > Impact Wrenches 447685656893` = `[Impact Wrenches, LXT]`. Picking that ONE node gives type + platform; added the platform root too (XGT 448042860861 / LXT 448043090237) for redundancy/discoverability.
- **XGT has no typed Heat Guns node** -> used generic `Power Tools > Surfacing & Finishing > Heat Guns 444988129597` + XGT root. When a platform lacks a typed node for a category, use the generic Power-Tools type node + platform root (gives `[Type, Platform]`).
- Placements: grease gun->Grease Guns; magnetic work light->Lighting (XGT `445040918845` / LXT `445016146237`); flathead grinder->Grinders; angle impact wrench->Impact Wrenches; compact stick vacuum->Vacuums `445041377597`; heat gun->Heat Guns.
- Avoid the mislabeled `Makita LXT Vacuums 478856970557` (its tag list reads `[Vacuums, XGT]`); use the clean `40V XGT > System Enhancement > Vacuums`.
