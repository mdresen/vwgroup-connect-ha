# VAG Connect — Home Assistant

**[Deutsch](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Ik wilde mijn auto vanuit Home Assistant bedienen zonder drie losse integraties bij te houden of een aparte MQTT-broker te draaien. Dus bouwde ik dit.

**VAG Connect** verbindt Home Assistant rechtstreeks met de officiële apps van Audi, VW, Skoda, SEAT en CUPRA. Geen tussenlaag, geen Docker, geen extra dienst. Installeer de integratie, vul je inloggegevens in, klaar.

Het zware technische werk is grotendeels gedaan door Till Steinbach met zijn [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) framework. Deze integratie is in feite een nette Home Assistant-wrapper daaromheen.

---

## Installation

### Via HACS (aanbevolen)

1. HACS → Integraties → ⋮ → Aangepaste repositories
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Categorie: Integratie
3. Zoek naar **VAG Connect**, installeer, herstart HA

---

## Juridisch

Deze integratie gebruikt onofficiële API's — dezelfde die de officiële apps gebruiken. Ze is niet goedgekeurd door Audi AG, Volkswagen AG, CARIAD, Škoda Auto of SEAT S.A. Alle merknamen zijn eigendom van hun respectieve houders. Details in [NOTICE.md](NOTICE.md).

---

*Gebouwd door/por/przez/od/av [prash1407](https://github.com/Prash1407) · MIT License · 2026*
