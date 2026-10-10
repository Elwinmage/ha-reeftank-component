# ReefTank 🐟
> Fait partie de l'[**écosystème ReefTech**](https://elwinmage.github.io/reeftank/)
<p align="center">
  <img src="https://github.com/Elwinmage/ha-reeftank-component/raw/main/icon.png"  width="50%"/>
</p>

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/hacs)
[![IoT Class](https://img.shields.io/badge/IoT%20Class-Calculated-green?style=flat-square)](https://developers.home-assistant.io/docs/architecture_index/#branding)
[![GH-release](https://img.shields.io/github/v/release/Elwinmage/ha-reeftank-component.svg?style=flat-square)](https://github.com/Elwinmage/ha-reeftank-component/releases)
![Installations](https://img.shields.io/badge/dynamic/json?label=Active%20Installs&query=estimated&cacheSeconds=3600&url=https%3A%2F%2Fraw.githubusercontent.com%2FElwinmage%2Fha-reeftank-component%2Fmain%2Fbadges%2Fstats.json&color=CE1126&logo=home-assistant)
[![Ruff Status](https://github.com/Elwinmage/ha-reeftank-component/actions/workflows/main.yml/badge.svg)](https://github.com/Elwinmage/ha-reeftank-component/actions/workflows/main.yml)
[![HA & HACS Validation](https://github.com/Elwinmage/ha-reeftank-component/actions/workflows/hass_and_hacs.yml/badge.svg)](https://github.com/Elwinmage/ha-reeftank-component/actions/workflows/hass_and_hacs.yml)
[![Coverage](https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/badges/coverage.svg)](https://app.codecov.io/gh/Elwinmage/ha-reeftank-component)
[![GH-last-commit](https://img.shields.io/github/last-commit/Elwinmage/ha-reeftank-component.svg?style=flat-square)](https://github.com/Elwinmage/ha-reeftank-component/commits/main)
[![GitHub Clones](https://img.shields.io/badge/dynamic/json?color=success&label=Clone&query=count&url=https://gist.githubusercontent.com/Elwinmage/5432d90f7ee0c30506438c42030dd887/raw/clone.json&logo=github)](https://github.com/MShawon/github-clone-count-badge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![GH-code-size](https://img.shields.io/github/languages/code-size/Elwinmage/ha-reeftank-component.svg?color=red&style=flat-square)](https://github.com/Elwinmage/ha-reeftank-component)
[![BuyMeCoffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://paypal.me/Elwinmage)

# Langues disponibles: [<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/README.md) <img src="https://flagicons.lipis.dev/flags/4x3/fr.svg" width="5%"/> [<img src="https://flagicons.lipis.dev/flags/4x3/de.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/de/README.de.md) [<img src="https://flagicons.lipis.dev/flags/4x3/es.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/es/README.es.md) [<img src="https://flagicons.lipis.dev/flags/4x3/it.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/it/README.it.md) [<img src="https://flagicons.lipis.dev/flags/4x3/nl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/nl/README.nl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pl/README.pl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pt.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pt/README.pt.md)

Intégration Home Assistant derrière la **carte aquarium** de [ha-reef-card](https://github.com/Elwinmage/ha-reef-card) : une image vivante de votre bac, éclairée par vos vraies lampes, peuplée de poissons et de coraux animés, et portant vos appareils et vos entités.

Elle stocke les aquariums, leurs images et leur population, enregistre les nourrissages et tient le catalogue d'espèces à jour. Rien de propre à une marque : elle fonctionne avec Red Sea, Aqua Medic ou tout autre matériel connu de Home Assistant.

<p align="center">
  <img src="../../doc/img/preview.webp" width="80%" alt="La carte aquarium"/>
</p>

<!-- ecosystem:start -->

## Projets liés

Les projets ReefTech s'articulent entre eux : les intégrations font entrer votre matériel dans Home Assistant, la carte l'affiche et le pilote, et le secours le maintient en marche pendant une coupure. Chacun fonctionne aussi seul.

<table>
  <tr>
    <th width="100px"></th>
    <th>Projet</th>
    <th>Rôle</th>
    <th>Fonctionne avec</th>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/main/icon.png" width="64" alt="ha-reefbeat-component" /></td>
    <td>🐠<br /><a href="https://github.com/Elwinmage/ha-reefbeat-component"><b>ha-reefbeat-component</b></a></td>
    <td>Appareils Red Sea ReefBeat, pilotés en local sans cloud : ReefATO+, ReefControl, ReefControl-Power, ReefDose, ReefLed, ReefMat, ReefRun et ReefWave.<br />blueprint d'alertes pour les modes anormaux, les calibrations et les batteries faibles. <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/refs/heads/main/blueprints/automation/redsea_alerts.en.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a></td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-aquamedic-component/main/icon.png" width="64" alt="ha-aquamedic-component" /></td>
    <td>🌊<br /><a href="https://github.com/Elwinmage/ha-aquamedic-component"><b>ha-aquamedic-component</b></a></td>
    <td>Pompes Aqua Medic via l'API cloud Gizwits : brasseurs EcoDrift et SmartDrift, pompes DC Runner de remontée et d'écumeur.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-maintenance-component/main/icon.png" width="64" alt="ha-reef-maintenance-component" /></td>
    <td>🐙<br /><a href="https://github.com/Elwinmage/ha-reef-maintenance-component"><b>ha-reef-maintenance-component</b></a></td>
    <td>Suivi du nettoyage et de l'usure du matériel que Home Assistant ne peut pas interroger : pompes de brassage, pompes de remontée, écumeurs, réacteurs, tout ce que vous entretenez à la main.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-card/main/icon.png" width="64" alt="ha-reef-card" /></td>
    <td>🪸<br /><a href="https://github.com/Elwinmage/ha-reef-card"><b>ha-reef-card</b></a></td>
    <td>Vue graphique interactive de chaque appareil sur votre tableau de bord, et seul moyen d'éditer les programmes avancés. Lit les trois intégrations ci-dessus via le contrat <code>reef_role</code> commun, sans configuration côté carte. Dessine aussi les flux d'énergie de reefbeatEnergyBackup. Sa carte aquarium donne vie à votre bac avec ha-reeftank-component.</td>
    <td>les trois intégrations, et ha-reeftank-component pour l'aquarium</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/icon.png" width="64" alt="ha-reeftank-component" /></td>
    <td>🐟<br /><b>ha-reeftank-component</b><br /><i>(ce dépôt)</i></td>
    <td>Une image vivante de votre bac sur le tableau de bord : votre photo, éclairée par vos vraies lampes, avec des poissons et des coraux animés, et vos appareils et entités dessus. Stocke les aquariums et leur population, enregistre les nourrissages.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reeftank-catalog/main/icon.png" width="64" alt="reeftank-catalog" /></td>
    <td>🐡<br /><a href="https://github.com/Elwinmage/reeftank-catalog"><b>reeftank-catalog</b></a></td>
    <td>Poissons, coraux et textures de la carte aquarium, téléchargés et tenus à jour par ha-reeftank-component.</td>
    <td>ha-reeftank-component</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-blueprints/main/icon.png" width="64" alt="ha-reef-blueprints" /></td>
    <td>🐬<br /><a href="https://github.com/Elwinmage/ha-reef-blueprints"><b>ha-reef-blueprints</b></a></td>
    <td>Blueprints de notification communs à tout l'écosystème : entretiens en retard trouvés via le contrat <code>reef_role</code>, et appareils devenus injoignables. Huit langues.</td>
    <td>les trois intégrations</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reefbeatEnergyBackup/main/icon.png" width="64" alt="reefbeatEnergyBackup" /></td>
    <td>⚡<br /><a href="https://github.com/Elwinmage/reefbeatEnergyBackup"><b>reefbeatEnergyBackup</b></a></td>
    <td>Secours sur batterie en cas de coupure. Pack 24V LiFePO₄ piloté par un Raspberry Pi, avec dégradation progressive de la vitesse des pompes selon l'état de charge.</td>
    <td>seul, ou avec ha-reefbeat-component et ha-reef-card</td>
  </tr>
</table>

L'ensemble est documenté sur la [page du projet ReefTech](https://elwinmage.github.io/reeftank/).

<!-- ecosystem:end -->

## Fonctionnalités

- **Votre photo, vivante** : détourez l'eau sur une photo de votre bac, la carte l'anime
- **La vraie lumière** : l'eau prend la couleur et l'intensité de vos lampes (ReefLED ou n'importe quelle `light`), assombrie la nuit mais toujours lisible
- **Poissons et coraux** du [catalogue ReefTank](https://github.com/Elwinmage/reeftank-catalog) : bancs, nageurs de pleine eau, poissons de sable, gobies qui sortent la tête de leur terrier, coraux qui ondulent avec les pompes
- **Profondeur** : les poissons passent derrière les roches détourées et se posent sur le sable la nuit
- **Bac dessiné** : pas de belle photo de l'eau ? Dessinez-la (eau, sable, textures de roche) en gardant le reste de la photo
- **Appareils et entités** posés sur l'image, cliquables ; zones qui ouvrent une autre image (la décante dans le meuble)
- **Nourrissage** : nourrisseurs, raccourcis Red Sea ou un service enregistrent chaque nourrissage ; les poissons se ruent vers le point de nourrissage
- **Inventaire** : nombre de poissons et de coraux en capteurs, avec leur historique

## Installation

### Installation directe

Cliquez ici pour ouvrir le dépôt directement dans HACS puis cliquez sur « Télécharger » : [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Elwinmage&repository=ha-reeftank-component&category=integration)

### Recherche dans HACS

Ou ajoutez `https://github.com/Elwinmage/ha-reeftank-component` en dépôt personnalisé (Intégration) et cherchez « ReefTank ».

Redémarrez Home Assistant, puis ajoutez l'intégration (une seule entrée, rien à configurer) : [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)

La carte aquarium elle-même est fournie par [ha-reef-card](https://github.com/Elwinmage/ha-reef-card), à installer aussi.

## Premiers pas

1. Ajoutez une **Reef Aquarium Card** à un tableau de bord (`custom:reef-aquarium-card`).
2. Dans son éditeur, créez un aquarium (**Nouvel aquarium**), puis **Éditer la scène**.
3. **Vues** : envoyez une photo de votre bac, détourez l'eau, tracez la ligne de sable et les roches.
4. **Appareils** et **Lumière et brassage** : posez vos appareils et entités sur l'image, placez vos lampes.
5. **Population** : ajoutez vos poissons et coraux, puis enregistrez.

La configuration de la carte ne contient que l'identifiant de l'aquarium ; tout le reste est stocké par l'intégration :

```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```

## L'éditeur de scène

Une fenêtre plein écran, ouverte depuis l'éditeur de la carte, en six onglets :

| Onglet | Ce qu'on y fait |
|---|---|
| **Aquarium** | Nom, dimensions, l'aquarium du cloud correspondant, lumière sous laquelle les photos ont été prises, niveau de rendu |
| **Vues** | Les images ; pour chaque eau : contour, ligne de sable (avant et arrière), roches et leur profondeur, zones cliquables, fond dessiné et ses textures |
| **Appareils** | Vos appareils et entités par étage et par pièce, glissés sur l'image |
| **Lumière et brassage** | Les lampes qui éclairent chaque eau et leur position ; les pompes qui font bouger l'eau |
| **Population** | Poissons (espèce, nombre, taille, abri) et coraux (espèce, taille, couleurs, position) |
| **Nourrissage** | Les entités qui enregistrent un nourrissage, et où tombe la nourriture |

## Niveaux de rendu

Chaque aquarium s'affiche à l'un de trois niveaux ; une carte peut l'abaisser, par exemple sur une tablette murale lente :

| Niveau | Affiche |
|---|---|
| **Statique** (`static`) | image, appareils et entités |
| **Lumière** (`light`) | plus la couleur des lampes |
| **Complet** (`full`) | plus poissons et coraux |

Une photo du local technique avec ses appareils en direct est un très bon aquarium `static`.

## Entités

Chaque aquarium est un appareil avec :

| Entité | État |
|---|---|
| `sensor.<aquarium>_fish` | Nombre de poissons, par espèce dans les attributs |
| `sensor.<aquarium>_corals` | Nombre de coraux, par espèce dans les attributs |
| `event.<aquarium>_feeding` | Dernier nourrissage, avec son type (nourrisseur, raccourci, manuel) et sa source |
| `sensor.<aquarium>_feedings_today` | Nourrissages depuis minuit |

Et l'appareil *ReefTank catalog* :

| Entité | État |
|---|---|
| `update.reeftank_catalog` | Version du catalogue installée et dernière publiée |
| `button.reeftank_catalog_check_for_updates` | Vérifie tout de suite si une nouvelle version existe |

## Services

| Service | Effet |
|---|---|
| `reeftank.feed` | Enregistre un nourrissage (nourrisseurs inconnus de Home Assistant, scripts) |
| `reeftank.livestock_add` | Ajoute des animaux à l'inventaire |
| `reeftank.livestock_remove` | Retire des animaux (pertes, cessions) |

`aquarium` est le nom, l'identifiant ou l'identifiant d'appareil de l'aquarium.

```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```

## Catalogue d'espèces

Poissons, coraux et textures viennent du [catalogue ReefTank](https://github.com/Elwinmage/reeftank-catalog), téléchargé au premier démarrage (github.com doit être joignable une fois), puis tenu à jour :

- une nouvelle version s'installe automatiquement ; *Paramètres → Appareils et services → ReefTank → Configurer* le désactive ;
- `button.reeftank_catalog_check_for_updates` vérifie tout de suite au lieu d'attendre la prochaine vérification (toutes les 12 heures) ;
- seul ce qui a changé est téléchargé, et une mise à jour interrompue laisse le catalogue précédent en place.

Vos propres espèces vont dans `<config>/reeftank/catalog/` (même organisation que le catalogue) : elles apparaissent dans l'éditeur sans redémarrer.

## Référence technique

Modèle de données, API WebSocket, chaîne de rendu, comportement des poissons, format des sprites et mises à jour du catalogue : [référence technique](../../doc/en/technical.md) (en anglais).

## Développement

Les tests couvrent entièrement l'intégration et la CI y veille. `scripts/gen_readme.py` régénère cette page et ses sept traductions : c'est lui qu'il faut modifier, pas les fichiers générés.

```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```
