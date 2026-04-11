# VAG Connect — Home Assistant

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)

**[English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Ich wollte meinen Audi in Home Assistant steuern, ohne drei verschiedene Integrationen parallel zu pflegen oder einen extra MQTT-Broker zu betreiben. Also hab ich das hier gebaut.

**VAG Connect** verbindet Home Assistant direkt mit den offiziellen Apps von Audi, VW, Skoda, SEAT und CUPRA. Keine Zwischenschicht, kein Docker, kein separater Dienst. Integration installieren, Zugangsdaten eingeben, fertig.

Die technische Arbeit dahinter hat vor allem Till Steinbach mit seinem [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)-Framework erledigt. Diese Integration ist im Grunde ein sauberer Home Assistant-Wrapper darum.

---

## Was funktioniert

| Funktion | Audi | VW | Skoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Tankfüllstand / Ladestand | ✅ | ✅ | ✅ | ✅ |
| Reichweite | ✅ | ✅ | ✅ | ✅ |
| Kilometerstand | ✅ | ✅ | ✅ | ✅ |
| Position auf der Karte | ✅ | ✅ | ✅ | ✅ |
| Türen & Fenster Status | ✅ | ✅ | ✅ | ✅ |
| Verriegeln / Entriegeln | ✅ | ✅ | ✅ | ✅ |
| Klimatisierung starten | ✅ | ✅ | ✅ | ✅ |
| Laden starten / stoppen | ✅ | ✅ | ✅ | ✅ |
| Ladziel setzen (Slider) | ✅ | ✅ | ✅ | ✅ |
| Ölstand, Inspektion | ✅ | ✅ | – | – |
| Außentemperatur | ✅ | ✅ | ✅ | ✅ |
| Lichtsignal | ✅ | ✅ | ✅ | ✅ |

Nicht alle Funktionen sind bei jedem Modell verfügbar — das hängt vom Fahrzeug und den gebuchten Connected-Services ab. Was in der App nicht geht, geht hier auch nicht.

---

## Installation

### Über HACS (empfohlen)

1. HACS öffnen → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Kategorie: Integration
3. Nach **VAG Connect** suchen, installieren, HA neu starten

### Manuell

Den Ordner `custom_components/vag_connect/` aus diesem Repository in dein `config/custom_components/`-Verzeichnis kopieren, dann Home Assistant neu starten.

---

## Einrichtung

**Einstellungen → Geräte & Dienste → + Integration → "VAG Connect"**

Du wirst nach vier Dingen gefragt:

- **Marke** — Audi, VW (EU), VW (US/CA), Skoda oder SEAT/CUPRA
- **E-Mail** — dieselbe wie in der App
- **Passwort** — dasselbe wie in der App
- **S-PIN** — optional, aber ohne die geht Verriegeln nicht

Das war's. Nach dem ersten Laden erscheint dein Auto als Gerät mit allen verfügbaren Sensoren.

---

## Abfrageintervall

Standard sind 15 Minuten. Du kannst das unter **Einstellungen → Geräte & Dienste → VAG Connect → Konfigurieren** ändern.

Geh nicht unter 5 Minuten. Die Hersteller-APIs werden nicht öffentlich betrieben und zu viele Anfragen können deinen Account temporär sperren. Das steht auch in den Nutzungsbedingungen von Audi Connect und WeConnect.

---

## Automationen

Alle wichtigen Aktionen stehen auch als HA-Services bereit:

```yaml
# Verriegeln
service: vag_connect.lock
data:
  vin: "WAUZZZ4G7EN123456"

# Klimatisierung starten
service: vag_connect.start_climatisation
data:
  vin: "WAUZZZ4G7EN123456"

# Laden stoppen
service: vag_connect.stop_charging
data:
  vin: "WAUZZZ4G7EN123456"
```

Die VIN steht in der App unter Fahrzeugdetails, oder du schaust kurz in die Entities — sie taucht als Geräte-ID auf.

---

## Fehlermeldungen & Debugging

Wenn etwas nicht funktioniert, aktivier zuerst Debug-Logging:

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.vag_connect: debug
```

Dann HA neu starten und das Log anschauen. Die meisten Probleme sind entweder falsche Zugangsdaten oder eine geänderte API auf Herstellerseite.

Wenn du einen Bug meldest, lad bitte die **Diagnose-Datei** herunter (Einstellungen → Geräte & Dienste → VAG Connect → ⋮ → Diagnose). Die enthält keine Passwörter oder GPS-Daten, hilft aber enorm.

---

## Mitmachen

PRs und Issues sind willkommen. Was besonders fehlt:

- Jemand mit **Porsche** zum Testen (nutzt dieselbe CARIAD-API wie Audi)
- Jemand mit einem **chinesischen VAG-Account** (CN-Region hat andere Endpoints)
- Weitere Übersetzungen — eine neue Sprachdatei ist in 20 Minuten gemacht, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Rechtliches

Diese Integration nutzt inoffizielle APIs — dieselben, die die offiziellen Apps nutzen. Sie ist weder von Audi AG, Volkswagen AG, CARIAD, Škoda Auto, SEAT S.A. noch von Nabu Casa autorisiert oder unterstützt.

Audi, myAudi, Volkswagen, WeConnect, Škoda, MySkoda, SEAT, CUPRA und alle weiteren Markennamen sind Warenzeichen ihrer jeweiligen Inhaber.

Alle genutzten Bibliotheken stehen unter MIT-Lizenz. Details und Attributionen in [NOTICE.md](NOTICE.md).

---

*Gebaut von [prash1407](https://github.com/Prash1407) · MIT Lizenz · 2026*
