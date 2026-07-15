"""Generator — aus einer Idee werden plattformgerechte Post-Varianten.

Arbeitsteilung: das LLM formuliert (mit deiner Tonalität), der Code setzt die
Plattform-Limits durch und garantiert, dass JEDE angefragte Plattform eine
Variante bekommt (deterministischer Fallback statt Lücke).
"""

from __future__ import annotations

from typing import List, Tuple

from .backends import LLMBackend
from .config import Settings
from .platforms import PLATFORMS, enforce
from .profile import profile_text
from .schemas import GeneratedPosts, PostVariant

SYSTEM_PROMPT = (
    "Du bist ein deutschsprachiger Social-Media-Redakteur. Du bekommst eine "
    "Idee/Nachricht und eine Liste von Zielplattformen mit Stil-Hinweisen und "
    "Limits. Schreibe je Plattform GENAU EINE eigenständige Variante — kein "
    "Copy-Paste zwischen Plattformen, jede Variante folgt dem Stil ihrer "
    "Plattform und der Tonalität des Auftraggebers. Hashtags separat im Feld "
    "hashtags (ohne #-Zeichen), nicht im Text. Antworte ausschließlich als "
    "JSON gemäß Schema."
)


def generate(
    idea: str,
    platform_keys: List[str],
    settings: Settings,
    backend: LLMBackend,
) -> Tuple[List[PostVariant], List[str]]:
    """Erzeugt Varianten für alle angefragten Plattformen (+ Warnungen)."""
    keys = [k.lower().strip() for k in platform_keys if k.strip()]
    unknown = [k for k in keys if k not in PLATFORMS]
    if unknown:
        raise ValueError(
            f"Unbekannte Plattform(en): {', '.join(unknown)} — verfügbar: {', '.join(PLATFORMS)}"
        )
    specs = "\n".join(
        f"- {key} ({PLATFORMS[key].label}): max. {PLATFORMS[key].max_chars} Zeichen, "
        f"max. {PLATFORMS[key].max_hashtags} Hashtags. Stil: {PLATFORMS[key].hint}"
        for key in keys
    )
    tonality = profile_text(settings)
    prompt = (
        f"Idee/Nachricht: {idea}\n\n"
        f"Zielplattformen:\n{specs}\n\n"
        + (f"Tonalität des Auftraggebers:\n{tonality}\n\n" if tonality else "")
        + "Erzeuge je Plattform genau eine Variante (Feld platform = der "
        "Plattform-Schlüssel in Kleinbuchstaben)."
    )
    raw = backend.complete_json(SYSTEM_PROMPT, prompt, GeneratedPosts.model_json_schema())
    generated = GeneratedPosts.model_validate(raw)

    variants: List[PostVariant] = []
    warnings: List[str] = []
    by_platform = {v.platform.lower().strip(): v for v in generated.variants}
    for key in keys:
        candidate = by_platform.get(key)
        if candidate is None:
            # Deterministischer Fallback: nie eine Plattform leer lassen.
            candidate = PostVariant(platform=key, text=idea, hashtags=[])
            warnings.append(f"LLM lieferte keine Variante für {key} — Idee als Rohtext übernommen.")
        clean, notes = enforce(candidate)
        variants.append(clean)
        warnings.extend(notes)
    return variants, warnings
