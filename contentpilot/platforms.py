"""Plattform-Spezifikationen + deterministische Durchsetzung.

Das LLM schlägt Texte vor — die Limits (Zeichen, Hashtags) setzt der Code
durch. Gekürzt wird an Wortgrenzen, jede Kürzung wird als Warnung vermerkt.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from pydantic import BaseModel

from .schemas import PostVariant


class Platform(BaseModel):
    label: str
    max_chars: int
    max_hashtags: int
    hint: str  # Stil-Anweisung für den Generator


PLATFORMS: Dict[str, Platform] = {
    "linkedin": Platform(
        label="LinkedIn",
        max_chars=3000,
        max_hashtags=5,
        hint="fachlich und persönlich, kurze Absätze, eine klare Kernaussage, "
        "Hook in der ersten Zeile, am Ende eine Frage oder ein Call-to-Action",
    ),
    "x": Platform(
        label="X (Twitter)",
        max_chars=280,
        max_hashtags=2,
        hint="ein Gedanke, pointiert, keine Einleitung, kein Thread",
    ),
    "instagram": Platform(
        label="Instagram",
        max_chars=2200,
        max_hashtags=8,
        hint="erzählend und nahbar, kurze Zeilen, sparsame Emojis, Hashtags ans Ende",
    ),
    "facebook": Platform(
        label="Facebook",
        max_chars=2000,
        max_hashtags=3,
        hint="locker und verständlich, direkt die Leser ansprechen",
    ),
    "threads": Platform(
        label="Threads",
        max_chars=500,
        max_hashtags=2,
        hint="conversational, wie der Beginn eines Gesprächs",
    ),
    "mastodon": Platform(
        label="Mastodon",
        max_chars=500,
        max_hashtags=3,
        hint="techniknah und bodenständig, kein Marketing-Ton",
    ),
}


def _trim(text: str, limit: int) -> Tuple[str, bool]:
    """Kürzt an einer Wortgrenze auf limit Zeichen (inkl. '…')."""
    if len(text) <= limit:
        return text, False
    cut = text[: limit - 2]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip() + " …", True


def enforce(variant: PostVariant) -> Tuple[PostVariant, List[str]]:
    """Setzt die Plattform-Limits deterministisch durch (Invariante: Code entscheidet)."""
    warnings: List[str] = []
    key = variant.platform.lower().strip()
    spec = PLATFORMS.get(key)
    if spec is None:
        return variant, [f"Unbekannte Plattform '{variant.platform}' — ungeprüft übernommen."]
    hashtags = []
    for tag in variant.hashtags:
        clean = tag.strip().lstrip("#").replace(" ", "")
        if clean and clean not in hashtags:
            hashtags.append(clean)
    if len(hashtags) > spec.max_hashtags:
        warnings.append(f"Hashtags auf {spec.max_hashtags} begrenzt ({spec.label}).")
        hashtags = hashtags[: spec.max_hashtags]
    # Hashtags zählen zum Zeichenlimit — Budget = Limit minus Hashtag-Zeile.
    tag_line = " ".join("#" + t for t in hashtags)
    budget = spec.max_chars - (len(tag_line) + 2 if tag_line else 0)
    text, trimmed = _trim(variant.text.strip(), budget)
    if trimmed:
        warnings.append(f"Text auf {spec.max_chars} Zeichen gekürzt ({spec.label}).")
    return PostVariant(platform=key, text=text, hashtags=hashtags), warnings


def full_text(variant: PostVariant) -> str:
    """Fertiger Post-Text inkl. Hashtag-Zeile — das, was gesendet wird."""
    tags = " ".join("#" + t for t in variant.hashtags)
    return f"{variant.text}\n\n{tags}" if tags else variant.text
