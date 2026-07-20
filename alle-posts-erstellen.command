#!/bin/bash
# ◆ Alle LinkedIn-Posts erzeugen — Doppelklick genügt.
# Legt (idempotent) das Rawkeep-Tonalitätsprofil an und erzeugt die
# komplette erste Content-Staffel (6 Posts) im Kalender. Jeder Post
# erscheint fertig formatiert im Fenster zum Kopieren.
set -e
cd "$(dirname "$0")"

echo "◆ Content-Pilot — Rawkeep Content-Staffel (6 Posts)"
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

# Tonalitätsprofil sicherstellen (überschreibt eigene Änderungen nie)
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

# Die Post-Ideen (Seed-Sätze in Rawkeep-Stimme). Der Content-Pilot
# formatiert daraus plattformgerechte LinkedIn-Posts.
IDEEN=(
"GroundedRAG: Ich habe eine KI gebaut, die zugibt, wenn sie etwas nicht weiss. Die meisten RAG-Systeme antworten immer, auch wenn die Quelle duenn ist - und halluzinieren. GroundedRAG verweigert lieber: jede Antwort quellenverifiziert Zitat fuer Zitat, oder ein ehrliches 'Ich weiss es nicht'. Komplett offline, Open Source. Ehrliche Grenze: niedrigere Trefferquote, dafuer Vertrauen."
"EIS Autonom-Modus: 40 Lieferscheine pro Woche von Hand aus PDFs in Excel abtippen war bei vielen Exporteuren jahrelang normal. Mein Export-Flaggschiff EIS macht das im Autonom-Modus: OCR-Import, sechs Agenten pruefen Compliance (Nigeria, CBAM, Sanktionen) nach festen Regeln, bei allem Kritischen eine Freigabe-Karte fuer den Menschen. Autonomie wird verdient, nicht verschenkt."
"Vier Prinzipien: Nach 30+ Software-Projekten habe ich vier Prinzipien, die ich nicht mehr verhandle. Lokal-first (eure Daten bleiben bei euch). Agentic (Software handelt, zeigt nicht nur Daten). Human-in-the-Loop (die KI schlaegt vor, ihr entscheidet, alles im Audit-Log). Messbar (gesparte Stunden statt Buzzwords). Unbequemer zu bauen als ein ChatGPT-Wrapper - aber der Unterschied zwischen Tool und System."
"Prozess-Check: 'Wir muessten mal was mit KI machen' ist der falsche Startpunkt. Der richtige: EIN konkreter Prozess, der nachweislich Zeit frisst. Deshalb gibt es bei mir den Prozess-Check - eine Woche, Festpreis: echten Ablauf zerlegen, ehrliche ROI-Schaetzung (auch ein 'lohnt sich nicht' ist ein Ergebnis), plus lauffaehiger Prototyp am echten Fall. Kein Foliensatz."
"Export nach Afrika: Export nach Nigeria ist ein Dokumenten-Marathon - Form M, SONCAP, CBAM, Sanktionslisten. Ich habe 15 Jahre Aussenhandel gemacht, bevor ich angefangen habe, genau diese Ablaeufe in Software zu giessen. Meine Weltkarte zeigt fuer 197 Laender Zoll, Haefen, Incoterms und Frachtrouten - offline-faehig. Fachwissen, das im Code steckt, nicht in einem Handbuch."
"Zwei Welten: Ich bin gelernter Aussenhandelskaufmann und entwickle seit 2006 Software - erst aus Hobby, dann im Studium der Wirtschaftsinformatik formalisiert. Diese zwei Welten sind mein Vorteil: Ich verstehe den Fachbereich UND den Code, und uebersetze ohne Verlust zwischen beiden. Ich baue die Werkzeuge, die ich als Fachanwender selbst immer vermisst habe."
)

n=1
for idee in "${IDEEN[@]}"; do
  echo "══════════ Post $n von ${#IDEEN[@]} ══════════"
  $CP erstellen "$idee" --plattformen linkedin
  echo
  n=$((n+1))
done

echo "════════════════════════════════════════════════"
echo "✓ Fertig — alle Posts liegen im Kalender."
echo "  Anzeigen:  $CP kalender"
echo "  Jeder Post ist oben fertig formatiert zum Kopieren."
echo "  Verteile sie uebers Programm: 2x pro Woche (Mo + Do vormittags)."
echo
read -p "  (Enter zum Schließen)"
