# Reference — One-Click Runner (`run_backfill.bat`)

Generated into the working folder alongside `pdp_backfill.py`. The operator just
double-clicks it. First run sets up the environment; later runs reuse it. Uses the
operator's installed Chrome/Edge (no browser download — firewall-safe).

Write this file with CRLF line endings (it's a Windows batch file):

```bat
@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  PCS Facet Enrichment - PDP Backfill
echo ============================================================

REM --- 1. Ensure Python is available (hardened) ---
set PY=
where py     >nul 2>nul && set PY=py
if not defined PY ( where python >nul 2>nul && set PY=python )
if not defined PY (
  where winget >nul 2>nul && (
    echo Python not found. Installing it via winget - approve any Windows prompt...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    echo.
    echo Python was installed. Please CLOSE this window and double-click run_backfill.bat again.
    pause & exit /b 0
  )
  echo.
  echo [ACTION NEEDED] Python is required. The download page is opening now.
  echo Install Python 3.10+ and TICK "Add python.exe to PATH", then re-run this file.
  start "" https://www.python.org/downloads/
  pause & exit /b 1
)
%PY% --version

REM --- 2. One-time virtual environment + deps ---
if not exist ".venv\" (
  echo First-time setup: creating environment and installing dependencies...
  %PY% -m venv .venv || (echo [ERROR] venv failed & pause & exit /b 1)
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip >nul
  pip install playwright openpyxl || (echo [ERROR] pip install failed ^(check network/proxy^) & pause & exit /b 1)
  echo Setup complete.
) else (
  call .venv\Scripts\activate.bat
)

REM --- 3. Run the scan (uses system Chrome/Edge; no chromium download) ---
echo Running PDP backfill... watch the live counter below.
python pdp_backfill.py
set RC=%ERRORLEVEL%

echo ============================================================
if "%RC%"=="0" (echo Done. Output files are in this folder.) else (echo Finished with errors ^(code %RC%^).)
echo ============================================================
pause
```

## Notes
- `pdp_backfill.py` sets `BROWSER_CHANNELS = ["chrome","msedge",None]`, so it drives an installed browser; `playwright install chromium` is NOT required (that download is what corporate firewalls block).
- If `pip install` is blocked (PyPI filtered), fall back to the no-install path in `pdp-backfill-script.md` (urllib + embedded JSON) or run via Claude in Chrome.
- The `.bat` is generated, never committed to the marketplace repo (markdown-only rule).
