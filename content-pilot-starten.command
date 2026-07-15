#!/bin/zsh
# Content-Pilot per Doppelklick starten (macOS).
# Öffnet automatisch http://localhost:8801 im Browser — Strg+C beendet.
cd "$(dirname "$0")"

if ! python3 -c "import contentpilot" 2>/dev/null; then
  echo "Erststart: installiere Content-Pilot ..."
  python3 -m pip install --user --quiet --upgrade pip setuptools
  python3 -m pip install --user --quiet -e . || python3 -m pip install --user --quiet "pydantic>=2"
fi

exec python3 -m contentpilot.cli ui
