"""CLI des Content-Piloten.

contentpilot erstellen "Wir haben X gelauncht" --plattformen linkedin,x
contentpilot kalender
contentpilot senden 3
contentpilot ui
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import calendar_store
from .backends import create_backend
from .config import from_env
from .generator import generate
from .platforms import PLATFORMS, full_text
from .profile import ensure_profile


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="contentpilot", description="Deutsches KI-Content-Studio (Rawkeep)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    erstellen = sub.add_parser("erstellen", help="Idee → plattformgerechte Post-Varianten")
    erstellen.add_argument("idee", help="Die Nachricht/Idee in einem Satz oder Absatz")
    erstellen.add_argument(
        "--plattformen",
        default="linkedin,x",
        help=f"Kommagetrennt; verfügbar: {', '.join(PLATFORMS)}",
    )
    erstellen.add_argument("--datum", help="Geplanter Zeitpunkt (ISO, z. B. 2026-07-20T09:00)")
    erstellen.add_argument("--backend", help="auto | claude | ollama | mock")

    sub.add_parser("kalender", help="Content-Kalender anzeigen")

    senden = sub.add_parser("senden", help="Kalender-Eintrag an Postiz übergeben")
    senden.add_argument("id", type=int, help="Eintrags-ID aus 'contentpilot kalender'")
    senden.add_argument("--sofort", action="store_true", help="sofort posten statt planen")

    sub.add_parser("profil", help="Tonalitäts-Profil anzeigen/anlegen")
    sub.add_parser("plattformen", help="Unterstützte Plattformen + Limits")

    ui = sub.add_parser("ui", help="Lokales Web-Interface (http://localhost:8801)")
    ui.add_argument("--port", type=int, default=8801)
    ui.add_argument("--no-browser", action="store_true")

    args = parser.parse_args(argv)
    settings = from_env()

    if args.command == "plattformen":
        for key, spec in PLATFORMS.items():
            print(
                f"  {key:<10} {spec.label:<14} max. {spec.max_chars} Zeichen, "
                f"{spec.max_hashtags} Hashtags"
            )
        return 0

    if args.command == "profil":
        path = ensure_profile(settings)
        print(f"Profil: {path}\n\n{path.read_text(encoding='utf-8')}")
        return 0

    if args.command == "ui":
        from .ui import serve

        serve(args.port, open_browser=not args.no_browser)
        return 0

    if args.command == "kalender":
        entries = calendar_store.load(settings)
        if not entries:
            print("Kalender ist leer — 'contentpilot erstellen \"…\"' legt los.")
            return 0
        for entry in entries:
            when = entry.scheduled or "—"
            print(
                f"  [{entry.id}] {entry.platform:<10} {entry.status:<8} {when}  "
                f"{entry.text[:60].replace(chr(10), ' ')}"
            )
        return 0

    if args.command == "senden":
        from .postiz import PostizClient, PostizError

        eintrag = calendar_store.get(settings, args.id)
        if eintrag is None:
            print(f"❌ Eintrag {args.id} nicht gefunden.")
            return 1
        try:
            client = PostizClient(settings)
            integration = client.find_integration(eintrag.platform)
            if integration is None:
                print(f"❌ Kein verbundener {eintrag.platform}-Account in Postiz gefunden.")
                return 1
            from datetime import datetime, timedelta

            date_iso = eintrag.scheduled or (datetime.now() + timedelta(minutes=10)).isoformat()
            from .schemas import PostVariant

            variant = PostVariant(
                platform=eintrag.platform, text=eintrag.text, hashtags=eintrag.hashtags
            )
            postiz_id = client.schedule_post(
                str(integration["id"]),
                full_text(variant),
                date_iso,
                post_type="now" if args.sofort else "schedule",
            )
        except PostizError as error:
            print(f"❌ {error}")
            return 1
        eintrag.status = "gesendet"
        eintrag.postiz_id = postiz_id
        calendar_store.update(settings, eintrag)
        print(
            f"✅ An Postiz übergeben ({integration.get('name', eintrag.platform)}, Post {postiz_id})."
        )
        return 0

    # erstellen
    if args.backend:
        settings.backend = args.backend
    ensure_profile(settings)
    variants, warnings = generate(
        args.idee, args.plattformen.split(","), settings, create_backend(settings)
    )
    for variant in variants:
        entry = calendar_store.add(
            settings,
            platform=variant.platform,
            text=variant.text,
            hashtags=variant.hashtags,
            idea=args.idee,
            scheduled=args.datum,
            warnings=warnings,
        )
        print(
            f"\n── [{entry.id}] {PLATFORMS[variant.platform].label} "
            f"({len(full_text(variant))} Zeichen) " + "─" * 20
        )
        print(full_text(variant))
    for warning in warnings:
        print(f"\n  ⚠ {warning}")
    print("\n✅ Im Kalender gespeichert — senden mit: contentpilot senden <ID>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
