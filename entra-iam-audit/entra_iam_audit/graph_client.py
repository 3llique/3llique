from __future__ import annotations

import requests

from .auth import GraphAuth

BASE_URL = "https://graph.microsoft.com/v1.0"


class GraphClient:
    def __init__(self, auth: GraphAuth):
        self.auth = auth
        self._session = requests.Session()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Content-Type": "application/json",
        }

    def get(self, path: str, params: dict | None = None) -> dict:
        resp = self._session.get(
            f"{BASE_URL}{path}", headers=self._headers(), params=params
        )
        resp.raise_for_status()
        return resp.json()

    def get_all(self, path: str, params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paged Graph API endpoint."""
        results: list[dict] = []
        url = f"{BASE_URL}{path}"
        while url:
            resp = self._session.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            params = None  # nextLink already carries query params
        return results
