# VAG Connect — Home Assistant

**[Deutsch](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Chtěl jsem ovládat své auto z Home Assistant bez správy tří samostatných integrací nebo provozování dedikovaného MQTT brokeru. Tak jsem to postavil.

**VAG Connect** připojuje Home Assistant přímo k oficiálním aplikacím Audi, VW, Skoda, SEAT a CUPRA. Žádný mezičlánek, žádný Docker, žádná extra služba. Nainstalujte integraci, zadejte přihlašovací údaje, hotovo.

Těžkou technickou práci odvedl především Till Steinbach svým frameworkem [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity). Tato integrace je v podstatě čistý wrapper pro Home Assistant kolem něj.

---

## Installation

### Přes HACS (doporučeno)

1. HACS → Integrace → ⋮ → Vlastní repozitáře
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Kategorie: Integrace
3. Vyhledejte **VAG Connect**, nainstalujte, restartujte HA

---

## Právní upozornění

Tato integrace používá neoficiální API — stejná, která používají oficiální aplikace. Není autorizována společnostmi Audi AG, Volkswagen AG, CARIAD, Škoda Auto ani SEAT S.A. Všechny názvy značek jsou majetkem svých vlastníků. Podrobnosti v [NOTICE.md](NOTICE.md).

---

*Vytvořeno door/por/przez/od/av [prash1407](https://github.com/Prash1407) · MIT License · 2026*
