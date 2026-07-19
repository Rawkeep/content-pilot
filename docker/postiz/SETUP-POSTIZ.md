# Postiz self-hosted aufsetzen (einmalig, ~15 Minuten)

Postiz übernimmt für den Content-Pilot die Plattform-Anbindungen (OAuth,
Veröffentlichen). Es läuft komplett auf deinem Rechner/Server — DSGVO-freundlich.

## 1. Starten

**Der einfachste Weg (Mac): Doppelklick auf `postiz-starten.command`** in
diesem Ordner — setzt das JWT-Secret automatisch, fragt optional die
LinkedIn-Zugangsdaten ab, startet die Container und öffnet den Browser.
Erneuter Doppelklick später: trägt LinkedIn nach bzw. startet einfach neu.

<details><summary>Manuell (Terminal)</summary>

```bash
cd docker/postiz
```

In `docker-compose.yml` **JWT_SECRET ändern** (irgendein langer Zufallswert), dann:

```bash
docker compose up -d
```

</details>

Nach ~1 Minute: <http://localhost:5000> öffnen → Konto anlegen (erste
Registrierung wird Admin).

## 2. Social-Accounts verbinden

In Postiz: **Add Channel** → Plattform wählen (LinkedIn, X, Instagram …) und
den OAuth-Flow durchklicken. Für einige Plattformen brauchst du eigene
Developer-App-Keys — die Anleitung je Plattform steht in der Postiz-Doku
(<https://docs.postiz.com/providers>).

> Tipp für den Start: **LinkedIn zuerst** — der Flow ist am einfachsten,
> und für dein Agentur-Marketing ist es ohnehin der wichtigste Kanal.

### LinkedIn verbinden (einmalig, ~10 Minuten)

Self-hosted Postiz braucht eine **eigene LinkedIn-Developer-App**:

1. <https://developer.linkedin.com> → **Create app**. Pflichtfeld ist eine
   verknüpfte **LinkedIn-Unternehmensseite** — falls noch keine existiert,
   vorher unter <https://www.linkedin.com/company/setup/new/> anlegen (2 Min.).
2. In der App → Tab **Products**: **„Share on LinkedIn"** und **„Sign In with
   LinkedIn using OpenID Connect"** anfordern (beide werden sofort freigeschaltet).
3. Tab **Auth** → **Authorized redirect URLs** eintragen:
   `http://localhost:5000/integrations/social/linkedin`
   (bzw. deine `FRONTEND_URL` + `/integrations/social/linkedin`).
4. **Client ID** und **Primary Client Secret** (Tab Auth) in die
   `docker-compose.yml` bei `LINKEDIN_CLIENT_ID`/`LINKEDIN_CLIENT_SECRET`
   eintragen → `docker compose up -d` (Container startet neu).
5. Postiz → **Add Channel → LinkedIn** → OAuth durchklicken → dein Profil
   erscheint als Kanal. Fertig.

> **Persönliches Profil vs. Unternehmensseite:** Posten aufs persönliche
> Profil funktioniert sofort („Share on LinkedIn"). Für das Posten **als
> Unternehmensseite** verlangt LinkedIn zusätzlich die Freigabe der
> Community-Management-API (Antrag, dauert Tage bis Wochen) — fürs
> Agentur-Marketing ist das persönliche Profil ohnehin der stärkere Kanal.

## 3. API-Key für den Content-Pilot holen

Postiz → **Settings → Public API** → Key kopieren. Dann:

```bash
export CP_POSTIZ_URL="http://localhost:5000/api"
export CP_POSTIZ_API_KEY="<dein-key>"
```

(Am besten in `~/.zshrc` eintragen.)

## 4. Testen

```bash
contentpilot erstellen "Testpost vom Content-Pilot" --plattformen linkedin
contentpilot kalender
contentpilot senden 1
```

Der Post erscheint in Postiz im Kalender und wird von dort veröffentlicht.

## Hinweise

- Details des Compose-Setups können sich mit neuen Postiz-Versionen ändern —
  maßgeblich ist <https://docs.postiz.com/installation/docker-compose>.
- Updates: `docker compose pull && docker compose up -d`.
- Backup: die Docker-Volumes `postiz-postgres` und `postiz-config` sichern.

## 5. Optional: automatische Backups (databasement)

[databasement](https://github.com/David-Crty/databasement) (MIT) sichert die
Postiz-Datenbank automatisch — täglich/wöchentlich, AES-256-verschlüsselt,
nach lokal, S3 oder SFTP, mit Benachrichtigung (E-Mail/Telegram/Webhook):

```bash
docker compose -f docker-compose.yml -f docker-compose.backup.yml up -d
```

Dann <http://localhost:2226> öffnen → Account anlegen → Server hinzufügen:
Host `postiz-postgres`, Datenbank/User/Passwort `postiz` (bzw. deine Werte
aus der docker-compose.yml) → Zeitplan „täglich" + Aufbewahrung setzen.
Restore geht über dieselbe Oberfläche — auch auf einen anderen Server.
