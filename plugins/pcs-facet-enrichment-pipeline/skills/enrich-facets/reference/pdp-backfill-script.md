# Reference — PDP Backfill Script (template)

Claude writes this `pdp_backfill.py` into the working folder at run time, configured
for the brand/run (markdown-only rule: never commit it). It scans real PDPs, fills
ONLY blank tree-linked attributes with HIGH-confidence values, validates ENUM values
strictly against `attributes (15).csv`, and proposes frequent out-of-dropdown values.

## Behavior contract (must hold)
- Source per SKU = brand-token URL first, else first available (see `brand-config.md`); retailer URL only as fallback for PDP-quality attrs.
- Fill **blanks only**, **tree-linked only**, **HIGH-confidence/explicit only**.
- Target the **backfill_plan** attributes first (gap-analysis driven).
- **Single value unless the key is one of `safety_rating` / `drive_size` / `battery_compatibility`** (the only multi-value attributes — then comma-join after dedupe). Never emit multiple values for any other attribute, even if `attributes (NN).csv` types it `MULTI_SELECT`. The NetSuite-format step also collapses any multi-value Anglera left in other fields.
- ENUM/MULTI_SELECT value written only if it matches a v15 dropdown after the normalization map; else not written.
- Out-of-dropdown values reasonably belonging to the attribute and seen on **> 5 products** → `dropdown_additions_needed.csv` (not written).
- Facet label = attribute `Name`. Read full HTML + `__NEXT_DATA__` for Compliance/Industries; clean visible text for description attrs.

## Provenance + AUTO / REVIEW split (v1.3.0)

Every value the scraper would write is classified before it lands. Attach provenance to each —
`source_url`, `source_kind` (`brand_pdp` | `retailer`), `attribute_key`/`attribute_label`,
`proposed_value`, a one-line `why_pulled` — and compute `review_reasons[]` from:

- **retailer-sourced** — the value came from the retailer-URL fallback, not the brand PDP;
- **normalized** — `normalize_raw`/the canon map changed the raw string to hit a dropdown entry;
- **inferred-from-prose** — the extractor is in `INFER_KEYS` (heuristic/keyword over visible text);
- **out-of-dropdown** — `validate()` returned `in_dropdown = False`;
- **multiple-candidate** — the extractor returned more than one value.

Then split:
- **AUTO** (`review_reasons` empty): write the xlsx cell + `*_GapFill_log.csv` exactly as before.
- **REVIEW** (≥ 1 reason): **do not write the cell.** Append the item to `*_review_queue.json`
  (+ human-readable `*_review_queue.csv`); it stays out of the import until the operator accepts it
  in the in-chat review (see `manual-review.md`). Out-of-dropdown values still also feed the
  `> 5 products` discovery list as before.

## Template

