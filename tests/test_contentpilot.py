"""Tests: Limits (Code entscheidet), Kalender, Generator, Postiz-Client."""

from __future__ import annotations

import json

import pytest

from contentpilot.backends import BackendError, MockBackend
from contentpilot.config import Settings
from contentpilot.generator import generate
from contentpilot.platforms import PLATFORMS, enforce, full_text
from contentpilot.schemas import PostVariant


def _settings(tmp_path, **overrides) -> Settings:
    return Settings(backend="mock", data_dir=str(tmp_path), **overrides)


# ── Plattform-Limits: der Code entscheidet ──────────────────────────────
def test_enforce_kuerzt_an_wortgrenze():
    lang = "Wort " * 100
    variant, warnings = enforce(PostVariant(platform="x", text=lang))
    assert len(variant.text) <= PLATFORMS["x"].max_chars
    assert variant.text.endswith("…")
    assert any("gekürzt" in w for w in warnings)


def test_enforce_begrenzt_und_bereinigt_hashtags():
    variant, warnings = enforce(
        PostVariant(platform="x", text="Hallo", hashtags=["#Export", "Export", "a", "b", "c"])
    )
    assert len(variant.hashtags) == PLATFORMS["x"].max_hashtags
    assert variant.hashtags[0] == "Export"  # dedupliziert, ohne #
    assert any("Hashtags" in w for w in warnings)


def test_hashtags_zaehlen_zum_limit():
    variant, _ = enforce(PostVariant(platform="x", text="X" * 280, hashtags=["EinLangerHashtag"]))
    assert len(full_text(variant)) <= PLATFORMS["x"].max_chars


# ── Generator ───────────────────────────────────────────────────────────
def test_generator_erzwingt_jede_plattform(tmp_path):
    """LLM vergisst eine Plattform ⇒ deterministischer Fallback statt Lücke."""
    backend = MockBackend(
        [{"variants": [{"platform": "linkedin", "text": "Fachlicher Post.", "hashtags": ["KI"]}]}]
    )
    variants, warnings = generate(
        "Wir haben gelauncht", ["linkedin", "x"], _settings(tmp_path), backend
    )
    assert [v.platform for v in variants] == ["linkedin", "x"]
    assert variants[1].text == "Wir haben gelauncht"  # Fallback = Idee als Rohtext
    assert any("keine Variante für x" in w for w in warnings)


def test_generator_lehnt_unbekannte_plattform_ab(tmp_path):
    with pytest.raises(ValueError):
        generate("Idee", ["myspace"], _settings(tmp_path), MockBackend([]))


# ── Kalender ────────────────────────────────────────────────────────────
def test_kalender_roundtrip_und_status(tmp_path):
    from contentpilot import calendar_store

    settings = _settings(tmp_path)
    entry = calendar_store.add(settings, "linkedin", "Text", ["KI"], idea="Idee")
    assert entry.id == 1 and entry.status == "entwurf"
    zweiter = calendar_store.add(settings, "x", "Kurz", [], scheduled="2026-08-01T09:00")
    assert zweiter.id == 2 and zweiter.status == "geplant"

    entry.status = "gesendet"
    entry.postiz_id = "p-1"
    calendar_store.update(settings, entry)
    geladen = calendar_store.get(settings, 1)
    assert geladen is not None and geladen.status == "gesendet" and geladen.postiz_id == "p-1"


def test_kalender_ueberlebt_kaputte_datei(tmp_path):
    from contentpilot import calendar_store

    settings = _settings(tmp_path)
    (tmp_path / "kalender.json").write_text("KAPUTT{")
    assert calendar_store.load(settings) == []


# ── Profil ──────────────────────────────────────────────────────────────
def test_profil_starter_wird_angelegt(tmp_path):
    from contentpilot.profile import ensure_profile, profile_text

    settings = _settings(tmp_path)
    path = ensure_profile(settings)
    assert path.is_file()
    assert "Tonalität" in profile_text(settings)


# ── Postiz-Client (gegen Fake-Server) ───────────────────────────────────
def _fake_postiz(tmp_path):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            seen["auth"] = self.headers.get("Authorization")
            seen["get_path"] = self.path
            body = json.dumps(
                [{"id": "abc-1", "identifier": "linkedin", "name": "Rawkeep LinkedIn"}]
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            seen["post_body"] = json.loads(self.rfile.read(length))
            seen["post_path"] = self.path
            body = json.dumps([{"postId": "post-42"}]).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, seen


def test_postiz_client_sendet_korrekt(tmp_path):
    from contentpilot.postiz import PostizClient

    server, seen = _fake_postiz(tmp_path)
    port = server.server_address[1]
    try:
        settings = _settings(
            tmp_path, postiz_url=f"http://127.0.0.1:{port}/api", postiz_api_key="key-123"
        )
        client = PostizClient(settings)
        integration = client.find_integration("linkedin")
        assert integration is not None and integration["id"] == "abc-1"
        assert seen["auth"] == "key-123"
        assert seen["get_path"].endswith("/api/public/v1/integrations")  # URL normalisiert

        post_id = client.schedule_post("abc-1", "Hallo Welt", "2026-08-01T09:00:00")
        assert post_id == "post-42"
        assert seen["post_body"]["type"] == "schedule"
        assert seen["post_body"]["posts"][0]["integration"]["id"] == "abc-1"
        assert seen["post_body"]["posts"][0]["value"][0]["content"] == "Hallo Welt"
    finally:
        server.shutdown()


def test_postiz_ohne_konfiguration_erklaert_deutsch(tmp_path):
    from contentpilot.postiz import PostizClient, PostizError

    with pytest.raises(PostizError, match="CP_POSTIZ_API_KEY"):
        PostizClient(_settings(tmp_path, postiz_url="http://x"))


# ── Backend-Auswahl ─────────────────────────────────────────────────────
def test_backend_auswahl_erklaert_deutsch(tmp_path, monkeypatch):
    from contentpilot import backends

    monkeypatch.setattr(backends, "claude_cli_available", lambda: False)
    monkeypatch.setattr(backends, "ollama_reachable", lambda s: False)
    with pytest.raises(BackendError, match="Claude Code CLI"):
        backends.create_backend(Settings(backend="auto"))
