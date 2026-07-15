"""contentpilot ui — lokales Web-Interface (nur Standardbibliothek).

Idee eintippen → Varianten je Plattform ansehen/bearbeiten → in den Kalender
übernehmen → an Postiz senden. Läuft auf localhost; die Generierung läuft im
Hintergrund-Thread, der Browser pollt den Status.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from . import calendar_store
from .backends import create_backend
from .config import from_env
from .generator import generate
from .platforms import PLATFORMS, full_text
from .profile import ensure_profile


class _GenState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running = False
        self.error: Optional[str] = None
        self.variants: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
        self.idea = ""


_STATE = _GenState()


def _generate_async(idea: str, platforms: List[str]) -> None:
    settings = from_env()
    ensure_profile(settings)
    try:
        variants, warnings = generate(idea, platforms, settings, create_backend(settings))
        with _STATE.lock:
            _STATE.variants = [
                {**v.model_dump(), "voll": full_text(v), "label": PLATFORMS[v.platform].label}
                for v in variants
            ]
            _STATE.warnings = warnings
            _STATE.error = None
    except Exception as error:
        with _STATE.lock:
            _STATE.error = str(error)[:500]
            _STATE.variants = []
    finally:
        with _STATE.lock:
            _STATE.running = False


_PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Content-Pilot — Idee rein, Posts raus</title>
<style>
:root{--bg:#07120d;--panel:#0d1d15;--line:#203729;--ink:#edf5ee;--muted:#9ab3a3;
--gold:#d3f566;--gold2:#95dd33;--red:#ff8f7a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:36px 20px}
h1{font-size:26px;letter-spacing:-.5px;margin:0 0 4px}h1 span{color:var(--gold)}
p.sub{color:var(--muted);margin:0 0 26px;font-size:14.5px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;
padding:20px;margin-bottom:16px}
label{display:block;font-size:12.5px;color:var(--muted);margin:12px 0 4px}
textarea,input{width:100%;background:#0a1712;border:1px solid var(--line);
border-radius:10px;color:var(--ink);padding:10px 12px;font-family:inherit;font-size:14px}
textarea{min-height:80px;resize:vertical}
.pf{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.pf label{display:inline-flex;align-items:center;gap:6px;margin:0;border:1px solid var(--line);
border-radius:999px;padding:6px 14px;cursor:pointer;font-size:13px;color:var(--muted)}
.pf input{width:auto;accent-color:var(--gold2)}
button{margin-top:14px;background:linear-gradient(115deg,var(--gold),var(--gold2));
color:#0a1a10;border:none;border-radius:12px;padding:11px 20px;font-weight:750;
font-size:14.5px;cursor:pointer;font-family:inherit}
button.sec{background:none;border:1px solid var(--line);color:var(--ink);font-weight:600}
button:disabled{opacity:.5;cursor:wait}
.variant{border:1px solid var(--line);border-radius:12px;padding:14px;margin:10px 0}
.variant h3{margin:0 0 6px;font-size:14px;color:var(--gold)}
.variant textarea{min-height:120px}
.count{font-size:12px;color:var(--muted);text-align:right;margin-top:4px}
.warn{color:var(--red);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{padding:8px 6px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.6px}
.status-entwurf{color:var(--muted)}.status-geplant{color:var(--gold)}.status-gesendet{color:var(--gold2)}
.err{color:var(--red)}
</style></head><body><div class="wrap">
<h1>Content-Pilot<span>.</span></h1>
<p class="sub">Idee rein → plattformgerechte Posts in deiner Tonalität → Kalender → Postiz. Alles lokal.</p>
<div class="panel">
<label>Was gibt es zu erzählen?</label>
<textarea id="idee" placeholder="z. B. Wir haben heute den Export-Dokumenten-Check gelauncht: 196 Länder, läuft komplett im Browser …"></textarea>
<label>Plattformen</label>
<div class="pf" id="pf"></div>
<button id="go" onclick="gen()">Posts generieren →</button>
<span id="genstatus" style="margin-left:12px;font-size:13.5px;color:var(--muted)"></span>
</div>
<div class="panel" id="varpanel" style="display:none">
<h2 style="font-size:17px;margin:0 0 4px">Varianten <span style="color:var(--muted);font-size:13px">(bearbeitbar)</span></h2>
<div id="varianten"></div>
<button onclick="uebernehmen()">In den Kalender übernehmen ✓</button>
</div>
<div class="panel">
<h2 style="font-size:17px;margin:0 0 10px">Kalender</h2>
<table><thead><tr><th>ID</th><th>Plattform</th><th>Status</th><th>Text</th><th></th></tr></thead>
<tbody id="kal"></tbody></table>
</div>
</div>
<script>
const PLATTFORMEN = __PLATFORMS__;
const pf = document.getElementById('pf');
for (const [key, label] of PLATTFORMEN) {
  const l = document.createElement('label');
  const c = document.createElement('input');
  c.type = 'checkbox'; c.value = key;
  if (key === 'linkedin' || key === 'x') c.checked = true;
  l.appendChild(c); l.appendChild(document.createTextNode(label));
  pf.appendChild(l);
}
let timer = null;
async function gen() {
  const idee = document.getElementById('idee').value.trim();
  const plattformen = Array.from(pf.querySelectorAll('input:checked')).map(c => c.value);
  if (!idee) { alert('Bitte erst die Idee beschreiben.'); return; }
  if (!plattformen.length) { alert('Mindestens eine Plattform wählen.'); return; }
  document.getElementById('go').disabled = true;
  document.getElementById('genstatus').textContent = '⚙️ Das LLM schreibt …';
  await fetch('/generate', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({idee, plattformen})});
  timer = setInterval(pollGen, 1500);
}
async function pollGen() {
  const s = await (await fetch('/genstatus')).json();
  if (s.running) return;
  clearInterval(timer);
  document.getElementById('go').disabled = false;
  const st = document.getElementById('genstatus');
  if (s.error) { st.innerHTML = '<span class="err">' + esc(s.error) + '</span>'; return; }
  st.textContent = '✅ Fertig — unten prüfen & übernehmen.';
  const host = document.getElementById('varianten');
  host.innerHTML = '';
  s.variants.forEach((v, i) => {
    const d = document.createElement('div'); d.className = 'variant';
    d.innerHTML = '<h3>' + esc(v.label) + '</h3>';
    const t = document.createElement('textarea');
    t.value = v.voll; t.id = 'var' + i; t.dataset.platform = v.platform;
    t.addEventListener('input', () => cnt(i));
    d.appendChild(t);
    const c = document.createElement('div'); c.className = 'count'; c.id = 'cnt' + i;
    d.appendChild(c);
    host.appendChild(d);
    cnt(i);
  });
  if (s.warnings.length) {
    const w = document.createElement('p'); w.className = 'warn';
    w.textContent = '⚠ ' + s.warnings.join(' · ');
    host.appendChild(w);
  }
  document.getElementById('varpanel').style.display = 'block';
}
function cnt(i) {
  const t = document.getElementById('var' + i);
  document.getElementById('cnt' + i).textContent = t.value.length + ' Zeichen';
}
async function uebernehmen() {
  const idee = document.getElementById('idee').value.trim();
  const items = Array.from(document.querySelectorAll('#varianten textarea')).map(t => ({
    platform: t.dataset.platform, text: t.value}));
  await fetch('/uebernehmen', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({idee, items})});
  document.getElementById('varpanel').style.display = 'none';
  ladeKalender();
}
async function senden(id) {
  const r = await fetch('/senden', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id})});
  const text = await r.text();
  if (!r.ok) alert(text);
  ladeKalender();
}
function esc(x) { return x.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
async function ladeKalender() {
  const entries = await (await fetch('/kalender')).json();
  document.getElementById('kal').innerHTML = entries.map(e =>
    '<tr><td>' + e.id + '</td><td>' + esc(e.platform) + '</td>' +
    '<td class="status-' + e.status + '">' + e.status + '</td>' +
    '<td>' + esc(e.text.slice(0, 60)) + '</td>' +
    '<td>' + (e.status !== 'gesendet'
      ? '<button class="sec" style="margin:0;padding:5px 12px" onclick="senden(' + e.id + ')">an Postiz →</button>'
      : '✓') + '</td></tr>').join('') || '<tr><td colspan="5" style="color:var(--muted)">leer</td></tr>';
}
ladeKalender();
</script></body></html>
"""


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any, code: int = 200) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode(), "application/json")

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            page = _PAGE.replace(
                "__PLATFORMS__",
                json.dumps([[k, s.label] for k, s in PLATFORMS.items()], ensure_ascii=False),
            )
            self._send(200, page.encode(), "text/html; charset=utf-8")
        elif path == "/genstatus":
            with _STATE.lock:
                self._json(
                    {
                        "running": _STATE.running,
                        "error": _STATE.error,
                        "variants": _STATE.variants,
                        "warnings": _STATE.warnings,
                    }
                )
        elif path == "/kalender":
            entries = calendar_store.load(from_env())
            self._json([entry.model_dump() for entry in entries])
        else:
            self._send(404, b"nicht gefunden", "text/plain")

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if path == "/generate":
            with _STATE.lock:
                if _STATE.running:
                    self._send(409, "Es läuft bereits eine Generierung.".encode(), "text/plain")
                    return
                _STATE.running = True
                _STATE.idea = str(payload.get("idee", ""))
            threading.Thread(
                target=_generate_async,
                args=(str(payload.get("idee", "")), list(payload.get("plattformen", []))),
                daemon=True,
            ).start()
            self._send(200, b"gestartet", "text/plain")
        elif path == "/uebernehmen":
            settings = from_env()
            for item in payload.get("items", []):
                calendar_store.add(
                    settings,
                    platform=str(item.get("platform", "")),
                    text=str(item.get("text", "")),
                    hashtags=[],  # Hashtags stehen nach dem Bearbeiten im Text selbst
                    idea=str(payload.get("idee", "")),
                )
            self._send(200, b"ok", "text/plain")
        elif path == "/senden":
            from datetime import datetime, timedelta

            from .platforms import full_text as _ft
            from .postiz import PostizClient, PostizError

            settings = from_env()
            entry = calendar_store.get(settings, int(payload.get("id", 0)))
            if entry is None:
                self._send(404, b"Eintrag nicht gefunden", "text/plain")
                return
            try:
                client = PostizClient(settings)
                integration = client.find_integration(entry.platform)
                if integration is None:
                    raise PostizError(
                        f"Kein verbundener {entry.platform}-Account in Postiz gefunden."
                    )
                date_iso = entry.scheduled or (datetime.now() + timedelta(minutes=10)).isoformat()
                from .schemas import PostVariant

                variant = PostVariant(
                    platform=entry.platform, text=entry.text, hashtags=entry.hashtags
                )
                entry.postiz_id = client.schedule_post(
                    str(integration["id"]), _ft(variant), date_iso
                )
            except PostizError as error:
                self._send(400, str(error).encode(), "text/plain")
                return
            entry.status = "gesendet"
            calendar_store.update(settings, entry)
            self._send(200, b"ok", "text/plain")
        else:
            self._send(404, b"nicht gefunden", "text/plain")


def serve(port: int = 8801, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    url = f"http://localhost:{port}"
    print(f"Content-Pilot läuft: {url}  (Strg+C beendet)")
    if open_browser:
        import webbrowser

        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
