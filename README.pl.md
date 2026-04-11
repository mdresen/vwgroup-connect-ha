# VAG Connect — Home Assistant

**[Deutsch](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Chciałem sterować swoim samochodem z Home Assistant bez utrzymywania trzech osobnych integracji czy uruchamiania dedykowanego brokera MQTT. Więc zbudowałem to.

**VAG Connect** łączy Home Assistant bezpośrednio z oficjalnymi aplikacjami Audi, VW, Skoda, SEAT i CUPRA. Bez pośredników, bez Dockera, bez dodatkowej usługi. Zainstaluj integrację, wpisz dane logowania, gotowe.

Ciężką pracę techniczną wykonał głównie Till Steinbach swoim frameworkiem [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity). Ta integracja to w zasadzie czysty wrapper Home Assistant wokół niego.

---

## Installation

### Przez HACS (zalecane)

1. HACS → Integracje → ⋮ → Niestandardowe repozytoria
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Kategoria: Integracja
3. Wyszukaj **VAG Connect**, zainstaluj, zrestartuj HA

---

## Prawne

Ta integracja korzysta z nieoficjalnych API — tych samych, których używają oficjalne aplikacje. Nie jest autoryzowana przez Audi AG, Volkswagen AG, CARIAD, Škoda Auto ani SEAT S.A. Wszystkie nazwy marek są własnością ich właścicieli. Szczegóły w [NOTICE.md](NOTICE.md).

---

*Zbudowane door/por/przez/od/av [prash1407](https://github.com/Prash1407) · MIT License · 2026*
