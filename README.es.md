# VAG Connect — Home Assistant

**[Deutsch](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Quería controlar mi coche desde Home Assistant sin mantener tres integraciones separadas ni ejecutar un broker MQTT dedicado. Así que construí esto.

**VAG Connect** conecta Home Assistant directamente con las aplicaciones oficiales de Audi, VW, Skoda, SEAT y CUPRA. Sin intermediarios, sin Docker, sin servicio extra. Instala la integración, introduce tus credenciales, listo.

El trabajo técnico duro fue realizado principalmente por Till Steinbach con su framework [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity). Esta integración es básicamente un wrapper limpio de Home Assistant alrededor de él.

---

## Installation

### A través de HACS (recomendado)

1. HACS → Integraciones → ⋮ → Repositorios personalizados
2. URL: `https://github.com/Prash1407/vag-connect-ha`, Categoría: Integración
3. Buscar **VAG Connect**, instalar, reiniciar HA

---

## Legal

Esta integración utiliza API no oficiales — las mismas que usan las apps oficiales. No está autorizada por Audi AG, Volkswagen AG, CARIAD, Škoda Auto ni SEAT S.A. Todos los nombres de marca son propiedad de sus respectivos titulares. Detalles en [NOTICE.md](NOTICE.md).

---

*Creado door/por/przez/od/av [prash1407](https://github.com/Prash1407) · MIT License · 2026*
