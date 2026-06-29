"""
build_report.py — per-run categorization report workbook (READ-ONLY; writes only local files).

Produces the colored Excel report and drops it in the Google-Drive-for-Desktop synced folder so Drive
auto-uploads it. The report is NOT sent through the MCP Drive connector — a binary .xlsx and a full
multi-row sheet both blow past the connector's inline per-message ceiling, and the connector cannot make
tabs or cell colors. See reference/report-format.md.

Columns: Store, Shopify ID, Shopify Handle, Variant SKU, Title, Vendor, Category Tree Logic,
Proposed Tags Applied, Confidence (0-100). The Confidence cell is color-filled:
  red 0-33  |  yellow 34-66  |  green 67-100.

Confidence per product = the classifier's 0-100 score from decisions.json when present; otherwise a
deterministic signal proxy (existing-anchor overlap + facet presence + fallback flag).

Modes:
  --store <key>   targeted run -> one workbook, one tab, filename "<store>-<YYYY-MM-DD>-categorization.xlsx"
  (no --store)    weekly run  -> one workbook, ONE TAB PER STORE, "categorization-weekly-<YYYY-MM-DD>.xlsx"

Inputs (per store): <data_dir>/runs/<week>/<slug>/{candidates.json, decisions.json, fallback-tagged.json}.
Output: config.report_dir() (Drive-synced) + an audit copy under <data_dir>/runs/<week>/. If the report
dir is missing (Drive for Desktop not mounted), writes the audit copy and prints how to deliver it.

If xlsxwriter is unavailable, degrades to a single stacked CSV (no colors/tabs) and says so.
"""

import argparse
import csv
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

import config

try:
    import xlsxwriter
    HAVE_XLSX = True
except Exception:
    HAVE_XLSX = False

PROJECT = config.data_dir()

COLS = ["Store", "Shopify ID", "Shopify Handle", "Variant SKU", "Title", "Vendor",
        "Category Tree Logic", "Proposed Tags Applied", "Confidence (0-100)"]
WIDTHS = {"Store": 20, "Shopify ID": 15, "Shopify Handle": 34, "Variant SKU": 12, "Title": 46,
          "Vendor": 16, "Category Tree Logic": 60, "Proposed Tags Applied": 46, "Confidence (0-100)": 15}


def iso_week():
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w:02d}"


def order_closure(node):
    """Node closure with the leaf (node title) placed last for readability."""
    tags = list(node.get("tags_to_apply", []))
    leaf = node.get("title")
    return [t for t in tags if t != leaf] + ([leaf] if leaf in tags else [])


def score_proxy(cat_node, existing_cat_tags, has_facet, is_fallback):
    """Deterministic 0-100 used when the classifier didn't supply a numeric score."""
    if is_fallback:
        return 40
    ct = set(cat_node.get("tags_to_apply", [])) if cat_node else set()
    ov = (len(ct & set(existing_cat_tags)) / len(ct)) if ct else 0
    if ov >= 0.9:
        return 97
    if ov >= 0.6:
        return 91
    if ov >= 0.34:
        return 84
    if has_facet:
        return 78
    if ov > 0:
        return 72
    return 62


def resolve_confidence(dec, cat_node, existing_cat_tags, has_facet, is_fallback):
    c = dec.get("confidence")
    if isinstance(c, (int, float)) and 0 <= c <= 100:
        return int(c)
    if isinstance(c, str) and c.strip().isdigit() and 0 <= int(c.strip()) <= 100:
        return int(c.strip())
    # categorical ("high"/etc.) or missing -> deterministic proxy (more informative than a flat map)
    return score_proxy(cat_node, existing_cat_tags, has_facet, is_fallback)


def band(score):
    return "GREEN" if score >= 67 else ("YELLOW" if score >= 34 else "RED")


def load_store_rows(slug_dir):
    """Return (store_label, [row dicts]) for one store's run dir."""
    cand = json.loads((slug_dir / "candidates.json").read_text(encoding="utf-8"))
    dec = json.loads((slug_dir / "decisions.json").read_text(encoding="utf-8")).get("decisions", [])
    fb_ids = set()
    fb_path = slug_dir / "fallback-tagged.json"
    if fb_path.exists():
        for it in (json.loads(fb_path.read_text(encoding="utf-8")).get("items") or []):
            fb_ids.add(str(it.get("product_id")))
    store = cand.get("store") or slug_dir.name
    cb = {str(x["product_id"]): x for x in cand.get("candidates", [])}
    cat_l = {n["gid"]: n for n in cand.get("categories", [])}
    br_l = {n["gid"]: n for n in cand.get("brands", [])}
    pl_l = {n["gid"]: n for n in cand.get("platforms", [])}

    rows = []
    for d in dec:
        pid = str(d.get("product_id"))
        p = cb.get(pid, {})
        cn = cat_l.get(d.get("category_gid"))
        bn = br_l.get(d.get("brand_gid"))
        pn = pl_l.get(d.get("platform_gid"))
        cc = order_closure(cn) if cn else []
        bc = order_closure(bn) if bn else []
        pc = order_closure(pn) if pn else []
        if d.get("review") and not (cc or bc or pc):
            logic = "REVIEW: " + (d.get("reason") or "no confident placement")
            applied = ""
            c = d.get("confidence")
            score = int(c) if isinstance(c, str) and c.strip().isdigit() else (int(c) if isinstance(c, (int, float)) else 15)
        else:
            logic = "; ".join(filter(None, [
                "Cat: " + " > ".join(cc) if cc else "",
                "Brand: " + " > ".join(bc) if bc else "",
                "Platform: " + " > ".join(pc) if pc else "",
            ]))
            applied = " | ".join(sorted(set(cc) | set(bc) | set(pc)))
            score = resolve_confidence(d, cn, p.get("current_category_tags") or [],
                                       bool(p.get("facets_product_type")), pid in fb_ids)
        rows.append({
            "Store": store, "Shopify ID": pid, "Shopify Handle": p.get("handle", ""),
            "Variant SKU": p.get("sku", ""), "Title": p.get("title", ""), "Vendor": p.get("vendor", ""),
            "Category Tree Logic": logic, "Proposed Tags Applied": applied, "Confidence (0-100)": score,
        })
    return store, rows


