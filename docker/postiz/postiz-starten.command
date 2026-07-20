#!/bin/bash
# ◆ Postiz-Starter — Doppelklick genügt.
# Secrets (JWT, LinkedIn) liegen in der lokalen .env (nicht in Git) —
# dadurch kollidiert ein späteres 'git pull' nie mit deinen Einstellungen.
set -e
cd "$(dirname "$0")"
ENVFILE=".env"

echo "◆ Postiz-Starter für den Content-Pilot"
echo

# 1) Läuft Docker?
if ! docker info >/dev/null 2>&1; then
  echo "✗ Docker läuft nicht."
  echo "  → Docker Desktop öffnen, warten bis das Wal-Symbol ruhig ist,"
  echo "    dann dieses Skript nochmal doppelklicken."
  read -p "  (Enter zum Schließen)"
  exit 1
fi
echo "✓ Docker läuft."

# 2) JWT_SECRET in .env (nur beim allerersten Start)
if ! grep -q '^JWT_SECRET=' "$ENVFILE" 2>/dev/null; then
  echo "JWT_SECRET=$(openssl rand -hex 32)" >> "$ENVFILE"
  echo "✓ Sicherheits-Schlüssel (JWT_SECRET) automatisch gesetzt."
fi

# 3) LinkedIn-Zugangsdaten — optional, Enter zum Überspringen
if ! grep -q '^LINKEDIN_CLIENT_ID=' "$ENVFILE" 2>/dev/null; then
  echo
  echo "LinkedIn-Developer-App (Anleitung: SETUP-POSTIZ.md, Abschnitt LinkedIn)."
  echo "Falls du Client ID & Secret schon hast, hier einfügen — sonst Enter,"
  echo "das lässt sich jederzeit durch erneuten Doppelklick nachholen."
  read -p "  Client ID (oder Enter): " LI_ID
  if [ -n "$LI_ID" ]; then
    read -p "  Client Secret: " LI_SECRET
    {
      echo "LINKEDIN_CLIENT_ID=$LI_ID"
      echo "LINKEDIN_CLIENT_SECRET=$LI_SECRET"
    } >> "$ENVFILE"
    echo "✓ LinkedIn-Zugangsdaten eingetragen."
  else
    echo "→ Übersprungen — LinkedIn später per erneutem Doppelklick verbinden."
  fi
fi

# 4) Starten
echo
echo "… Postiz startet (beim ersten Mal dauert der Download ein paar Minuten) …"
docker compose up -d

# 5) Warten, bis das Backend antwortet (nicht nur die Oberfläche).
#    Gibt der interne Prozess-Manager das Backend beim Erststart auf
#    (Temporal/ES noch nicht bereit), hilft genau ein Neustart.
warte_auf_backend() {
  for i in $(seq 1 $1); do
    code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5050/api/user/self 2>/dev/null)
    case "$code" in 200|401|403) return 0 ;; esac
    sleep 5
  done
  return 1
}
echo "… warte auf das Backend (Erststart kann mehrere Minuten dauern) …"
if ! warte_auf_backend 48; then
  echo "→ Backend noch nicht da — starte den Postiz-Container einmal neu …"
  docker compose restart postiz >/dev/null 2>&1
  warte_auf_backend 60 || {
    echo "✗ Backend antwortet weiterhin nicht. Logs ansehen mit:"
    echo "  docker compose logs postiz | grep -iE '[0-9]\|backend' | tail -30"
  }
fi
open "http://localhost:5050" 2>/dev/null || xdg-open "http://localhost:5050" 2>/dev/null \
  || echo "→ Bitte http://localhost:5050 im Browser öffnen."

echo
echo "✓ Fertig! Im Browser: Konto anlegen (erste Registrierung = Admin),"
echo "  dann 'Add Channel' → LinkedIn."
echo "  Hinweis: Nach dem ersten Start braucht das Backend noch 1–2 Minuten"
echo "  (Temporal richtet sich ein) — bei Fehlern kurz warten und neu laden."