```python
#!/usr/bin/env python3
import asyncio, csv, json, re, sys
from pathlib import Path
from collections import defaultdict, Counter

# ---- CONFIG (Claude fills BRAND + confirms paths) ----
HERE = Path(__file__).resolve().parent
BRAND       = "{{BRAND}}"                       # e.g. "Guardian"
EXPORT_CSV  = HERE / "{{EXPORT_FILENAME}}"
ATTRS_CSV   = HERE / "attributes (15).csv"      # newest attributes master
TREE_CSV    = HERE / "TUP_Master_Facets_V2_export_cleaned_with_PT.csv"
PLAN_CSV    = HERE / "backfill_plan.csv"        # from gap analysis (optional)
OUT_XLSX    = HERE / f"{BRAND}_GapFill_PDP.xlsx"
OUT_LOG     = HERE / f"{BRAND}_GapFill_log.csv"
OUT_ADDS    = HERE / f"{BRAND}_dropdown_additions_needed.csv"
OUT_RQ_JSON = HERE / f"{BRAND}_review_queue.json"      # uncertain values, HELD for in-chat review
OUT_RQ_CSV  = HERE / f"{BRAND}_review_queue.csv"       # same, human-readable
CONCURRENCY = 5
PAGE_TIMEOUT_MS = 25000
BROWSER_CHANNELS = ["chrome", "msedge", None]
DISCOVERY_MIN = 6          # "> 5 products"
MULTI_KEYS = {"safety_rating", "drive_size", "battery_compatibility"}  # the ONLY attrs allowed multiple values
INFER_KEYS = {"application","material","lanyard_type","connection_type","connector_type"}  # heuristic/prose extractors -> always REVIEW
HARNESS_L2 = {"Body Harnesses","1 D-Ring Harnesses","2 D-Ring Harnesses","3 D-Ring Harnesses",
              "4 D-Ring Harnesses","5 D-Ring Hanesses","6 D-Ring Hanesses"}
BRAND_TOKEN = re.sub(r"[^a-z0-9]+","", BRAND.lower())

def norm(s): return re.sub(r"[^a-z0-9]+","", (s or "").lower())
def clean(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>"," ",html or "",flags=re.S|re.I)
    t = re.sub(r"<[^>]+>"," ",t); t = re.sub(r"&[a-z#0-9]+;"," ",t)
    return re.sub(r"\s+"," ",t).strip()

# ---- normalization map (resolve variants to existing dropdown value) ----
def normalize_raw(key, v):
    v = v.strip()
    if key in ("safety_rating",):
        v = re.sub(r"\bcsa\b","CSA Certified",v,flags=re.I)
        m = re.match(r"(ANSI(?:/ISEA)?\s*Z?\s*\d+\.\d+)", v, re.I)
        if m: v = re.sub(r"\s+"," ",m.group(1)).strip()
        else:
            m2 = re.match(r"(OSHA\s*\d+\.\d+)", v, re.I)
            if m2: v = m2.group(1)
    repl = {"telecoms":"Telecom", "self-retracting":"Self-Retracting (SRL)"}
    if v.lower() in repl: v = repl[v.lower()]
    return v

# ---- load attributes(15): key -> {name, type, canon{normval:canonical}} ----
ATTR = {}
for r in csv.DictReader(open(ATTRS_CSV, encoding="utf-8-sig")):
    drops = [d.strip() for d in (r["Dropdown Values"] or "").split(",") if d.strip()]
    ATTR[r["Key"]] = {"name": r["Name"], "type": r["Type"],
                      "canon": {norm(d): d for d in drops}, "has_dropdown": bool(drops)}
LABEL2KEY = {a["name"]: k for k,a in ATTR.items()}

def validate(key, raw):
    """Return (value or None, in_dropdown, match_kind).
    match_kind: 'exact' | 'normalized' | 'free_text' | 'out_of_dropdown'."""
    a = ATTR.get(key)
    if not a: return None, False, "out_of_dropdown"
    raw_s = (raw or "").strip()
    v = normalize_raw(key, raw)
    changed = (v != raw_s)
    if a["type"] in ("ENUM","MULTI_SELECT") and a["has_dropdown"]:
        c = a["canon"].get(norm(v))
        if c: return c, True, ("normalized" if (changed or c != v) else "exact")
        return v, False, "out_of_dropdown"   # not in dropdown -> held for review + discovery
    return v, True, ("normalized" if changed else "free_text")   # STRING/NUMBER/CATEGORY: free text

# ---- tree linkage + backfill plan ----
tree = {}
for r in csv.DictReader(open(TREE_CSV, encoding="utf-8-sig")):
    l2 = (r.get("Level 2") or "").strip()
    if l2: tree[l2] = set(a for a in [(r.get(f"Attr {i}") or "").strip() for i in range(1,10)] if a)
plan = defaultdict(list)   # L2 -> ordered target keys
if PLAN_CSV.exists():
    for r in csv.DictReader(open(PLAN_CSV, encoding="utf-8-sig")):
        plan[r["L2"]].append(r.get("Attribute (key)") or r.get("Attribute"))

# ---- export ----
rows = list(csv.DictReader(open(EXPORT_CSV, encoding="utf-8-sig")))
hdr = list(rows[0].keys())
facet_cols = [h for h in hdr if h.startswith("Facet")]
sr_cols = [f"Safety Rating {i}" for i in range(1,11)]
src_cols = [h for h in hdr if h.startswith("Source URL")]

def pick_sources(r):
    urls = [(r.get(c) or "").strip() for c in src_cols if (r.get(c) or "").strip()]
    vendor = next((u for u in urls if BRAND_TOKEN and BRAND_TOKEN in norm(u)), "")
    if not vendor and urls: vendor = urls[0]
    retailer = next((u for u in urls if u != vendor), "")
    return vendor, retailer

# ---- extractors (return RAW candidate; validate() gates it) ----
IND = ["Construction","Roofing","Transportation","Mining","Oil & Gas","Telecom","Telecoms","Renewables",
       "General Industry","Engineering Firm","Utility","Demolition","Painting","Welding","Manufacturing","Maintenance"]
def x_application(vis, full, title):
    s = (title+" "+vis).lower()
    for pat,val in [(r"rebar|concrete contractor|concrete or rebar","Concrete Work"),
                    (r"roofing|roofer|roof anchor|roof bracket","Roofing"),
                    (r"wind turbine|turbine","Renewables"),
                    (r"tower climb|communication tower|cell tower|telecom","Telecom"),
                    (r"oil and gas|oil & gas|refinery","Oil & Gas"),
                    (r"\bmining\b|\bminer","Mining"),(r"lineman|electrical utility|power line","Utility"),
                    (r"\bdemolition\b","Demolition"),(r"for welding|welders\b","Welding"),
                    (r"for painting|painters\b","Painting")]:
        if re.search(pat,s): return val
    # else first specific industry from full HTML (skip generics)
    m = re.search(r"industr(?:y|ies)", full, re.I)
    scope = full[m.end():m.end()+400] if m else ""
    hits = [(scope.lower().find(i.lower()), i) for i in IND if i.lower() in scope.lower()]
    spec = [i for _,i in sorted(hits) if i.lower() not in ("construction","general industry")]
    if spec: return spec[0]
    return sorted(hits)[0][1] if hits else None
def x_safety(vis, full, title):
    m = re.search(r"compliance", full, re.I); scope = full[m.start():m.start()+600] if m else full
    std = re.findall(r"ANSI(?:/ISEA)?\s*Z?\s*\d+\.\d+[A-Za-z0-9.\-]*|OSHA\s*19\d\d\.\d+|CSA(?:\s*Certified)?", scope, re.I)
    return std or None     # list -> multi
def x_connector(vis, full, title):
    s=(title+" "+vis).lower()
    for pat,val in [(r"rebar hook|form hook","Rebar Hook"),(r"carabiner","Carabiner"),
                    (r"snap hook","Snap Hook"),(r"d-?ring","D-Ring")]:
        if re.search(pat,s): return val
    return None
def x_material(vis, full, title):
    s=(title+" "+vis).lower()
    if "stainless steel" in s: return "Stainless Steel"
    if re.search(r"steel cable|galvanized steel|steel construction|powder[- ]coated steel|forged steel",s): return "Steel"
    if "aluminum" in s: return "Aluminum"
    if re.search(r"nylon webbing|polyester webbing|\bwebbing\b",s): return "Webbing"
    return None
def x_lanyard_type(vis, full, title):
    s=(title+" "+vis).lower()
    for pat,val in [(r"non[ -]?shock","Non-Shock Absorbing"),(r"self[- ]retract","Self-Retracting (SRL)"),
                    (r"stretch|bungee","Stretch"),(r"positioning","Positioning"),(r"restraint","Restraint"),
                    (r"shock[ -]?absorb|energy[ -]?absorb","Shock-Absorbing")]:
        if re.search(pat,s): return val
    return None
COLORS=["High Visibility","Hi-Vis","Orange","Yellow","Black","Green","Red","Blue","White","Silver","Camo","Gray","Brown","Tan"]
def x_color(vis, full, title):
    for c in COLORS:
        if re.search(r"\b"+re.escape(c.lower())+r"\b", title.lower()):
            return "Hi-Vis Yellow" if c in ("High Visibility","Hi-Vis") else c
    return None
def x_beam(vis, full, title):
    m=re.search(r"(\d+(?:\.\d+)?)\s*(?:in(?:ch(?:es)?)?)?\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*in(?:ch(?:es)?)?\s*beam",title+" "+vis,re.I)
    return f"{m.group(1)} in-{m.group(2)} in" if m else None
def x_len(vis, full, title):
    m=re.search(r"(\d+(?:\.\d+)?)\s*(?:ft|foot|feet|')", title+" "+vis); return f"{m.group(1)} ft" if m else None
def x_wcap(vis, full, title):
    m=re.search(r"(?:capacity|rated|user weight)[^\d]{0,20}(\d{3})\s*lb", title+" "+vis, re.I); return f"{m.group(1)} lb" if m else None

EXTRACT = {"application":x_application,"safety_rating":x_safety,"connection_type":x_connector,
           "connector_type":x_connector,"material":x_material,"lanyard_type":x_lanyard_type,
           "color":x_color,"beam_width_range":x_beam,"cable_length":x_len,"lanyard_length":x_len,
           "weight_capacity":x_wcap}
PDP_QUALITY = {"weight_capacity","color","cable_length","lanyard_length"}

async def render(page, url):
    try:
        await page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
        await page.wait_for_timeout(500)
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(300)
            for kw in ("Compliance","Industries","Specifications"):
                try: await page.get_by_text(kw, exact=False).first.click(timeout=1000)
                except Exception: pass
        except Exception: pass
        return await page.inner_text("body"), await page.content()
    except Exception: return "", ""

def parse(vis, html):
    full = clean(html)
    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html or "", re.S)
    if m: full += " " + re.sub(r"\s+"," ",m.group(1))
    return vis, full

async def main():
    from playwright.async_api import async_playwright
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font
    cache={}; sem=asyncio.Semaphore(CONCURRENCY); prog={"d":0,"t":0,"e":0}
    async with async_playwright() as p:
        browser=None
        for ch in BROWSER_CHANNELS:
            try: browser=await (p.chromium.launch(headless=True,channel=ch) if ch else p.chromium.launch(headless=True)); print("browser:",ch or "chromium"); break
            except Exception as e: print("  no",ch,str(e)[:60])
        if not browser: sys.exit("No browser. Install Chrome/Edge.")
        ctx=await browser.new_context()
        async def getsig(u):
            if u in cache: return cache[u]
            async with sem:
                pg=await ctx.new_page(); vis,html=await render(pg,u); await pg.close()
            sig=parse(vis,html) if (vis or html) else None
            cache[u]=sig; prog["d"]+=1; prog["e"]+= (0 if sig else 1)
            print(f"[{prog['d']}/{prog['t']}] {'ok' if sig else 'EMPTY'}  {u[:66]}",flush=True); return sig
        # prefetch unique URLs
        need=set()
        for r in rows:
            v,ret=pick_sources(r)
            if v: need.add(v)
            if ret: need.add(ret)
        prog["t"]=len(need); print(f"Scanning {len(need)} unique PDPs...")
        await asyncio.gather(*(getsig(u) for u in need))

        log=[]; review=[]; disc=defaultdict(Counter); disc_samples=defaultdict(lambda: defaultdict(list))
        for r in rows:
            l2=(r.get("Master Facet Category") or "").strip(); title=r.get("Page Title") or ""
            linked=tree.get(l2,set())
            present=set()
            for fc in facet_cols:
                c=r.get(fc,"")
                if c and ":" in c: present.add(LABEL2KEY.get(c.split(":",1)[0].strip(), keyify_label(c)))
            if any((r.get(s) or "").strip() for s in sr_cols): present.add("safety_rating")
            # target order: backfill plan first, then any other tree-linked
            targets=[k for k in plan.get(l2,[]) if k in linked] + [k for k in linked if k not in plan.get(l2,[])]
            v,ret=pick_sources(r); vsig=cache.get(v); rsig=cache.get(ret)
            r["_added"]=[]
            for key in targets:
                if key in present or key not in EXTRACT: continue
                if key=="connection_type" and l2 in HARNESS_L2: continue
                # source: brand PDP first; retailer only as a PDP-quality fallback
                src_url, src_kind, sig = v, "brand_pdp", (vsig if vsig else None)
                raw = EXTRACT[key](*sig, title) if sig else None
                if not raw and rsig and key in PDP_QUALITY:
                    raw = EXTRACT[key](*rsig, title); src_url, src_kind, sig = ret, "retailer", rsig
                if not raw: continue
                rawlist = raw if isinstance(raw, list) else [raw]
                multi_candidate = len(rawlist) > 1
                canon=[]; mkinds=set(); had_ood=False
                for rv in rawlist:
                    cv, ok, mk = validate(key, rv)
                    if not cv: continue
                    mkinds.add(mk); canon.append(cv)
                    if not ok:   # reasonable value, not in the dropdown -> hold + propose
                        had_ood=True
                        disc[key][cv]+=1
                        if len(disc_samples[key][cv])<3: disc_samples[key][cv].append(r.get("Internal ID","").strip())
                if not canon: continue
                if key not in MULTI_KEYS: canon=canon[:1]   # only safety_rating/drive_size/battery_compatibility may be multi
                else:
                    seen=set(); canon=[x for x in canon if not (x in seen or seen.add(x))]
                val=", ".join(canon); label=ATTR[key]["name"]
                # classify: any reason -> HELD for review; none -> AUTO-written
                reasons=[]
                if src_kind=="retailer": reasons.append("retailer-sourced")
                if "normalized" in mkinds: reasons.append("normalized")
                if key in INFER_KEYS: reasons.append("inferred-from-prose")
                if had_ood: reasons.append("out-of-dropdown")
                if multi_candidate: reasons.append("multiple-candidate")
                if reasons:
                    review.append({
                        "item_id": f"{r.get('Internal ID','').strip()}::{key}",
                        "internal_id": r.get("Internal ID","").strip(),
                        "product_title": r.get("Input Product Name") or title,
                        "attribute_key": key, "attribute_label": label,
                        "proposed_value": val, "source_url": src_url, "source_kind": src_kind,
                        "why_pulled": f'{label}: read "{val}" from the {src_kind.replace("_"," ")} page',
                        "review_reasons": reasons,
                    })
                    continue   # HELD — not written until the operator accepts it (manual-review.md)
                # AUTO (high-confidence): write the cell + log it, as before
                tgt=next((fc for fc in facet_cols if not (r.get(fc) or "").strip()), None)
                if not tgt: break
                r[tgt]=f"{label}: {val}"; r["_added"].append(tgt); present.add(key)
                if key=="safety_rating":
                    st=next((s for s in sr_cols if not (r.get(s) or "").strip()),None)
                    if st: r[st]=canon[0]; r["_added"].append(st)
                log.append((r.get("Internal ID","").strip(),l2,label,val,src_url))
        await browser.close()

    # write xlsx + log + discovery
    GREEN=PatternFill("solid",fgColor="C6EFCE"); HEAD=PatternFill("solid",fgColor="1F3864"); HF=Font(color="FFFFFF",bold=True)
    wb=Workbook(); ws=wb.active; ws.title="Backfill (PDP-filled)"
    for c,h in enumerate(hdr,1): x=ws.cell(1,c,h); x.fill=HEAD; x.font=HF
    for i,r in enumerate(rows,2):
        ad=set(r.get("_added",[]))
        for c,h in enumerate(hdr,1):
            cell=ws.cell(i,c,r.get(h,""))
            if h in ad: cell.fill=GREEN
    ws2=wb.create_sheet("Value-Adds")
    for c,h in enumerate(["Internal ID","L2","Attribute","Value","Source PDP"],1): ws2.cell(1,c,h)
    for i,row in enumerate(log,2):
        for c,v in enumerate(row,1): ws2.cell(i,c,v)
    wb.save(OUT_XLSX)
    with open(OUT_LOG,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["Internal ID","L2","Attribute","Value","Source PDP"]); w.writerows(log)
    with open(OUT_ADDS,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["Attribute","Proposed Value","Occurrences","Sample SKUs","Suggested Action"])
        for key,cnt in disc.items():
            for val,n in cnt.most_common():
                if n>=DISCOVERY_MIN:
                    w.writerow([ATTR[key]["name"],val,n,"; ".join(disc_samples[key][val]),"ADD (review)"])
    # review queue — uncertain values HELD for the in-chat accept/reject step (see manual-review.md)
    with open(OUT_RQ_JSON,"w",encoding="utf-8") as f:
        json.dump(review, f, indent=2, ensure_ascii=False)
    with open(OUT_RQ_CSV,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(["item_id","Internal ID","Product","Attribute","Proposed Value","Source URL","Source","Why pulled","Review reasons"])
        for it in review:
            w.writerow([it["item_id"],it["internal_id"],it["product_title"],it["attribute_label"],
                        it["proposed_value"],it["source_url"],it["source_kind"],it["why_pulled"],
                        "; ".join(it["review_reasons"])])
    print(f"\nDONE. {len(log)} AUTO values across {len(set(x[0] for x in log))} SKUs; {len(review)} HELD for review. Empty pages: {prog['e']}.")
    print(f"Wrote {OUT_XLSX.name}, {OUT_LOG.name}, {OUT_ADDS.name}, {OUT_RQ_JSON.name}, {OUT_RQ_CSV.name}")

def keyify_label(cell): return re.sub(r"[^a-z0-9]+","_",cell.split(":",1)[0].strip().lower()).strip("_")

if __name__ == "__main__":
    asyncio.run(main())
```

## Tailoring notes for Claude
- Fill `{{BRAND}}` and `{{EXPORT_FILENAME}}`; confirm the attributes/tree filenames are the newest present.
- The `EXTRACT` map ships with fall-protection + general tool extractors. For a new vertical, add/adjust per-attribute extractors — but **never loosen** the `validate()` gate; new vocabulary should flow through discovery, not be force-written.
- `validate()` is the universal guardrail: ENUM values must resolve to a dropdown entry (after normalization) or they go to discovery, never to output.
- **`INFER_KEYS`** lists the heuristic/prose extractors (application, material, lanyard_type, connector). Their values are sound enough to *propose* but are **always routed to REVIEW**, never AUTO-written — the operator confirms them in the in-chat step. Add a new vertical's prose-guess extractors here too.
- No-`pip` fallback: if Playwright can't be installed, swap `render()` for a `urllib.request` fetch of the page HTML (Next.js `__NEXT_DATA__` is in the static HTML); everything downstream is unchanged.
