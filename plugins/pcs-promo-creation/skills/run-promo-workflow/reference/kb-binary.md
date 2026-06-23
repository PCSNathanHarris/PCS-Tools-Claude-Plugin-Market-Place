# Fetching the Kit Builder CLI binary (private Release, `.env` token)

The Kit Builder ships as a prebuilt headless CLI on every Release of the **private**
repo `PCSNathanHarris/pcs-kit-builder-lite` (alongside the GUI `PCSKitBuilderLite.exe`):
**`kb.exe`** for Windows (v0.5.22+) and **`kb-macos`** for macOS (v0.5.24+). Operators
run the kit stage with **no Python / pip / Git** — Claude downloads the right binary into
the working folder using the GitHub token. (`gh` CLI is not installed; use the REST API +
`curl`.)

**Pick by platform:**
- **Windows** → fetch `kb.exe`; call `.\kb.exe` (PowerShell flow below).
- **macOS** → fetch `kb-macos`; `chmod +x` + clear Gatekeeper quarantine; call `./kb-macos`
  (see "macOS" section below).
- **Linux** (Claude's sandbox) → there is **no binary**; install from source via pip
  (`prerequisites.md` §1).

## When to fetch
At **Step 0, before parsing** — settle the Kit Builder up front; never defer the
install to the kit stage. Skip the fetch if the platform binary already exists
(`.\kb.exe` on Windows / `./kb-macos` on macOS) and `--version` is **≥ 0.5.24**.
Otherwise (missing/old):
- **A token file is present** (found per *Find + read the token* below) → fetch
  **immediately**, no Y/N (the token's presence is the go-ahead). Announce
  `Installing the Kit Builder (kb.exe) from the private Release…` and download.
- **No token file found** → do **not** fetch and do **not** stop the run. Tell
  the operator to ask their admin for the GitHub token `.env` file (drop it in
  this folder, re-run) **if** they want kit building, and offer to continue
  without it — deck parsing + Jira still run; the kit stages are skipped. This is
  **Gate 0** in `pipeline-and-gates.md`.

## Find + read the token (robust — do this every time)
Don't assume the file is named `.env` or that the line is `GITHUB_TOKEN=`. The
token may sit in a **subfolder** (e.g. `Token/`), in a **differently-named file**
(e.g. `… github_p.env`), and may be a bare value or a human-labeled line.

1. **Locate it** — search the working folder **and one level of subfolders** for a
   likely file: `.env`, `*.env`, or any name containing `token` (case-insensitive).
2. **Extract by token shape, not by key** — match a fine-grained PAT
   `github_pat_[A-Za-z0-9_]+` **or** a classic token `ghp_[A-Za-z0-9]+`. This handles
   `GITHUB_TOKEN=ghp_…`, a bare `github_pat_…` line, and a human-labeled
   `Promo Kit Tool Git Token - github_p…` line alike.
3. **Never echo it** — read into a variable in one command; never print the token or
   any authenticated URL; pass it only via the `Authorization: Bearer` header.

PowerShell (Windows):
```powershell
$f   = Get-ChildItem -Path . -Recurse -Depth 1 -File -ErrorAction SilentlyContinue |
       Where-Object { $_.Name -match '(?i)(\.env$|token)' } | Select-Object -First 1
$tok = [regex]::Match((Get-Content $f.FullName -Raw), 'github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+').Value
```
Bash (Linux / Cowork sandbox):
```bash
tok=$(grep -rhoE 'github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+' \
        --include='.env' --include='*.env' --include='*[Tt]oken*' . 2>/dev/null | head -n1)
```

## Step 1 — resolve the latest Release + find the `kb.exe` asset id
```powershell
curl -sSL -H "Authorization: Bearer $tok" `
     -H "Accept: application/vnd.github+json" `
     -H "X-GitHub-Api-Version: 2022-11-28" `
     https://api.github.com/repos/PCSNathanHarris/pcs-kit-builder-lite/releases/latest `
     -o release.json
$rel     = Get-Content release.json | ConvertFrom-Json
$assetId = ($rel.assets | Where-Object { $_.name -eq 'kb.exe' }).id
$tag     = $rel.tag_name
```
If no asset named `kb.exe` is found, stop and tell the operator the latest
Release predates v0.5.22 (no binary yet) — fall back to the source `pip install`
(see `prerequisites.md` §1) or download a newer Release manually.

## Step 2 — download the asset bytes (the redirect)
Asset bytes come from the **asset API endpoint** with `Accept:
application/octet-stream`; GitHub returns a 302 to a signed storage URL. `curl -L`
follows it, and curl drops the `Authorization` header on the cross-host hop
(correct — the storage URL is pre-signed):
```powershell
curl -sSL -H "Authorization: Bearer $tok" `
     -H "Accept: application/octet-stream" `
     -H "X-GitHub-Api-Version: 2022-11-28" `
     https://api.github.com/repos/PCSNathanHarris/pcs-kit-builder-lite/releases/assets/$assetId `
     -o kb.exe
Remove-Item release.json
```
Write `kb.exe` into the **working / Cowork folder** (next to `.env`). All later
calls use `.\kb.exe …`.

## Step 3 — verify
```powershell
.\kb.exe --version    # must print "kb, version 0.5.24" or newer
```
First run may trip **SmartScreen** ("More info → Run anyway") — expected for an
unsigned in-house binary.

## macOS — fetch `kb-macos` (bash / Terminal)
Same private-Release flow, but the asset is **`kb-macos`** and it must be made executable
and un-quarantined (it's unsigned):
```bash
# $tok discovered per "Find + read the token" (bash variant above)
curl -sSL -H "Authorization: Bearer $tok" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/PCSNathanHarris/pcs-kit-builder-lite/releases/latest > release.json
aid=$(python3 -c "import json;print(next(a['id'] for a in json.load(open('release.json'))['assets'] if a['name']=='kb-macos'))")
curl -sSL -L -H "Authorization: Bearer $tok" -H "Accept: application/octet-stream" \
  https://api.github.com/repos/PCSNathanHarris/pcs-kit-builder-lite/releases/assets/$aid -o kb-macos
rm -f release.json
chmod +x kb-macos
xattr -dr com.apple.quarantine kb-macos 2>/dev/null || true   # clear Gatekeeper quarantine
./kb-macos --version    # must print "kb, version 0.5.24" or newer
```
First launch may still trip **Gatekeeper** ("unidentified developer") — right-click → Open
once, or the `xattr` above clears it. `kb-macos` is **arm64** (Apple Silicon); on an Intel
Mac it won't run — fall back to the source `pip install` (`prerequisites.md` §1).

## Manual fallback (no automation)
Open the Release page for `PCSNathanHarris/pcs-kit-builder-lite` in a browser,
download `kb.exe` from the latest release's assets, and drop it in the working
folder. Then `.\kb.exe --version`.

## Notes
- **No auto-update.** Re-run this fetch when a new tag ships; the Step-0
  `--version` gate is what flags a stale/missing binary.
- **Platform binaries:** `kb.exe` (Windows) + `kb-macos` (macOS, arm64) ship on the
  Release. On **Linux** (e.g. Claude's sandbox) there's no binary — use the source
  `pip install` fallback (`prerequisites.md` §1). An **Intel Mac** also uses the source
  fallback (the binary is arm64-only).
- **Never** commit the token or `kb.exe` to a repo; both live only in the
  operator's working folder.
