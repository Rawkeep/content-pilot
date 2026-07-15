"""Verträge des Content-Piloten (single source of truth).

Das LLM liefert strukturiertes JSON gegen genau diese Schemas; validiert und
begrenzt (Zeichen-Limits, Hashtag-Anzahl) wird IMMER im Code — nie im Modell.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class PostVariant(BaseModel):
    """Eine Post-Variante für genau eine Plattform."""

    platform: str  # Schlüssel aus platforms.PLATFORMS (z. B. "linkedin")
    text: str
    hashtags: List[str] = []


class GeneratedPosts(BaseModel):
    """LLM-Ausgabe: je angefragter Plattform eine Variante."""

    variants: List[PostVariant]


class CalendarEntry(BaseModel):
    """Ein Eintrag im lokalen Content-Kalender."""

    id: int
    created: str  # ISO-Zeitstempel
    platform: str
    text: str
    hashtags: List[str] = []
    scheduled: Optional[str] = None  # ISO-Zeitpunkt der geplanten Veröffentlichung
    status: str = "entwurf"  # entwurf | geplant | gesendet
    postiz_id: Optional[str] = None  # gesetzt nach erfolgreichem Senden
    idea: str = ""  # die ursprüngliche Idee (für Kontext/Suche)
    warnings: List[str] = []  # z. B. "Text auf 280 Zeichen gekürzt"
