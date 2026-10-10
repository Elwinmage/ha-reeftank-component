# ReefTank 🐟
> Part of the [**ReefTech Project Ecosystem**](https://elwinmage.github.io/reeftank/)
<p align="center">
  <img src="icon.png"  width="50%"/>
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

# Supported Languages: <img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="5%"/> [<img src="https://flagicons.lipis.dev/flags/4x3/fr.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/fr/README.fr.md) [<img src="https://flagicons.lipis.dev/flags/4x3/de.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/de/README.de.md) [<img src="https://flagicons.lipis.dev/flags/4x3/es.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/es/README.es.md) [<img src="https://flagicons.lipis.dev/flags/4x3/it.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/it/README.it.md) [<img src="https://flagicons.lipis.dev/flags/4x3/nl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/nl/README.nl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pl/README.pl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pt.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pt/README.pt.md)

Home Assistant integration behind the **aquarium card** of [ha-reef-card](https://github.com/Elwinmage/ha-reef-card): a living picture of your tank, lit by your real lamps, populated with animated fish and corals, and carrying your devices and entities.

It stores the aquariums, their pictures and their livestock, records the feedings, and keeps the species catalog up to date. Nothing vendor-specific: it works with Red Sea, Aqua Medic or any other equipment Home Assistant knows.

<p align="center">
  <img src="doc/img/preview.webp" width="80%" alt="The aquarium card"/>
</p>

<!-- ecosystem:start -->

## Related projects

The ReefTech projects fit together: the integrations bring your equipment into Home Assistant, the card displays and drives it, and the backup keeps it running through an outage. Each one also works on its own.

<table>
  <tr>
    <th width="100px"></th>
    <th>Project</th>
    <th>What it does</th>
    <th>Works with</th>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/main/icon.png" width="64" alt="ha-reefbeat-component" /></td>
    <td>🐠<br /><a href="https://github.com/Elwinmage/ha-reefbeat-component"><b>ha-reefbeat-component</b></a></td>
    <td>Red Sea ReefBeat devices, controlled locally with no cloud: ReefATO+, ReefControl, ReefControl-Power, ReefDose, ReefLed, ReefMat, ReefRun and ReefWave.<br />alert blueprint for abnormal modes, calibrations and low battery. <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/refs/heads/main/blueprints/automation/redsea_alerts.en.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a></td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-aquamedic-component/main/icon.png" width="64" alt="ha-aquamedic-component" /></td>
    <td>🌊<br /><a href="https://github.com/Elwinmage/ha-aquamedic-component"><b>ha-aquamedic-component</b></a></td>
    <td>Aqua Medic pumps through the Gizwits cloud API: EcoDrift and SmartDrift wavemakers, DC Runner return and skimmer pumps.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-maintenance-component/main/icon.png" width="64" alt="ha-reef-maintenance-component" /></td>
    <td>🐙<br /><a href="https://github.com/Elwinmage/ha-reef-maintenance-component"><b>ha-reef-maintenance-component</b></a></td>
    <td>Cleaning and wear tracking for the equipment Home Assistant cannot talk to: flow pumps, return pumps, skimmers, media reactors, anything you service by hand.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-card/main/icon.png" width="64" alt="ha-reef-card" /></td>
    <td>🪸<br /><a href="https://github.com/Elwinmage/ha-reef-card"><b>ha-reef-card</b></a></td>
    <td>Interactive graphical view of each device on your dashboard, and the only way to edit advanced schedules. Reads the three integrations above through the shared <code>reef_role</code> contract, with no card-side configuration. Also draws the power flows of reefbeatEnergyBackup. Its aquarium card brings your tank to life with ha-reeftank-component.</td>
    <td>all three integrations, and ha-reeftank-component for the aquarium</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/icon.png" width="64" alt="ha-reeftank-component" /></td>
    <td>🐟<br /><b>ha-reeftank-component</b><br /><i>(this repository)</i></td>
    <td>A living picture of your tank on the dashboard: your photo, lit by your real lamps, with animated fish and corals, and your devices and entities on it. Stores the aquariums and their livestock, records the feedings.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reeftank-catalog/main/icon.png" width="64" alt="reeftank-catalog" /></td>
    <td>🐡<br /><a href="https://github.com/Elwinmage/reeftank-catalog"><b>reeftank-catalog</b></a></td>
    <td>Fish, corals and textures of the aquarium card, downloaded and kept up to date by ha-reeftank-component.</td>
    <td>ha-reeftank-component</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-blueprints/main/icon.png" width="64" alt="ha-reef-blueprints" /></td>
    <td>🐬<br /><a href="https://github.com/Elwinmage/ha-reef-blueprints"><b>ha-reef-blueprints</b></a></td>
    <td>Notification blueprints shared by the whole ecosystem: overdue maintenance found through the <code>reef_role</code> contract, and devices that went unreachable. Eight languages.</td>
    <td>all three integrations</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reefbeatEnergyBackup/main/icon.png" width="64" alt="reefbeatEnergyBackup" /></td>
    <td>⚡<br /><a href="https://github.com/Elwinmage/reefbeatEnergyBackup"><b>reefbeatEnergyBackup</b></a></td>
    <td>Battery backup for power outages. A 24V LiFePO₄ pack driven by a Raspberry Pi, with pump speed degraded progressively according to the state of charge.</td>
    <td>standalone, or alongside ha-reefbeat-component and ha-reef-card</td>
  </tr>
</table>

All of them are documented together on the [ReefTech project page](https://elwinmage.github.io/reeftank/).

<!-- ecosystem:end -->

## Features

- **Your photo, alive**: outline the water on a picture of your tank, the card animates it
- **Real light**: the water takes the colour and the intensity of your lamps (ReefLED or any `light`), dimmed at night but still readable
- **Fish and corals** from the [ReefTank catalog](https://github.com/Elwinmage/reeftank-catalog): shoals, open-water swimmers, sand dwellers, gobies peeking out of their burrow, corals swaying with the pumps
- **Depth**: fish swim behind the rocks you outlined, and rest on the sand at night
- **Drawn tank**: no nice picture of the water? Draw it (water, sand, rock textures) and keep the rest of the photo
- **Devices and entities** dropped on the picture, clickable; zones that open another picture (the sump in the cabinet)
- **Feeding**: feeders, Red Sea shortcuts or a service record each feeding; the fish rush to the feeding point
- **Inventory**: fish and coral counts as sensors, with their history

## Installation

### Direct installation

Click here to open the repository directly in HACS and click "Download": [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Elwinmage&repository=ha-reeftank-component&category=integration)

### Search in HACS

Or add `https://github.com/Elwinmage/ha-reeftank-component` as a custom repository (Integration) and search for "ReefTank".

Restart Home Assistant, then add the integration (one entry, nothing to configure): [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)

The aquarium card itself comes with [ha-reef-card](https://github.com/Elwinmage/ha-reef-card), to install as well.

## Getting started

1. Add a **Reef Aquarium Card** to a dashboard (`custom:reef-aquarium-card`).
2. In its editor, create an aquarium (**New aquarium**), then **Edit the scene**.
3. **Views**: upload a photo of your tank, outline the water, trace the sand line and the rocks.
4. **Devices** and **Light & flow**: drop your devices and entities on the picture, place your lamps.
5. **Livestock**: add your fish and corals, then save.

The card configuration only holds the aquarium id; everything else is stored by the integration:

```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```

## The scene editor

A full-screen dialog, opened from the card editor, with six tabs:

| Tab | What you do there |
|---|---|
| **Aquarium** | Name, dimensions, the matching cloud aquarium, light the photos were taken under, render level |
| **Views** | Pictures; for each water: outline, sand line (front and back), rocks with their depth, clickable zones, drawn background and its textures |
| **Devices** | Your devices and entities by floor and area, dragged onto the picture |
| **Light & flow** | Lamps lighting each water and their position; pumps that make the water move |
| **Livestock** | Fish (species, count, size, home) and corals (species, size, colours, position) |
| **Feeding** | Entities that record a feeding, and where the food falls |

## Render levels

Each aquarium renders at one of three levels; a card can lower it, e.g. on a slow wall tablet:

| Level | Shows |
|---|---|
| **Static** (`static`) | picture, devices and entities |
| **Light** (`light`) | plus the colour of the lamps |
| **Full** (`full`) | plus fish and corals |

A picture of the technical room with live devices on it is a perfectly good `static` aquarium.

## Entities

Each aquarium is a device with:

| Entity | State |
|---|---|
| `sensor.<aquarium>_fish` | Number of fish, per species in the attributes |
| `sensor.<aquarium>_corals` | Number of corals, per species in the attributes |
| `event.<aquarium>_feeding` | Last feeding, with its kind (feeder, shortcut, manual) and source |
| `sensor.<aquarium>_feedings_today` | Feedings since midnight |

And the *ReefTank catalog* device:

| Entity | State |
|---|---|
| `update.reeftank_catalog` | Installed and latest catalog release |
| `button.reeftank_catalog_check_for_updates` | Checks for a new release right away |

## Services

| Service | Effect |
|---|---|
| `reeftank.feed` | Records a feeding (feeders unknown to Home Assistant, scripts) |
| `reeftank.livestock_add` | Adds animals to the inventory |
| `reeftank.livestock_remove` | Removes animals (losses, rehoming) |

`aquarium` is the aquarium's name, id or device id.

```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```

## Species catalog

Fish, corals and textures come from the [ReefTank catalog](https://github.com/Elwinmage/reeftank-catalog), downloaded on the first start (github.com must be reachable once), then kept up to date:

- a new release is installed automatically; *Settings → Devices & services → ReefTank → Configure* turns this off;
- `button.reeftank_catalog_check_for_updates` checks right away instead of waiting for the next check (every 12 hours);
- only what changed is downloaded, and an interrupted update leaves the previous catalog in place.

Your own species go in `<config>/reeftank/catalog/` (same layout as the catalog): they appear in the editor without restarting.

## Technical reference

Data model, WebSocket API, rendering pipeline, fish behaviour, sprite format and catalog updates: [technical reference](doc/en/technical.md) (in English).

## Development

The test suite covers the integration fully and CI keeps it that way. `scripts/gen_readme.py` regenerates this page and its seven translations: edit it, not the generated files.

```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```
