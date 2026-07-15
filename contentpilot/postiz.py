"""Postiz-Anbindung — dünner Client für die Public API (nur Standardbibliothek).

Postiz übernimmt die Plattform-Anbindungen (OAuth, Publishing) — Content-Pilot
liefert die Inhalte. Eigenständiges Tool über die öffentliche API; die AGPL
von Postiz färbt dadurch nicht auf diesen Code ab.

Konfiguration: CP_POSTIZ_URL (z. B. http://localhost:5000/api) und
CP_POSTIZ_API_KEY (Postiz → Settings → Public API).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .config import Settings


class PostizError(RuntimeError):
    pass


def _base_url(settings: Settings) -> str:
    url = settings.postiz_url.rstrip("/")
    if not url:
        raise PostizError(
            "Postiz ist nicht konfiguriert — CP_POSTIZ_URL setzen "
            "(z. B. http://localhost:5000/api) und CP_POSTIZ_API_KEY "
            "(Postiz → Settings → Public API)."
        )
    if not url.endswith("/public/v1"):
        url += "/public/v1"
    return url


class PostizClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.postiz_api_key:
            raise PostizError("CP_POSTIZ_API_KEY fehlt (Postiz → Settings → Public API).")
        self._base = _base_url(settings)
        self._key = settings.postiz_api_key
        self._timeout = settings.timeout_seconds

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        request = urllib.request.Request(
            f"{self._base}{path}",
            method=method,
            headers={"Authorization": self._key, "Content-Type": "application/json"},
            data=json.dumps(body).encode("utf-8") if body is not None else None,
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8") or "null")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            raise PostizError(f"Postiz antwortet mit HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise PostizError(
                f"Postiz nicht erreichbar unter {self._base}: {error.reason}"
            ) from error

    def integrations(self) -> List[Dict[str, Any]]:
        """Verbundene Social-Accounts (id, name, identifier je Eintrag)."""
        result = self._request("GET", "/integrations")
        return result if isinstance(result, list) else result.get("integrations", [])

    def find_integration(self, platform: str) -> Optional[Dict[str, Any]]:
        """Erste Integration, deren identifier/name zur Plattform passt."""
        wanted = platform.lower()
        for integration in self.integrations():
            haystack = f"{integration.get('identifier', '')} {integration.get('name', '')}".lower()
            if wanted in haystack:
                return integration
        return None

    def schedule_post(
        self,
        integration_id: str,
        content: str,
        date_iso: str,
        post_type: str = "schedule",  # schedule | draft | now
    ) -> str:
        """Legt einen Post in Postiz an; gibt die Postiz-Post-ID zurück."""
        body = {
            "type": post_type,
            "date": date_iso,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": {"id": integration_id},
                    "value": [{"content": content}],
                    "settings": {},
                }
            ],
        }
        result = self._request("POST", "/posts", body)
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return str(result[0].get("postId") or result[0].get("id") or "ok")
        if isinstance(result, dict):
            return str(result.get("id") or result.get("postId") or "ok")
        return "ok"
