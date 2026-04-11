# VAG Connect — Home Assistant

**[Deutsch](README.md) · [English](README.en.md) · [Nederlands](README.nl.md) · [Español](README.es.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md)**

---

Je voulais contrôler ma voiture depuis Home Assistant sans maintenir trois intégrations séparées ni faire tourner un broker MQTT dédié. Alors j'ai construit ça.

**VAG Connect** connecte Home Assistant directement aux applications officielles d'Audi, VW, Skoda, SEAT et CUPRA. Pas d'intermédiaire, pas de Docker, pas de service supplémentaire. On installe l'intégration, on entre ses identifiants, c'est tout.

Le travail technique difficile a surtout été accompli par Till Steinbach avec son framework [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity). Cette intégration en est essentiellement un wrapper propre pour Home Assistant.

---

## Ce qui fonctionne

| Fonctionnalité | Audi | VW | Skoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Niveau carburant / batterie | ✅ | ✅ | ✅ | ✅ |
| Autonomie | ✅ | ✅ | ✅ | ✅ |
| Kilométrage | ✅ | ✅ | ✅ | ✅ |
| Position sur la carte | ✅ | ✅ | ✅ | ✅ |
| État portes & vitres | ✅ | ✅ | ✅ | ✅ |
| Verrouillage / déverrouillage | ✅ | ✅ | ✅ | ✅ |
| Démarrer la climatisation | ✅ | ✅ | ✅ | ✅ |
| Démarrer / arrêter la charge | ✅ | ✅ | ✅ | ✅ |
| Curseur objectif de charge | ✅ | ✅ | ✅ | ✅ |
| Niveau d'huile, révision | ✅ | ✅ | – | – |
| Température extérieure | ✅ | ✅ | ✅ | ✅ |
| Signal lumineux | ✅ | ✅ | ✅ | ✅ |

Tout ne fonctionne pas sur tous les modèles — ça dépend du véhicule et des services connectés souscrits. Ce qui ne marche pas dans l'app ne marchera pas ici non plus.

---

## Installation

### Via HACS (recommandé)

1. HACS → Intégrations → ⋮ → Dépôts personnalisés
2. URL : `https://github.com/Prash1407/vag-connect-ha`, Catégorie : Intégration
3. Rechercher **VAG Connect**, installer, redémarrer HA

### Manuel

Copier le dossier `custom_components/vag_connect/` dans votre répertoire `config/custom_components/`, puis redémarrer Home Assistant.

---

## Configuration

**Paramètres → Appareils et services → + Ajouter une intégration → "VAG Connect"**

Quatre informations sont demandées : marque, e-mail, mot de passe, et S-PIN (facultatif, mais nécessaire pour le verrouillage).

---

## Intervalle de mise à jour

Par défaut : 15 minutes. Ne pas descendre en dessous de 5 minutes — trop de requêtes peuvent bloquer temporairement votre compte.

---

## Mentions légales

Cette intégration utilise des API non officielles — les mêmes que les apps officielles. Elle n'est pas autorisée par Audi AG, Volkswagen AG, CARIAD, Škoda Auto ou SEAT S.A.

Tous les noms de marques sont la propriété de leurs détenteurs respectifs. Détails dans [NOTICE.md](NOTICE.md).

---

*Créé par [prash1407](https://github.com/Prash1407) · Licence MIT · 2026*
