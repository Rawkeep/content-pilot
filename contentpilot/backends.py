"""LLM-Backends — dieselbe Philosophie wie devteam: BYOK, Abo zuerst.

Auto-Erkennung: claude CLI (Claude-Abo, kein API-Key) → Ollama (lokal) →
verständlicher deutscher Fehler. ``mock`` für Tests/Demos.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, List, Protocol

from .config import Settings


class BackendError(RuntimeError):
    pass


class LLMBackend(Protocol):
    def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]: ...


def claude_cli_available() -> bool:
    return shutil.which("claude") is not None


def _extract_json(text: str) -> Dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise BackendError(f"LLM lieferte kein JSON-Objekt: {text[:200]!r}")
    try:
        result: Dict[str, Any] = json.loads(text[start : end + 1], strict=False)
    except json.JSONDecodeError as error:
        raise BackendError(f"LLM-Antwort ist kein gültiges JSON: {error}") from error
    return result


class ClaudeCliBackend:
    """Nutzt das Claude-Abo über die Claude Code CLI (headless)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        if not claude_cli_available():
            raise BackendError(
                "claude CLI nicht gefunden — installieren und einloggen "
                "(https://claude.com/claude-code)."
            )
        prompt = (
            f"{system}\n\n{user}\n\n"
            "Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemäß diesem "
            f"JSON-Schema — kein Markdown, kein Text davor oder danach:\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        command = ["claude", "-p", "--output-format", "json"]
        if self._settings.model not in ("", "auto"):
            command += ["--model", self._settings.model]
        proc = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self._settings.timeout_seconds,
        )
        if proc.returncode != 0:
            detail = (proc.stderr.strip() or proc.stdout.strip())[:400]
            raise BackendError(
                f"claude CLI fehlgeschlagen (Exit {proc.returncode}): {detail or '(keine Ausgabe)'}"
                " — ist die CLI eingeloggt? (claude → /login → Claude account)"
            )
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as error:
            raise BackendError(f"claude CLI: kein JSON-Envelope ({error})") from error
        if envelope.get("is_error"):
            raise BackendError(f"claude CLI meldet Fehler: {str(envelope.get('result'))[:400]}")
        return _extract_json(str(envelope.get("result", "")))


class OllamaBackend:
    """Lokales LLM via Ollama (JSON-Schema-erzwungen)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        import httpx  # lazy — nur mit Extra .[ollama] nötig

        model = self._settings.model if self._settings.model not in ("", "auto") else "qwen2.5:7b"
        response = httpx.post(
            f"{self._settings.ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "format": schema,
                "stream": False,
            },
            timeout=self._settings.timeout_seconds,
        )
        response.raise_for_status()
        return _extract_json(response.json()["message"]["content"])


def ollama_reachable(settings: Settings) -> bool:
    try:
        import httpx

        return httpx.get(f"{settings.ollama_url}/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


class MockBackend:
    """Geskriptete Antworten für Tests und Demos — kein LLM nötig."""

    def __init__(self, answers: List[Dict[str, Any]]) -> None:
        self._answers = list(answers)

    def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        if not self._answers:
            raise BackendError("MockBackend: keine Antworten mehr.")
        return self._answers.pop(0)


def create_backend(settings: Settings) -> LLMBackend:
    choice = settings.backend
    if choice == "auto":
        if claude_cli_available():
            choice = "claude"
        elif ollama_reachable(settings):
            choice = "ollama"
        else:
            raise BackendError(
                "Kein LLM-Backend gefunden. Am einfachsten: Claude Code CLI installieren "
                "und einloggen (https://claude.com/claude-code) — läuft über dein "
                "Claude-Abo. Alternativ: Ollama starten (ollama pull qwen2.5:7b)."
            )
    if choice == "claude":
        return ClaudeCliBackend(settings)
    if choice == "ollama":
        return OllamaBackend(settings)
    if choice == "mock":
        return MockBackend([])
    raise BackendError(f"Unbekanntes Backend: {choice!r} (auto|claude|ollama|mock)")
