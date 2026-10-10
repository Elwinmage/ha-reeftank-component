# ReefTank 🐟
> Teil des [**ReefTech-Projekt-Ökosystems**](https://elwinmage.github.io/reeftank/)
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

# Unterstützte Sprachen: [<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/README.md) [<img src="https://flagicons.lipis.dev/flags/4x3/fr.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/fr/README.fr.md) <img src="https://flagicons.lipis.dev/flags/4x3/de.svg" width="5%"/> [<img src="https://flagicons.lipis.dev/flags/4x3/es.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/es/README.es.md) [<img src="https://flagicons.lipis.dev/flags/4x3/it.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/it/README.it.md) [<img src="https://flagicons.lipis.dev/flags/4x3/nl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/nl/README.nl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pl/README.pl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pt.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pt/README.pt.md)

Home-Assistant-Integration hinter der **Aquariumkarte** von [ha-reef-card](https://github.com/Elwinmage/ha-reef-card): ein lebendiges Bild Ihres Beckens, beleuchtet von Ihren echten Lampen, bevölkert von animierten Fischen und Korallen, mit Ihren Geräten und Entitäten darauf.

Sie speichert die Aquarien, ihre Bilder und ihren Besatz, protokolliert die Fütterungen und hält den Artenkatalog aktuell. Nichts Herstellerspezifisches: sie funktioniert mit Red Sea, Aqua Medic oder jedem anderen Gerät, das Home Assistant kennt.

<p align="center">
  <img src="../../doc/img/preview.webp" width="80%" alt="Die Aquariumkarte"/>
</p>

<!-- ecosystem:start -->

## Verwandte Projekte

Die ReefTech-Projekte greifen ineinander: die Integrationen bringen Ihre Geräte in Home Assistant, die Karte zeigt und steuert sie, und das Backup hält sie bei einem Stromausfall am Laufen. Jedes funktioniert auch für sich allein.

<table>
  <tr>
    <th width="100px"></th>
    <th>Projekt</th>
    <th>Funktion</th>
    <th>Arbeitet mit</th>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/main/icon.png" width="64" alt="ha-reefbeat-component" /></td>
    <td>🐠<br /><a href="https://github.com/Elwinmage/ha-reefbeat-component"><b>ha-reefbeat-component</b></a></td>
    <td>Red Sea ReefBeat-Geräte, lokal gesteuert ohne Cloud: ReefATO+, ReefControl, ReefControl-Power, ReefDose, ReefLed, ReefMat, ReefRun und ReefWave.<br />Alarm-Blueprint für abweichende Modi, Kalibrierungen und niedrigen Akkustand. <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/refs/heads/main/blueprints/automation/redsea_alerts.en.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a></td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-aquamedic-component/main/icon.png" width="64" alt="ha-aquamedic-component" /></td>
    <td>🌊<br /><a href="https://github.com/Elwinmage/ha-aquamedic-component"><b>ha-aquamedic-component</b></a></td>
    <td>Aqua Medic-Pumpen über die Gizwits-Cloud-API: EcoDrift- und SmartDrift-Strömungspumpen, DC Runner Rückförder- und Abschäumerpumpen.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-maintenance-component/main/icon.png" width="64" alt="ha-reef-maintenance-component" /></td>
    <td>🐙<br /><a href="https://github.com/Elwinmage/ha-reef-maintenance-component"><b>ha-reef-maintenance-component</b></a></td>
    <td>Reinigungs- und Verschleißverfolgung für Geräte, die Home Assistant nicht erreicht: Strömungspumpen, Rückförderpumpen, Abschäumer, Reaktoren, alles was von Hand gewartet wird.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-card/main/icon.png" width="64" alt="ha-reef-card" /></td>
    <td>🪸<br /><a href="https://github.com/Elwinmage/ha-reef-card"><b>ha-reef-card</b></a></td>
    <td>Interaktive grafische Ansicht jedes Geräts auf Ihrem Dashboard und der einzige Weg, erweiterte Zeitpläne zu bearbeiten. Liest die drei Integrationen über den gemeinsamen <code>reef_role</code>-Vertrag, ohne Konfiguration auf Kartenseite. Zeichnet außerdem die Energieflüsse von reefbeatEnergyBackup. Ihre Aquariumkarte erweckt Ihr Becken mit ha-reeftank-component zum Leben.</td>
    <td>alle drei Integrationen und ha-reeftank-component für das Aquarium</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/icon.png" width="64" alt="ha-reeftank-component" /></td>
    <td>🐟<br /><b>ha-reeftank-component</b><br /><i>(dieses Repository)</i></td>
    <td>Ein lebendiges Bild Ihres Beckens auf dem Dashboard: Ihr Foto, beleuchtet von Ihren echten Lampen, mit animierten Fischen und Korallen und Ihren Geräten und Entitäten darauf. Speichert die Aquarien und ihren Besatz, protokolliert die Fütterungen.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reeftank-catalog/main/icon.png" width="64" alt="reeftank-catalog" /></td>
    <td>🐡<br /><a href="https://github.com/Elwinmage/reeftank-catalog"><b>reeftank-catalog</b></a></td>
    <td>Fische, Korallen und Texturen der Aquariumkarte, von ha-reeftank-component heruntergeladen und aktuell gehalten.</td>
    <td>ha-reeftank-component</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-blueprints/main/icon.png" width="64" alt="ha-reef-blueprints" /></td>
    <td>🐬<br /><a href="https://github.com/Elwinmage/ha-reef-blueprints"><b>ha-reef-blueprints</b></a></td>
    <td>Benachrichtigungs-Blueprints für das gesamte Ökosystem: überfällige Wartungen, über den <code>reef_role</code>-Vertrag gefunden, und nicht mehr erreichbare Geräte. Acht Sprachen.</td>
    <td>alle drei Integrationen</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reefbeatEnergyBackup/main/icon.png" width="64" alt="reefbeatEnergyBackup" /></td>
    <td>⚡<br /><a href="https://github.com/Elwinmage/reefbeatEnergyBackup"><b>reefbeatEnergyBackup</b></a></td>
    <td>Batterie-Backup bei Stromausfall. Ein 24V LiFePO₄-Pack, gesteuert von einem Raspberry Pi, mit schrittweiser Reduzierung der Pumpendrehzahl je nach Ladezustand.</td>
    <td>eigenständig oder zusammen mit ha-reefbeat-component und ha-reef-card</td>
  </tr>
</table>

Alle zusammen sind auf der [ReefTech-Projektseite](https://elwinmage.github.io/reeftank/) dokumentiert.

<!-- ecosystem:end -->

## Funktionen

- **Ihr Foto, lebendig**: Wasser auf einem Foto Ihres Beckens umranden, die Karte animiert es
- **Echtes Licht**: das Wasser nimmt Farbe und Intensität Ihrer Lampen an (ReefLED oder jede `light`), nachts abgedunkelt, aber gut erkennbar
- **Fische und Korallen** aus dem [ReefTank-Katalog](https://github.com/Elwinmage/reeftank-catalog): Schwärme, Freiwasserschwimmer, Bodenbewohner, Grundeln, die aus ihrer Höhle schauen, Korallen, die sich mit den Pumpen wiegen
- **Tiefe**: Fische schwimmen hinter den umrandeten Steinen und ruhen nachts auf dem Sand
- **Gezeichnetes Becken**: kein schönes Foto vom Wasser? Zeichnen Sie es (Wasser, Sand, Gesteinstexturen) und behalten Sie den Rest des Fotos
- **Geräte und Entitäten** auf dem Bild, anklickbar; Zonen, die ein anderes Bild öffnen (das Technikbecken im Unterschrank)
- **Fütterung**: Futterautomaten, Red-Sea-Kurzbefehle oder ein Dienst protokollieren jede Fütterung; die Fische eilen zur Futterstelle
- **Bestand**: Anzahl der Fische und Korallen als Sensoren, mit Verlauf

## Installation

### Direkte Installation

Hier klicken, um das Repository direkt in HACS zu öffnen, dann auf „Herunterladen“ klicken: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Elwinmage&repository=ha-reeftank-component&category=integration)

### Suche in HACS

Oder `https://github.com/Elwinmage/ha-reeftank-component` als benutzerdefiniertes Repository (Integration) hinzufügen und nach „ReefTank“ suchen.

Home Assistant neu starten, dann die Integration hinzufügen (ein Eintrag, nichts zu konfigurieren): [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)

Die Aquariumkarte selbst kommt mit [ha-reef-card](https://github.com/Elwinmage/ha-reef-card), ebenfalls zu installieren.

## Erste Schritte

1. Fügen Sie einem Dashboard eine **Reef Aquarium Card** hinzu (`custom:reef-aquarium-card`).
2. Legen Sie in ihrem Editor ein Aquarium an (**Neues Aquarium**), dann **Szene bearbeiten**.
3. **Ansichten**: ein Foto Ihres Beckens hochladen, das Wasser umranden, Sandlinie und Steine nachzeichnen.
4. **Geräte** und **Licht & Strömung**: Geräte und Entitäten auf das Bild ziehen, Lampen platzieren.
5. **Besatz**: Fische und Korallen hinzufügen, dann speichern.

Die Kartenkonfiguration enthält nur die Aquarium-ID; alles andere speichert die Integration:

```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```

## Der Szeneneditor

Ein Vollbilddialog, aus dem Karteneditor geöffnet, mit sechs Reitern:

| Reiter | Was man dort macht |
|---|---|
| **Aquarium** | Name, Maße, das passende Cloud-Aquarium, Licht, unter dem die Fotos entstanden, Darstellungsstufe |
| **Ansichten** | Bilder; für jedes Wasser: Umriss, Sandlinie (vorne und hinten), Steine mit ihrer Tiefe, anklickbare Zonen, gezeichneter Hintergrund und seine Texturen |
| **Geräte** | Ihre Geräte und Entitäten nach Etage und Bereich, auf das Bild gezogen |
| **Licht & Strömung** | Lampen, die jedes Wasser beleuchten, und ihre Position; Pumpen, die das Wasser bewegen |
| **Besatz** | Fische (Art, Anzahl, Größe, Revier) und Korallen (Art, Größe, Farben, Position) |
| **Fütterung** | Entitäten, die eine Fütterung protokollieren, und wo das Futter fällt |

## Darstellungsstufen

Jedes Aquarium wird in einer von drei Stufen dargestellt; eine Karte kann sie senken, z. B. auf einem langsamen Wandtablet:

| Stufe | Zeigt |
|---|---|
| **Statisch** (`static`) | Bild, Geräte und Entitäten |
| **Licht** (`light`) | plus die Farbe der Lampen |
| **Voll** (`full`) | plus Fische und Korallen |

Ein Foto des Technikraums mit live angezeigten Geräten ist ein vollwertiges `static`-Aquarium.

## Entitäten

Jedes Aquarium ist ein Gerät mit:

| Entität | Zustand |
|---|---|
| `sensor.<aquarium>_fish` | Anzahl der Fische, pro Art in den Attributen |
| `sensor.<aquarium>_corals` | Anzahl der Korallen, pro Art in den Attributen |
| `event.<aquarium>_feeding` | Letzte Fütterung, mit Art (Futterautomat, Kurzbefehl, manuell) und Quelle |
| `sensor.<aquarium>_feedings_today` | Fütterungen seit Mitternacht |

Und das Gerät *ReefTank catalog*:

| Entität | Zustand |
|---|---|
| `update.reeftank_catalog` | Installierte und neueste Katalogversion |
| `button.reeftank_catalog_check_for_updates` | Prüft sofort, ob eine neue Version vorliegt |

## Dienste

| Dienst | Wirkung |
|---|---|
| `reeftank.feed` | Protokolliert eine Fütterung (Futterautomaten außerhalb von Home Assistant, Skripte) |
| `reeftank.livestock_add` | Fügt dem Bestand Tiere hinzu |
| `reeftank.livestock_remove` | Entfernt Tiere (Verluste, Abgabe) |

`aquarium` ist Name, ID oder Geräte-ID des Aquariums.

```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```

## Artenkatalog

Fische, Korallen und Texturen stammen aus dem [ReefTank-Katalog](https://github.com/Elwinmage/reeftank-catalog), beim ersten Start heruntergeladen (github.com muss einmal erreichbar sein) und dann aktuell gehalten:

- eine neue Version wird automatisch installiert; *Einstellungen → Geräte & Dienste → ReefTank → Konfigurieren* schaltet das ab;
- `button.reeftank_catalog_check_for_updates` prüft sofort, statt auf die nächste Prüfung (alle 12 Stunden) zu warten;
- nur Geändertes wird heruntergeladen, und ein abgebrochenes Update lässt den bisherigen Katalog unangetastet.

Eigene Arten gehören nach `<config>/reeftank/catalog/` (gleicher Aufbau wie der Katalog): sie erscheinen ohne Neustart im Editor.

## Technische Referenz

Datenmodell, WebSocket-API, Render-Pipeline, Fischverhalten, Sprite-Format und Katalog-Updates: [technische Referenz](../../doc/en/technical.md) (auf Englisch).

## Entwicklung

Die Tests decken die Integration vollständig ab, und die CI sorgt dafür, dass es so bleibt. `scripts/gen_readme.py` erzeugt diese Seite und ihre sieben Übersetzungen: dort ändern, nicht in den erzeugten Dateien.

```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```
