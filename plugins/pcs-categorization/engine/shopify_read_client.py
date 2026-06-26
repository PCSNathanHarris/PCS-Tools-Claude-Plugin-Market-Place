"""
Strictly read-only Shopify Admin API client (standard library only).

Mirrors the OAuth client-credentials flow used by toolup-themes/mcp/client.py, but inverts
the safety guard: instead of allow-listing specific mutations, it REFUSES every operation
that contains `mutation` or `subscription`. Only GraphQL `query` operations are sent.

There are no REST POST/PUT/DELETE methods. This client cannot write or delete anything.
All store writes go through the audited shopify_* MCP tools — never through here.
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API_VERSION = "2025-10"
_TOKEN_REFRESH_BUFFER = 300  # refresh 5 min before the 24h token expires

_MUTATION_RE = re.compile(r"\bmutation\b", re.IGNORECASE)
_SUBSCRIPTION_RE = re.compile(r"\bsubscription\b", re.IGNORECASE)


class ReadOnlyViolation(PermissionError):
    """Raised when a non-read operation is passed to the read-only client."""


class ShopifyReadClient:
    def __init__(self, shop_domain: str, client_id: str, client_secret: str):
        self.shop_domain = shop_domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = f"https://{shop_domain}/admin/api/{API_VERSION}"
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # ── read-only guard ──────────────────────────────────────────────────────
    @staticmethod
    def assert_read_only(query: str) -> None:
        """Refuse anything that isn't a plain query. Conservative by design."""
        if _MUTATION_RE.search(query) or _SUBSCRIPTION_RE.search(query):
            raise ReadOnlyViolation(
                "ShopifyReadClient is read-only: operations containing 'mutation' or "
                "'subscription' are refused. Use the audited shopify_* MCP tools for writes."
            )

    # ── auth ─────────────────────────────────────────────────────────────────
    def _ensure_token(self) -> None:
        if self._token and time.time() < self._token_expires_at:
            return
        url = f"https://{self.shop_domain}/admin/oauth/access_token"
        body = json.dumps(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }
        ).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 86400) - _TOKEN_REFRESH_BUFFER

    # ── read ─────────────────────────────────────────────────────────────────
    def graphql_read(self, query: str, variables: dict | None = None, retries: int = 4) -> dict:
        """Execute a read-only GraphQL query and return its `data` payload."""
        self.assert_read_only(query)
        self._ensure_token()
        url = f"{self.base_url}/graphql.json"
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        body = json.dumps(payload).encode()

        for _ in range(retries):
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": self._token or "",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code == 401:  # token invalidated — refresh once and retry
                    self._token = None
                    self._ensure_token()
                    continue
                if e.code == 429:  # throttled — honor Retry-After
                    time.sleep(float(e.headers.get("Retry-After", "2")))
                    continue
                raise
            if "errors" in data:
                raise ValueError(f"GraphQL errors: {data['errors']}")
            return data.get("data", {})
        raise RuntimeError("Max retries exceeded (rate limit / auth)")

    def rest_get(self, endpoint: str, params: dict | None = None, retries: int = 4) -> dict:
        """
        Read-only REST GET (e.g. 'themes.json', 'themes/<id>/assets.json').
        Only GET is implemented — there is deliberately no POST/PUT/DELETE here.
        Used to resolve the live theme + its header menu setting.
        """
        self._ensure_token()
        url = f"{self.base_url}/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for _ in range(retries):
            req = urllib.request.Request(
                url, headers={"X-Shopify-Access-Token": self._token or ""}, method="GET"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    self._token = None
                    self._ensure_token()
                    continue
                if e.code == 429:
                    time.sleep(float(e.headers.get("Retry-After", "2")))
                    continue
                raise
        raise RuntimeError("Max retries exceeded (rate limit / auth)")
