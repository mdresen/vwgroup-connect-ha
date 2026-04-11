# VAG Connect — Home Assistant Integration

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)

**Die erste einheitliche Home Assistant Integration für alle VAG-Fahrzeuge.**

Unterstützt: **Audi · Volkswagen (EU) · Volkswagen (US/CA) · Škoda · SEAT · CUPRA**

---

## Funktionen

| Funktion | Audi | VW | Skoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Tankfüllstand / Batteriestand | ✅ | ✅ | ✅ | ✅ |
| Reichweite | ✅ | ✅ | ✅ | ✅ |
| Kilometerstand | ✅ | ✅ | ✅ | ✅ |
| GPS-Position (Karte) | ✅ | ✅ | ✅ | ✅ |
| Türen & Fenster Status | ✅ | ✅ | ✅ | ✅ |
| Türen verriegeln / entriegeln | ✅ | ✅ | ✅ | ✅ |
| Klimatisierung starten / stoppen | ✅ | ✅ | ✅ | ✅ |
| Laden starten / stoppen (EV) | ✅ | ✅ | ✅ | ✅ |
| Ladekabel-Status (EV) | ✅ | ✅ | ✅ | ✅ |
| Ölstand | ✅ | ✅ | – | – |
| Inspektionsdaten | ✅ | ✅ | ✅ | ✅ |
| Außentemperatur | ✅ | ✅ | ✅ | ✅ |
| Lichtsignal (Honk & Flash) | ✅ | ✅ | ✅ | ✅ |

---

## Installation

### Via HACS (empfohlen)

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/prash1407/vag-connect-ha`  
   Kategorie: `Integration`
3. Suche nach **VAG Connect** und installieren
4. Home Assistant neu starten

### Manuell

1. Den Ordner `custom_components/vag_connect/` in dein HA `custom_components/` Verzeichnis kopieren
2. Home Assistant neu starten

---

## Einrichtung

1. **Einstellungen → Geräte & Dienste → + Integration hinzufügen**
2. Nach **VAG Connect** suchen
3. Marke wählen, App-E-Mail und Passwort eingeben
4. Optional: S-PIN für Verriegelungsaktionen

> ⚠️ **Hinweis:** Das Mindestintervall ist 5 Minuten. Zu häufige Abfragen können zur  
> temporären Sperrung deines Audi/VW-Kontos führen. Empfehlung: 15 Minuten.

---

## Technische Basis

Diese Integration basiert auf **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** von Till Steinbach als API-Engine. Die unterstützten Backends:

| Marke | API-Backend | Connector |
|---|---|---|
| Audi | CARIAD / myAudi (`emea.bff.cariad.digital`) | [CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi) |
| VW EU | WeConnect (`emea.bff.cariad.digital`) | [CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen) |
| VW NA | VW Car-Net US | [CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na) |
| Skoda | MySkoda API | [CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda) |
| SEAT/CUPRA | MyCupra API | [CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra) |

---

## Haftungsausschluss

Diese Integration ist nicht von Audi AG, Volkswagen AG oder dem VW-Konzern autorisiert  
oder unterstützt. Nutzung auf eigene Gefahr. Die Hersteller können ihre APIs jederzeit  
ohne Vorankündigung ändern.

---

## Mitmachen

PRs willkommen! Besonders gesucht:
- Tester mit Porsche (Cariad-API)
- Tester mit chinesischen VAG-Accounts (CN-Region)
- Weitere Übersetzungen

## Lizenz

MIT — siehe [LICENSE](LICENSE)
