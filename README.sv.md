# VAG Connect — Home Assistant

**[Deutsch](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Jag ville styra min bil från Home Assistant utan att underhålla tre separata integrationer eller köra en dedikerad MQTT-broker. Så jag byggde det här.

**VAG Connect** kopplar Home Assistant direkt till de officiella apparna för Audi, VW, Skoda, SEAT och CUPRA. Inget mellanlager, ingen Docker, ingen extra tjänst. Installera integrationen, ange dina inloggningsuppgifter, klart.

Det tunga tekniska arbetet gjordes främst av Till Steinbach med hans [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)-ramverk. Den här integrationen är i princip ett rent Home Assistant-omslag runt det.

---

## Installation

### Via HACS (rekommenderat)

1. HACS → Integrationer → ⋮ → Anpassade arkiv
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Kategori: Integration
3. Sök efter **VAG Connect**, installera, starta om HA

---

## Juridiskt

Den här integrationen använder inofficiella API:er — samma som de officiella apparna använder. Den är inte godkänd av Audi AG, Volkswagen AG, CARIAD, Škoda Auto eller SEAT S.A. Alla varumärken tillhör sina respektive ägare. Detaljer i [NOTICE.md](NOTICE.md).

---

*Byggt door/por/przez/od/av [prash1407](https://github.com/Prash1407) · MIT License · 2026*
