# VAG Connect — Home Assistant

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)

**[Deutsch](README.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

I wanted to control my Audi from Home Assistant without maintaining three separate integrations or running a dedicated MQTT broker. So I built this.

**VAG Connect** connects Home Assistant directly to the official apps of Audi, VW, Skoda, SEAT, and CUPRA. No middleware, no Docker, no extra service. Install the integration, enter your credentials, done.

The hard technical work was mostly done by Till Steinbach with his [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) framework. This integration is essentially a clean Home Assistant wrapper around it.

---

## What works

| Feature | Audi | VW | Skoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Fuel / battery level | ✅ | ✅ | ✅ | ✅ |
| Range | ✅ | ✅ | ✅ | ✅ |
| Odometer | ✅ | ✅ | ✅ | ✅ |
| Position on map | ✅ | ✅ | ✅ | ✅ |
| Door & window status | ✅ | ✅ | ✅ | ✅ |
| Lock / unlock | ✅ | ✅ | ✅ | ✅ |
| Start climatisation | ✅ | ✅ | ✅ | ✅ |
| Start / stop charging | ✅ | ✅ | ✅ | ✅ |
| Charge target slider | ✅ | ✅ | ✅ | ✅ |
| Oil level, service due | ✅ | ✅ | – | – |
| Outside temperature | ✅ | ✅ | ✅ | ✅ |
| Flash lights | ✅ | ✅ | ✅ | ✅ |

Not all features are available on every model — that depends on your vehicle and which connected services you have. If it doesn't work in the app, it won't work here either.

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom Repositories
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Category: Integration
3. Search for **VAG Connect**, install, restart HA

### Manual

Copy the `custom_components/vag_connect/` folder from this repository into your `config/custom_components/` directory, then restart Home Assistant.

---

## Setup

**Settings → Devices & Services → + Add Integration → "VAG Connect"**

You'll be asked for four things:

- **Brand** — Audi, VW (EU), VW (US/CA), Skoda, or SEAT/CUPRA
- **Email** — same as in the app
- **Password** — same as in the app
- **S-PIN** — optional, but locking won't work without it

That's it. After the first poll, your car appears as a device with all available sensors.

---

## Poll interval

The default is 15 minutes. You can change it under **Settings → Devices & Services → VAG Connect → Configure**.

Don't go below 5 minutes. The manufacturer APIs are not public infrastructure, and too many requests can temporarily lock your account. This is also in the terms of service for Audi Connect and WeConnect.

---

## Automations

All major actions are also available as HA services:

```yaml
# Lock
service: vag_connect.lock
data:
  vin: "WAUZZZ4G7EN123456"

# Start climatisation
service: vag_connect.start_climatisation
data:
  vin: "WAUZZZ4G7EN123456"

# Stop charging
service: vag_connect.stop_charging
data:
  vin: "WAUZZZ4G7EN123456"
```

The VIN is in the app under vehicle details, or check the entities — it shows up as the device ID.

---

## Debugging

If something doesn't work, enable debug logging first:

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.vag_connect: debug
```

Restart HA and check the log. Most problems are either wrong credentials or a changed API on the manufacturer side.

When filing a bug report, please download the **diagnostics file** (Settings → Devices & Services → VAG Connect → ⋮ → Diagnostics). It contains no passwords or GPS data, but helps a lot.

---

## Contributing

PRs and issues welcome. What's especially missing:

- Someone with a **Porsche** to test (uses the same CARIAD API as Audi)
- Someone with a **Chinese VAG account** (CN region has different endpoints)
- More translations — a new language file takes about 20 minutes, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Legal

This integration uses unofficial APIs — the same ones the official apps use. It is not authorized or endorsed by Audi AG, Volkswagen AG, CARIAD, Škoda Auto, SEAT S.A., or Nabu Casa.

Audi, myAudi, Volkswagen, WeConnect, Škoda, MySkoda, SEAT, CUPRA and all other brand names are trademarks of their respective owners.

All libraries used are MIT licensed. Full attributions in [NOTICE.md](NOTICE.md).

---

*Built by [prash1407](https://github.com/Prash1407) · MIT License · 2026*
