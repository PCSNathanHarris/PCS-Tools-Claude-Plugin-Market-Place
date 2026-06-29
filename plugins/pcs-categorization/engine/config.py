"""
Credential resolution for the read-only category reader.

Reuses the toolup-themes MCP credential source (stores.config.json + .env) so there is
ONE source of truth and no secrets are copied into this project. Nothing here writes.

Override the MCP directory location with the MCP_DIR environment variable if the repo
lives somewhere other than the default below.
"""

import json
import os
from pathlib import Path

# Default location of the toolup-themes `mcp/` directory (credential source).
_DEFAULT_MCP_DIR = Path(
    r"C:\Users\NathanHarris\OneDrive - Fasteners Inc\Documents\Theme Templates\toolup-themes\mcp"
)

# Persistent DATA dir (maps/, lessons-learned/, runs/). MUST live OUTSIDE the plugin so plugin
# auto-updates never clobber state. Defaults to the original Automated Categorization project;
# override with PCS_CATEGORIZATION_DATA.
_DEFAULT_DATA_DIR = Path(
    r"C:\Users\NathanHarris\Claude Project Files\Automated Categorization"
)

# REPORT dir = where per-run report workbooks are written. Defaults to the Google-Drive-for-Desktop
# synced folder so Drive auto-uploads them (the colored .xlsx cannot go through the MCP connector —
# see reference/report-format.md). Override with PCS_REPORT_DIR. Drive for Desktop must be running
# for the default path to exist during a cron run; build_report.py falls back to the run dir otherwise.
_DEFAULT_REPORT_DIR = Path(
    r"G:\My Drive\Claude Shopify Categorization Reviews"
)

# Marketplace repo (the published plugin source). sync_repo.py commits + pushes lessons-learned/ and
# change-reports/ here at the end of a weekly run. Override with PCS_PLUGIN_REPO. Not created — if it's
# absent (e.g. a machine without the repo cloned), sync_repo.py skips the push and logs it.
_DEFAULT_PLUGIN_REPO = Path(
    r"C:\Users\NathanHarris\Claude Project Files\Kit Builder Tool\PCS-Tools-Claude-Plugin-Market-Place"
)


def mcp_dir() -> Path:
    return Path(os.environ.get("MCP_DIR", str(_DEFAULT_MCP_DIR)))


def data_dir() -> Path:
    d = Path(os.environ.get("PCS_CATEGORIZATION_DATA", str(_DEFAULT_DATA_DIR)))
    d.mkdir(parents=True, exist_ok=True)
    return d


def report_dir() -> Path:
    """Where report workbooks land (Drive-for-Desktop synced folder by default). NOT created here —
    if it doesn't exist (Drive not running / different machine), build_report.py falls back to the run
    dir and logs it. Override with PCS_REPORT_DIR."""
    return Path(os.environ.get("PCS_REPORT_DIR", str(_DEFAULT_REPORT_DIR)))


def repo_dir() -> Path:
    """Marketplace repo root for auto-committing lessons + change reports (sync_repo.py). NOT created —
    if absent (machine without the repo), sync_repo.py skips the push and logs it. Override PCS_PLUGIN_REPO."""
    return Path(os.environ.get("PCS_PLUGIN_REPO", str(_DEFAULT_PLUGIN_REPO)))


def _parse_env_file(path: Path) -> dict:
    """Minimal .env reader: KEY=VALUE lines. Ignores blanks, comments, surrounding quotes."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def load_store_config(directory: Path | None = None) -> dict:
    directory = directory or mcp_dir()
    with open(directory / "stores.config.json", encoding="utf-8") as f:
        return json.load(f)["stores"]


def get_store_credentials(store_key: str, directory: Path | None = None) -> tuple[str, str, str]:
    """
    Return (shop_domain, client_id, client_secret) for `store_key`.
    Reads real environment first, then falls back to the MCP `.env` file. Read-only.
    """
    directory = directory or mcp_dir()
    stores = load_store_config(directory)
    if store_key not in stores:
        raise ValueError(f"Store '{store_key}' not found. Available: {sorted(stores)}")
    store = stores[store_key]

    file_env = _parse_env_file(directory / ".env")

    def _get(name: str) -> str | None:
        return os.environ.get(name) or file_env.get(name)

    client_id = _get(store["client_id_env"])
    client_secret = _get(store["client_secret_env"])
    if not client_id or not client_secret:
        raise ValueError(
            f"Credentials not set for '{store_key}'. Expected {store['client_id_env']} and "
            f"{store['client_secret_env']} in the environment or {directory / '.env'}."
        )
    return store["shop_domain"], client_id, client_secret
