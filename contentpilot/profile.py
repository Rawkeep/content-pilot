"""Tonalitäts-Profil — deine Stimme, die in jeden Post einfließt.

Eine lokale Markdown-Datei (Default ``~/.content-pilot/profil.md``). Wird beim
ersten Start mit einem Rawkeep-Starter angelegt und einfach als Text editiert.
"""

from __future__ import annotations

from pathlib import Path

from .config import Settings

MAX_PROFILE_CHARS = 2000

STARTER_PROFILE = """# Meine Tonalität (fließt in jeden generierten Post ein)

- Deutsch, klar und konkret — kein Marketing-Blabla, keine Superlative.
- Praktiker-Perspektive: zeigen, was das Ding wirklich tut und wem es hilft.
- Kurze Sätze. Fachbegriffe ja, Buzzwords nein.
- Themen: KI-Integration, Export/Logistik (Afrika), SAP, DSGVO-freundliche
  Local-first-Software, Automatisierung für den Mittelstand.
- Immer ehrlich über Grenzen ("kein Zertifikat, aber die technischen Kontrollen").
- Emojis sehr sparsam (max. 1–2, nie in jeder Zeile).
"""


def profile_path(settings: Settings) -> Path:
    return Path(settings.data_dir).expanduser() / "profil.md"


def ensure_profile(settings: Settings) -> Path:
    """Legt das Starter-Profil an, falls noch keines existiert."""
    path = profile_path(settings)
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(STARTER_PROFILE, encoding="utf-8")
    return path


def profile_text(settings: Settings) -> str:
    """Profil als Prompt-Baustein ('' wenn leer)."""
    path = profile_path(settings)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()[:MAX_PROFILE_CHARS]