def _safe_tab(name, used):
    n = re.sub(r"[\[\]:*?/\\]", " ", name).strip()[:31] or "Sheet"
    base, k = n, 2
    while n in used:
        n = f"{base[:28]}_{k}"
        k += 1
    used.add(n)
    return n


def write_xlsx(path, store_rows):
    wb = xlsxwriter.Workbook(str(path), {"in_memory": True})
    H = wb.add_format({"bold": True, "bg_color": "#1F2A44", "font_color": "white", "border": 1,
                       "text_wrap": True, "valign": "top"})
    BASE = wb.add_format({"border": 1, "valign": "top", "text_wrap": True})
    RED = wb.add_format({"border": 1, "align": "center", "bold": True, "bg_color": "#F4B6B6"})
    YEL = wb.add_format({"border": 1, "align": "center", "bold": True, "bg_color": "#F7E59B"})
    GRN = wb.add_format({"border": 1, "align": "center", "bold": True, "bg_color": "#B7E1A1"})
    used = set()
    for store, rows in store_rows:
        ws = wb.add_worksheet(_safe_tab(store, used))
        for j, c in enumerate(COLS):
            ws.write(0, j, c, H)
            ws.set_column(j, j, WIDTHS.get(c, 18))
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(rows), len(COLS) - 1)
        for i, r in enumerate(rows, 1):
            for j, c in enumerate(COLS):
                if c == "Confidence (0-100)":
                    s = int(r[c])
                    fmt = GRN if s >= 67 else (YEL if s >= 34 else RED)
                    ws.write_number(i, j, s, fmt)
                else:
                    ws.write(i, j, r[c], BASE)
    wb.close()


def write_csv(path, store_rows):
    """Degraded fallback (no colors, no tabs): one stacked CSV; Store column distinguishes stores."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLS + ["Confidence Band"])
        w.writeheader()
        for _, rows in store_rows:
            for r in rows:
                rr = dict(r)
                rr["Confidence Band"] = band(int(r["Confidence (0-100)"]))
                w.writerow(rr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default=None)
    ap.add_argument("--store", default=None,
                    help="single store key for a targeted run; omit for the weekly multi-store workbook")
    ap.add_argument("--slug", default=None, help="run-dir slug if it differs from the store key")
    a = ap.parse_args()

    week = a.week or iso_week()
    wk_dir = PROJECT / "runs" / week
    today = datetime.date.today().isoformat()

    if not wk_dir.exists():
        print(f"no run dir: {wk_dir}")
        sys.exit(1)

    store_rows = []
    if a.store:
        d = wk_dir / (a.slug or a.store)
        if not (d / "decisions.json").exists():
            # slug may differ from store key — find the dir whose candidates.json store matches
            d = next((x for x in wk_dir.iterdir()
                      if x.is_dir() and (x / "decisions.json").exists()
                      and json.loads((x / "candidates.json").read_text(encoding="utf-8")).get("store") == a.store), None)
        if d is None:
            print(f"no decisions.json for store '{a.store}' in {wk_dir}")
            sys.exit(1)
        store_rows.append(load_store_rows(d))
        base_name = f"{a.store}-{today}-categorization"
    else:
        dirs = sorted(x for x in wk_dir.iterdir() if x.is_dir() and (x / "decisions.json").exists())
        if not dirs:
            print(f"no store runs with decisions.json in {wk_dir}")
            sys.exit(1)
        for d in dirs:
            store_rows.append(load_store_rows(d))
        store_rows.sort(key=lambda sr: sr[0])
        base_name = f"categorization-weekly-{today}"

    fname = base_name + (".xlsx" if HAVE_XLSX else ".csv")
    writer = write_xlsx if HAVE_XLSX else write_csv

    # 1) audit copy in the run dir (local source of truth)
    audit = wk_dir / fname
    writer(audit, store_rows)
    total = sum(len(r) for _, r in store_rows)
    fmt_note = "xlsx" if HAVE_XLSX else "csv (xlsxwriter missing — NO colors/tabs; install xlsxwriter)"
    print(f"[report] {fname}: stores={len(store_rows)} rows={total} format={fmt_note}")
    print(f"  audit copy: {audit}")

    # 2) deliver to the Drive-synced report folder
    rd = config.report_dir()
    if rd.exists():
        dest = rd / fname
        shutil.copy2(audit, dest)
        print(f"  delivered:  {dest}")
        print("  Google Drive for Desktop will upload it automatically.")
    else:
        print(f"  DELIVERY DIR MISSING: {rd}")
        print("  Google Drive for Desktop is not mounted. Start it (or set PCS_REPORT_DIR), then copy")
        print(f"  the audit file into the folder. The report is ready at: {audit}")


if __name__ == "__main__":
    main()
