# Fetching the `kb.exe` CLI binary (private Release, `.env` token)

The Kit Builder ships as a prebuilt headless **`kb.exe`** (v0.5.22+) attached to
every Release of the **private** repo `PCSNathanHarris/pcs-kit-builder-lite`,
alongside the GUI `PCSKitBuilderLite.exe`. Windows operators run the kit stage
with **no Python / pip / Git** — Claude downloads `kb.exe` into the working
folder using the GitHub token in the `.env`. (`gh` CLI is not installed; use the
REST API + `curl`.)

## When to fetch
At **Step 0**, only after the operator confirms (Y/N). Skip the fetch if
`.\kb.exe` already exists and `.\kb.exe --version` is **≥ 0.5.22**.

## Token hygiene (do this every time)
- Read `GITHUB_TOKEN` from the `.env` in the working folder into a shell variable
  **in one command** — never `echo` it, never print the authenticated URL, never
  put it in chat output.
- PowerShell:
  ```powershell
  $tok = (Get-Content .env | Where-Object { $_ -match '^GITHUB_TOKEN=' }) -replace '^GITHUB_TOKEN=','' -replace '"','' ; $tok = $tok.Trim()
  ```
- Pass it only via the `Authorization: Bearer` header.

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
.\kb.exe --version    # must print "kb, version 0.5.22" or newer
```
First run may trip **SmartScreen** ("More info → Run anyway") — expected for an
unsigned in-house binary.

## Manual fallback (no automation)
Open the Release page for `PCSNathanHarris/pcs-kit-builder-lite` in a browser,
download `kb.exe` from the latest release's assets, and drop it in the working
folder. Then `.\kb.exe --version`.

## Notes
- **No auto-update.** Re-run this fetch when a new tag ships; the Step-0
  `--version` gate is what flags a stale/missing binary.
- **Windows only.** `kb.exe` is a Windows binary. On a non-Windows environment
  (e.g. a Linux sandbox where `kb build-imports` might run), use the source
  `pip install` fallback instead — see `prerequisites.md` §1.
- **Never** commit the token or `kb.exe` to a repo; both live only in the
  operator's working folder.
