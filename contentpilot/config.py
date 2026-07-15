"""Konfiguration — Umgebungsvariablen mit Präfix ``CP_`` (wie DEVTEAM_/FAI_).

Beispiel:
    CP_POSTIZ_URL=http://localhost:5000/api CP_POSTIZ_API_KEY=… contentpilot ui
"""

from __future__ import annotations

import os

from pydantic import BaseModel

_PREFIX = "CP_"


class Settings(BaseModel):
    backend: str = "auto"  # auto | claude (Abo) | ollama | mock
    model: str = "auto"  # auto = Backend-Default
    ollama_url: str = "http://localhost:11434"
    timeout_seconds: int = 300  # pro LLM-Call
    data_dir: str = "~/.content-pilot"  # Kalender + Profil (rein lokal)
    postiz_url: str = ""  # z. B. http://localhost:5000/api — leer = Senden deaktiviert
    postiz_api_key: str = ""  # Postiz → Settings → Public API


def from_env() -> Settings:
    """Settings aus der Umgebung (fehlende Werte = Defaults oben)."""
    values = {}
    for field in Settings.model_fields:
        raw = os.environ.get(_PREFIX + field.upper())
        if raw is not None:
            values[field] = raw
    return Settings(**values)
