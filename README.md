# Content-Pilot — dein deutsches KI-Content-Studio

> Eine Idee rein („Wir haben heute X gelauncht") — fertige, plattformgerechte
> Posts in deiner Tonalität raus. Veröffentlicht wird über dein self-gehostetes
> [Postiz](https://github.com/gitroomhq/postiz-app). Alles lokal, DSGVO-freundlich.

**Arbeitsteilung nach dem Rawkeep-Prinzip:** das LLM formuliert, der **Code
entscheidet** — Zeichen-Limits, Hashtag-Anzahl und Plattform-Zuordnung werden
deterministisch durchgesetzt, jede Kürzung wird als Warnung ausgewiesen.

```
  Idee ─▶ ✍️  GENERATOR   je Plattform eine Variante (dein Claude-Abo/Ollama)
             │            + deine Tonalität aus ~/.content-pilot/profil.md
             ▼
          📏 LIMITS       Code erzwingt Zeichen/Hashtags je Plattform
             │
             ▼
          🗓  KALENDER     lokale JSON-Datei — Entwurf → geplant → gesendet
             │
             ▼
          🚀 POSTIZ       Public API: dein Postiz veröffentlicht (OAuth dort)
```

## Quickstart

```bash
python3 -m pip install -e ".[dev]"
contentpilot erstellen "Wir haben den Export-Dokumenten-Check gelauncht: 196 Länder, läuft komplett im Browser"
```

Das war's — die Backend-Wahl läuft automatisch: **claude CLI** (dein Claude-Abo,
kein API-Key) → **Ollama** (lokal) → verständliche Fehlermeldung.

```bash
contentpilot ui                       # Web-Oberfläche: http://localhost:8801
contentpilot kalender                 # was liegt an?
contentpilot senden 3                 # Eintrag 3 an Postiz übergeben
contentpilot senden 3 --sofort        # sofort posten statt planen
contentpilot profil                   # Tonalität ansehen/anlegen (Markdown)
contentpilot plattformen              # unterstützte Plattformen + Limits
```

## Plattformen

LinkedIn (3000) · X (280) · Instagram (2200) · Facebook (2000) · Threads (500)
· Mastodon (500) — je mit eigenem Stil-Hint und Hashtag-Limit. Hashtags zählen
zum Zeichenbudget; gekürzt wird an Wortgrenzen, nie mitten im Wort.

## Postiz anbinden (einmalig)

Komplette Anleitung: [`docker/postiz/SETUP-POSTIZ.md`](docker/postiz/SETUP-POSTIZ.md).
Kurzfassung: `docker compose up -d` im Ordner `docker/postiz/`, Social-Accounts
in Postiz verbinden, API-Key holen, dann:

```bash
export CP_POSTIZ_URL="http://localhost:5000/api"
export CP_POSTIZ_API_KEY="<Postiz → Settings → Public API>"
```

Ohne Postiz funktioniert alles außer `senden` — generieren, bearbeiten und
den Kalender pflegen geht auch offline (Copy-Paste bleibt ja immer).

## Konfiguration (Env, Präfix `CP_`)

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `CP_BACKEND` | `auto` | `auto` \| `claude` (Abo) \| `ollama` \| `mock` |
| `CP_MODEL` | `auto` | Modell-Override fürs Backend |
| `CP_DATA_DIR` | `~/.content-pilot` | Kalender + Profil (rein lokal) |
| `CP_POSTIZ_URL` | *(leer)* | z. B. `http://localhost:5000/api` |
| `CP_POSTIZ_API_KEY` | *(leer)* | Postiz → Settings → Public API |

## Die Invarianten

1. **Der Code setzt die Limits durch** — das LLM schlägt nur vor.
2. **Deine Daten bleiben lokal**: Kalender und Profil sind Dateien in
   `~/.content-pilot/`, kein Cloud-Dienst außer deinem eigenen Postiz.
3. **Jede angefragte Plattform bekommt eine Variante** — fällt das LLM aus,
   gibt es einen deterministischen Fallback statt einer Lücke.
4. **Lizenz-sauber**: eigenständiges Tool, das nur die Postiz Public API
   nutzt — kein Postiz-Code enthalten.

## Entwicklung

```bash
ruff format . && ruff check . && python3 -m mypy && python3 -m pytest -q
```

---
© Rawkeep · Inhaber: Frakibou Imqhamed · <https://rawkeep.com>
