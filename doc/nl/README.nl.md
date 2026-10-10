# ReefTank 🐟
> Onderdeel van het [**ReefTech-projectecosysteem**](https://elwinmage.github.io/reeftank/)
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

# Beschikbare talen: [<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/README.md) [<img src="https://flagicons.lipis.dev/flags/4x3/fr.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/fr/README.fr.md) [<img src="https://flagicons.lipis.dev/flags/4x3/de.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/de/README.de.md) [<img src="https://flagicons.lipis.dev/flags/4x3/es.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/es/README.es.md) [<img src="https://flagicons.lipis.dev/flags/4x3/it.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/it/README.it.md) <img src="https://flagicons.lipis.dev/flags/4x3/nl.svg" width="5%"/> [<img src="https://flagicons.lipis.dev/flags/4x3/pl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pl/README.pl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pt.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pt/README.pt.md)

Home Assistant-integratie achter de **aquariumkaart** van [ha-reef-card](https://github.com/Elwinmage/ha-reef-card): een levend beeld van uw bak, verlicht door uw echte lampen, bevolkt met geanimeerde vissen en koralen, met uw apparaten en entiteiten erop.

Ze bewaart de aquaria, hun afbeeldingen en hun bezetting, legt de voederingen vast en houdt de soortencatalogus bij. Niets merkgebonden: ze werkt met Red Sea, Aqua Medic of elk ander apparaat dat Home Assistant kent.

<p align="center">
  <img src="../../doc/img/preview.webp" width="80%" alt="De aquariumkaart"/>
</p>

<!-- ecosystem:start -->

## Verwante projecten

De ReefTech-projecten grijpen in elkaar: de integraties brengen uw apparatuur in Home Assistant, de kaart toont en bedient ze, en de back-up houdt alles draaiend tijdens een stroomuitval. Elk werkt ook op zichzelf.

<table>
  <tr>
    <th width="100px"></th>
    <th>Project</th>
    <th>Rol</th>
    <th>Werkt samen met</th>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/main/icon.png" width="64" alt="ha-reefbeat-component" /></td>
    <td>🐠<br /><a href="https://github.com/Elwinmage/ha-reefbeat-component"><b>ha-reefbeat-component</b></a></td>
    <td>Red Sea ReefBeat-apparaten, lokaal aangestuurd zonder cloud: ReefATO+, ReefControl, ReefControl-Power, ReefDose, ReefLed, ReefMat, ReefRun en ReefWave.<br />blueprint met meldingen voor afwijkende modi, kalibraties en lage accu. <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/refs/heads/main/blueprints/automation/redsea_alerts.en.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a></td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-aquamedic-component/main/icon.png" width="64" alt="ha-aquamedic-component" /></td>
    <td>🌊<br /><a href="https://github.com/Elwinmage/ha-aquamedic-component"><b>ha-aquamedic-component</b></a></td>
    <td>Aqua Medic-pompen via de Gizwits-cloud-API: EcoDrift- en SmartDrift-stromingspompen, DC Runner opvoer- en afschuimerpompen.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-maintenance-component/main/icon.png" width="64" alt="ha-reef-maintenance-component" /></td>
    <td>🐙<br /><a href="https://github.com/Elwinmage/ha-reef-maintenance-component"><b>ha-reef-maintenance-component</b></a></td>
    <td>Schoonmaak- en slijtageopvolging voor apparatuur die Home Assistant niet kan uitlezen: stromingspompen, opvoerpompen, eiwitafschuimers, reactoren, alles wat u met de hand onderhoudt.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-card/main/icon.png" width="64" alt="ha-reef-card" /></td>
    <td>🪸<br /><a href="https://github.com/Elwinmage/ha-reef-card"><b>ha-reef-card</b></a></td>
    <td>Interactieve grafische weergave van elk apparaat op uw dashboard, en de enige manier om geavanceerde schema's te bewerken. Leest de drie integraties via het gedeelde <code>reef_role</code>-contract, zonder configuratie aan de kaartzijde. Tekent ook de energiestromen van reefbeatEnergyBackup. De aquariumkaart brengt uw bak tot leven met ha-reeftank-component.</td>
    <td>alle drie de integraties, en ha-reeftank-component voor het aquarium</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/icon.png" width="64" alt="ha-reeftank-component" /></td>
    <td>🐟<br /><b>ha-reeftank-component</b><br /><i>(deze repository)</i></td>
    <td>Een levend beeld van uw bak op het dashboard: uw foto, verlicht door uw echte lampen, met geanimeerde vissen en koralen, en uw apparaten en entiteiten erop. Bewaart de aquaria en hun bezetting, legt de voederingen vast.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reeftank-catalog/main/icon.png" width="64" alt="reeftank-catalog" /></td>
    <td>🐡<br /><a href="https://github.com/Elwinmage/reeftank-catalog"><b>reeftank-catalog</b></a></td>
    <td>Vissen, koralen en texturen van de aquariumkaart, gedownload en bijgehouden door ha-reeftank-component.</td>
    <td>ha-reeftank-component</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-blueprints/main/icon.png" width="64" alt="ha-reef-blueprints" /></td>
    <td>🐬<br /><a href="https://github.com/Elwinmage/ha-reef-blueprints"><b>ha-reef-blueprints</b></a></td>
    <td>Meldings-blueprints voor het hele ecosysteem: achterstallig onderhoud gevonden via het <code>reef_role</code>-contract, en apparaten die onbereikbaar zijn geworden. Acht talen.</td>
    <td>alle drie de integraties</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reefbeatEnergyBackup/main/icon.png" width="64" alt="reefbeatEnergyBackup" /></td>
    <td>⚡<br /><a href="https://github.com/Elwinmage/reefbeatEnergyBackup"><b>reefbeatEnergyBackup</b></a></td>
    <td>Accuback-up bij stroomuitval. Een 24V LiFePO₄-pakket aangestuurd door een Raspberry Pi, met de pompsnelheid die geleidelijk zakt met de laadtoestand.</td>
    <td>zelfstandig, of samen met ha-reefbeat-component en ha-reef-card</td>
  </tr>
</table>

Alles staat samen gedocumenteerd op de [ReefTech-projectpagina](https://elwinmage.github.io/reeftank/).

<!-- ecosystem:end -->

## Functies

- **Uw foto, levend**: omlijn het water op een foto van uw bak, de kaart brengt het tot leven
- **Echt licht**: het water krijgt de kleur en de sterkte van uw lampen (ReefLED of elke `light`), 's nachts gedimd maar leesbaar
- **Vissen en koralen** uit de [ReefTank-catalogus](https://github.com/Elwinmage/reeftank-catalog): scholen, openwaterzwemmers, zandbewoners, grondels die uit hun hol kijken, koralen die meewiegen met de pompen
- **Diepte**: vissen zwemmen achter de omlijnde stenen en rusten 's nachts op het zand
- **Getekende bak**: geen mooie foto van het water? Teken het (water, zand, steentexturen) en houd de rest van de foto
- **Apparaten en entiteiten** op de afbeelding, klikbaar; zones die een andere afbeelding openen (de sump in het meubel)
- **Voederen**: voederautomaten, Red Sea-snelkoppelingen of een dienst leggen elke voedering vast; de vissen haasten zich naar het voederpunt
- **Inventaris**: aantal vissen en koralen als sensoren, met hun geschiedenis

## Installatie

### Directe installatie

Klik hier om de repository direct in HACS te openen en klik op "Downloaden": [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Elwinmage&repository=ha-reeftank-component&category=integration)

### Zoeken in HACS

Of voeg `https://github.com/Elwinmage/ha-reeftank-component` toe als aangepaste repository (Integratie) en zoek naar "ReefTank".

Herstart Home Assistant en voeg de integratie toe (één item, niets in te stellen): [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)

De aquariumkaart zelf komt met [ha-reef-card](https://github.com/Elwinmage/ha-reef-card), dat u ook installeert.

## Aan de slag

1. Voeg een **Reef Aquarium Card** toe aan een dashboard (`custom:reef-aquarium-card`).
2. Maak in de editor een aquarium aan (**New aquarium**), daarna **Edit the scene**.
3. **Views**: upload een foto van uw bak, omlijn het water, trek de zandlijn en de stenen over.
4. **Devices** en **Light & flow**: zet uw apparaten en entiteiten op de afbeelding, plaats uw lampen.
5. **Livestock**: voeg uw vissen en koralen toe en sla op.

De kaartconfiguratie bevat alleen het id van het aquarium; al de rest bewaart de integratie:

```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```

## De scène-editor

Een schermvullend venster, geopend vanuit de kaarteditor, met zes tabbladen (de kaart is nog niet in het Nederlands vertaald):

| Tabblad | Wat u er doet |
|---|---|
| **Aquarium** | Naam, afmetingen, het bijbehorende cloudaquarium, licht waaronder de foto's genomen zijn, weergaveniveau |
| **Views** | De afbeeldingen; per water: omtrek, zandlijn (voor en achter), stenen met hun diepte, klikbare zones, getekende achtergrond en zijn texturen |
| **Devices** | Uw apparaten en entiteiten per verdieping en ruimte, naar de afbeelding gesleept |
| **Light & flow** | De lampen die elk water verlichten en hun positie; de pompen die het water bewegen |
| **Livestock** | Vissen (soort, aantal, grootte, thuis) en koralen (soort, grootte, kleuren, positie) |
| **Feeding** | De entiteiten die een voedering vastleggen, en waar het voer valt |

## Weergaveniveaus

Elk aquarium wordt op een van drie niveaus weergegeven; een kaart kan het verlagen, bijvoorbeeld op een trage wandtablet:

| Niveau | Toont |
|---|---|
| **Static** (`static`) | picture, devices and entities |
| **Light** (`light`) | plus the colour of the lamps |
| **Full** (`full`) | plus fish and corals |

Een foto van de technische ruimte met live apparaten erop is een prima `static`-aquarium.

## Entiteiten

Elk aquarium is een apparaat met:

| Entiteit | Status |
|---|---|
| `sensor.<aquarium>_fish` | Aantal vissen, per soort in de attributen |
| `sensor.<aquarium>_corals` | Aantal koralen, per soort in de attributen |
| `event.<aquarium>_feeding` | Laatste voedering, met soort (automaat, snelkoppeling, handmatig) en bron |
| `sensor.<aquarium>_feedings_today` | Voederingen sinds middernacht |

En het apparaat *ReefTank catalog*:

| Entiteit | Status |
|---|---|
| `update.reeftank_catalog` | Geïnstalleerde en nieuwste catalogusversie |
| `button.reeftank_catalog_check_for_updates` | Controleert meteen of er een nieuwe versie is |

## Diensten

| Dienst | Effect |
|---|---|
| `reeftank.feed` | Legt een voedering vast (automaten die Home Assistant niet kent, scripts) |
| `reeftank.livestock_add` | Voegt dieren toe aan de inventaris |
| `reeftank.livestock_remove` | Verwijdert dieren (verlies, weggegeven) |

`aquarium` is de naam, het id of het apparaat-id van het aquarium.

```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```

## Soortencatalogus

Vissen, koralen en texturen komen uit de [ReefTank-catalogus](https://github.com/Elwinmage/reeftank-catalog), gedownload bij de eerste start (github.com moet één keer bereikbaar zijn) en daarna bijgehouden:

- een nieuwe versie wordt automatisch geïnstalleerd; *Instellingen → Apparaten & diensten → ReefTank → Configureren* zet dit uit;
- `button.reeftank_catalog_check_for_updates` controleert meteen in plaats van te wachten op de volgende controle (elke 12 uur);
- alleen wat gewijzigd is wordt gedownload, en een onderbroken update laat de vorige catalogus staan.

Uw eigen soorten horen in `<config>/reeftank/catalog/` (zelfde indeling als de catalogus): ze verschijnen in de editor zonder herstart.

## Technische referentie

Datamodel, WebSocket-API, weergaveketen, visgedrag, spriteformaat en catalogusupdates: [technische referentie](../../doc/en/technical.md) (in het Engels).

## Ontwikkeling

De tests dekken de integratie volledig af en de CI bewaakt dat. `scripts/gen_readme.py` genereert deze pagina en haar zeven vertalingen: pas dat script aan, niet de gegenereerde bestanden.

```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```
