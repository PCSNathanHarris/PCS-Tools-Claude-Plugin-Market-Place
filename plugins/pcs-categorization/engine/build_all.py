"""
Sweep: build the category+tag tree for every non-Toolup store (promo excluded), ending RTS,
then aggregate per-store lessons into a cross-store synthesis.

  python build_all.py
"""

import json
import subprocess
import sys
from pathlib import Path

from build_category_map import STORE_SLUG

HERE = Path(__file__).resolve().parent
PROJECT = __import__("config").data_dir()  # persistent data dir (outside the plugin)

# Order: all non-Toolup stores, ending with RTS (the-milwaukee-store).
ORDER = [
    "the-pls-store", "the-jet-store", "the-makita-store", "fall-protection-store",
    "weather-guard-store", "fasteners-store", "the-sumner-store", "the-dewalt-store",
    "greenlee-store", "the-ridgid-store", "gearwrench-shop", "wood-shop-outlet",
    "occidentalleatheroutlet", "knaack-store", "toolup-my-tool-store", "the-milwaukee-store",
]
BLOCKED = {"the-klein-store": "menus field ACCESS_DENIED (app missing read_online_store_navigation scope)"}
EXCLUDED = {"toolupstore": "Toolup/TUP — NetSuite/manual, excluded by request"}

results = []
for s in ORDER:
    print(f"=== building {s} ===", flush=True)
    try:
        r = subprocess.run([sys.executable, "build_category_map.py", "--store", s],
                           cwd=str(HERE), capture_output=True, text=True, timeout=600)
        ok = r.returncode == 0
        tail = ((r.stdout or "")[-400:] + "\n" + (r.stderr or "")[-400:]) if not ok else ""
    except subprocess.TimeoutExpired:
        ok, tail = False, "TIMEOUT (>600s)"
    slug = STORE_SLUG.get(s, s)
    lj = PROJECT / "maps" / slug / "lessons.json"
    lessons = json.loads(lj.read_text(encoding="utf-8")) if (ok and lj.exists()) else None
    results.append({"store": s, "slug": slug, "ok": ok, "lessons": lessons, "tail": tail})
    print(("  OK   " if ok else "  FAIL ") + s, flush=True)

synth = PROJECT / "synthesis"
synth.mkdir(exist_ok=True)
(synth / "cross-store-lessons.json").write_text(json.dumps({
    "built": [r for r in results if r["ok"]],
    "failed": [{"store": r["store"], "tail": r["tail"]} for r in results if not r["ok"]],
    "blocked": BLOCKED, "excluded": EXCLUDED,
}, indent=2), encoding="utf-8")

L = ["# Cross-store category-tree synthesis", "",
     f"Built {sum(1 for r in results if r['ok'])}/{len(ORDER)} stores · "
     f"blocked {len(BLOCKED)} · excluded {len(EXCLUDED)}", "",
     "| Store | Theme | Menu (source) | Total | Category tree | Brand | Promo excl. | Primary src | Depth | no_tag | multi_tag |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in results:
    if not r["ok"] or not r["lessons"]:
        L.append(f"| {r['store']} | — | **FAILED** | | | | | | | | |")
        continue
    x = r["lessons"]
    mh = x["active_menu"] + (" ⚠fallback" if x.get("menu_fallback") else f" ({x.get('menu_source')})")
    L.append(f"| {r['store']} | {str(x['theme'])[:24]} | {mh} | {x['collections_total']} | "
             f"{x['category_tree_size']} | {x['brand_nodes']} | {x['promo_excluded']} | "
             f"{x['primary_subcollection_source']} | {x['max_nav_depth']} | {x['no_tag_rule']} | {x['multi_tag']} |")
L += ["", "## Blocked", ""]
for s, why in BLOCKED.items():
    L.append(f"- **{s}** — {why}")
L += ["", "## Excluded", ""]
for s, why in EXCLUDED.items():
    L.append(f"- **{s}** — {why}")
(synth / "cross-store-lessons.md").write_text("\n".join(L), encoding="utf-8")

print("\n=== SWEEP COMPLETE ===")
print(f"built {sum(1 for r in results if r['ok'])}/{len(ORDER)}; failed: {[r['store'] for r in results if not r['ok']]}")
print(f"  {synth / 'cross-store-lessons.md'}")
