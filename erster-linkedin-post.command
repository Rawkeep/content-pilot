#!/bin/bash
# ◆ Erster LinkedIn-Post — Doppelklick genügt.
# Legt (einmalig) das Rawkeep-Tonalitätsprofil an und erzeugt den ersten
# fertigen LinkedIn-Post. Am Ende steht der Text zum Kopieren im Fenster.
set -e
cd "$(dirname "$0")"

echo "◆ Content-Pilot — erster LinkedIn-Post für Rawkeep"
echo

# contentpilot-Befehl finden (installiert oder als Modul)
if command -v contentpilot >/dev/null 2>&1; then
  CP="contentpilot"
elif python3 -c "import contentpilot" >/dev/null 2>&1; then
  CP="python3 -m contentpilot.cli"
else
  echo "… Content-Pilot wird einmalig installiert …"
  python3 -m pip install -e . >/dev/null 2>&1
  CP="python3 -m contentpilot.cli"
fi

# 1) Tonalitätsprofil anlegen (nur falls noch nicht vorhanden — deine
#    eigenen Änderungen werden nie überschrieben)
PROFIL="$HOME/.content-pilot/profil.md"
if [ ! -s "$PROFIL" ] || ! grep -q "Tonalität Rawkeep" "$PROFIL" 2>/dev/null; then
  mkdir -p "$HOME/.content-pilot"
  cat > "$PROFIL" <<'PROFILENDE'
# Tonalität Rawkeep (Frakibou Imqhamed)

## Stimme
- Deutsch, direkt, erste Person ("ich baue", "ich habe gesehen").
- Praktiker, kein Guru: konkrete Zahlen, echte Prozesse, ehrliche Grenzen.
- Kernprinzip: LLM schlägt vor, Code entscheidet, Menschen geben frei.
- Kein Buzzword-Bingo (kein "disruptiv", "Game-Changer", "10x").
- Emojis maximal 2-3 pro Post.

## Themen
Autonome Prozesse im Mittelstand; RAG ohne Halluzination / lokale DSGVO-KI;
Export & Afrika-Logistik (Nigeria, Zoll, Form M); Einblicke aus dem
Maschinenraum (Open Source: ProzessOS, GroundedRAG).

## Call-to-Action
Nie mehr als EIN CTA. Variieren: "Welcher Prozess kostet euch taeglich Zeit?"
· rawkeep.com · Prozess-Check (1 Woche, Festpreis).

## Format
Hook in Zeile 1. Kurze Absaetze, max. 1-2 Listen. 3-5 Hashtags am Ende.
PROFILENDE
  echo "✓ Tonalitätsprofil angelegt: $PROFIL"
else
  echo "✓ Tonalitätsprofil vorhanden — bleibt unverändert."
fi
echo

# 2) Ersten Post erzeugen
echo "… erzeuge den ersten LinkedIn-Post (GroundedRAG) …"
echo "──────────────────────────────────────────────────────────"
$CP erstellen "Ich habe eine KI gebaut, die zugibt, wenn sie etwas nicht weiss. Die meisten RAG-Systeme (Chat mit deinen Dokumenten) antworten immer - auch wenn die Quelle duenn ist. GroundedRAG verweigert lieber, als zu halluzinieren: jede Antwort quellenverifiziert, Zitat fuer Zitat, oder ein ehrliches 'Ich weiss es nicht'. Laeuft komplett offline (SQLite + lokales LLM), Open Source. Fuer alle, die ihren Firmendaten Fragen stellen wollen, ohne der Antwort misstrauen zu muessen." --plattformen linkedin
echo "──────────────────────────────────────────────────────────"
echo
echo "✓ Fertig. Oben steht dein fertiger Post."
echo "  → Text markieren, kopieren, auf LinkedIn einfuegen,"
echo "    Video media/demo-groundedrag.mp4 anhaengen, posten."
echo
read -p "  (Enter zum Schließen)"
