"""Content-Kalender — lokale, menschenlesbare JSON-Datei (DSGVO: bleibt bei dir).

Bewusst simpel: eine Datei ``~/.content-pilot/kalender.json`` mit einer Liste
von Einträgen. Kein Server, keine Datenbank — Backup = Datei kopieren.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import Settings
from .schemas import CalendarEntry


def _file(settings: Settings) -> Path:
    return Path(settings.data_dir).expanduser() / "kalender.json"


def load(settings: Settings) -> List[CalendarEntry]:
    path = _file(settings)
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []  # kaputte Datei blockiert nie; Neuanlage beim nächsten Speichern
    return [CalendarEntry.model_validate(item) for item in raw]


def save(settings: Settings, entries: List[CalendarEntry]) -> None:
    path = _file(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [entry.model_dump() for entry in entries]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def add(
    settings: Settings,
    platform: str,
    text: str,
    hashtags: List[str],
    idea: str = "",
    scheduled: Optional[str] = None,
    warnings: Optional[List[str]] = None,
) -> CalendarEntry:
    entries = load(settings)
    entry = CalendarEntry(
        id=max((e.id for e in entries), default=0) + 1,
        created=datetime.now().isoformat(timespec="seconds"),
        platform=platform,
        text=text,
        hashtags=hashtags,
        idea=idea,
        scheduled=scheduled,
        status="geplant" if scheduled else "entwurf",
        warnings=warnings or [],
    )
    entries.append(entry)
    save(settings, entries)
    return entry


def get(settings: Settings, entry_id: int) -> Optional[CalendarEntry]:
    return next((e for e in load(settings) if e.id == entry_id), None)


def update(settings: Settings, entry: CalendarEntry) -> None:
    entries = load(settings)
    for i, existing in enumerate(entries):
        if existing.id == entry.id:
            entries[i] = entry
            save(settings, entries)
            return
    raise KeyError(f"Kalender-Eintrag {entry.id} nicht gefunden.")
