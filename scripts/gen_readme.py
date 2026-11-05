#!/usr/bin/env python3
"""Generate README.md and its seven translations from one source.

Usage, from the repository root::

    python3 scripts/gen_readme.py           # write the eight files
    python3 scripts/gen_readme.py --check   # exit 1 when one is out of date

Order matters on a first generation only: this script writes the whole file,
then reeftank/scripts/gen_ecosystem.py (run from the parent directory) inserts
the shared "Related projects" block. An existing block is carried over, so
this script can be re-run on its own afterwards.

Edit T below, never the generated files. The technical reference
(doc/en/technical.md) is hand-written, in English only, and linked from every
language.
"""

from __future__ import annotations

import sys
from pathlib import Path

OWNER = "Elwinmage"
NAME = "ha-reeftank-component"
REPO = f"https://github.com/{OWNER}/{NAME}"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{NAME}/main"
CARD = f"https://github.com/{OWNER}/ha-reef-card"
CATALOG = f"https://github.com/{OWNER}/reeftank-catalog"
SITE = "https://elwinmage.github.io/reeftank/"
TECH = "doc/en/technical.md"
PREVIEW = "doc/img/preview.webp"

# Flag, language code, and the path the flag links to. English is the root
# README; the rest live under doc/<lang>/.
LANGS = [
    ("gb", "en", "README.md"),
    ("fr", "fr", "doc/fr/README.fr.md"),
    ("de", "de", "doc/de/README.de.md"),
    ("es", "es", "doc/es/README.es.md"),
    ("it", "it", "doc/it/README.it.md"),
    ("nl", "nl", "doc/nl/README.nl.md"),
    ("pl", "pl", "doc/pl/README.pl.md"),
    ("pt", "pt", "doc/pt/README.pt.md"),
]

# Clone counter, kept in a gist by the clone.yml workflow (secret GIST_ID).
# One gist per repository: put its id here once the workflow has created it.
# Empty, the badge is simply not emitted rather than rendering broken.
CLONE_GIST_ID = "5432d90f7ee0c30506438c42030dd887"

CLONE_BADGE = (
    (
        "[![GitHub Clones](https://img.shields.io/badge/dynamic/json"
        "?color=success&label=Clone&query=count"
        f"&url=https://gist.githubusercontent.com/{OWNER}/"
        f"{CLONE_GIST_ID}/raw/clone.json&logo=github)]"
        "(https://github.com/MShawon/github-clone-count-badge)\n"
    )
    if CLONE_GIST_ID
    else ""
)

BADGES = f"""[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/hacs)
[![IoT Class](https://img.shields.io/badge/IoT%20Class-Calculated-green?style=flat-square)](https://developers.home-assistant.io/docs/architecture_index/#branding)
[![GH-release](https://img.shields.io/github/v/release/{OWNER}/{NAME}.svg?style=flat-square)]({REPO}/releases)
![Installations](https://img.shields.io/badge/dynamic/json?label=Active%20Installs&query=estimated&cacheSeconds=3600&url=https%3A%2F%2Fraw.githubusercontent.com%2F{OWNER}%2F{NAME}%2Fmain%2Fbadges%2Fstats.json&color=CE1126&logo=home-assistant)
[![Ruff Status]({REPO}/actions/workflows/main.yml/badge.svg)]({REPO}/actions/workflows/main.yml)
[![HA & HACS Validation]({REPO}/actions/workflows/hass_and_hacs.yml/badge.svg)]({REPO}/actions/workflows/hass_and_hacs.yml)
[![Coverage]({RAW}/badges/coverage.svg)](https://app.codecov.io/gh/{OWNER}/{NAME})
[![GH-last-commit](https://img.shields.io/github/last-commit/{OWNER}/{NAME}.svg?style=flat-square)]({REPO}/commits/main)
{CLONE_BADGE}[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![GH-code-size](https://img.shields.io/github/languages/code-size/{OWNER}/{NAME}.svg?color=red&style=flat-square)]({REPO})
[![BuyMeCoffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://paypal.me/{OWNER})"""

HACS_BADGE = (
    "[![Open your Home Assistant instance and open a repository inside the "
    "Home Assistant Community Store.]"
    "(https://my.home-assistant.io/badges/hacs_repository.svg)]"
    "(https://my.home-assistant.io/redirect/hacs_repository/"
    f"?owner={OWNER}&repository={NAME}&category=integration)"
)

FLOW_BADGE = (
    "[![Open your Home Assistant instance and start setting up a new "
    "integration.](https://my.home-assistant.io/badges/config_flow_start.svg)]"
    "(https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)"
)

CARD_YAML = """```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```"""

MONITORING_YAML = """```yaml
action: reeftank.monitoring_configure
data:
  aquarium: Reefer 425
  ph_entity: sensor.tank_ph
  orp_entity: sensor.tank_orp
  co2_entity: sensor.room_co2
  kh_entity: sensor.reefdose_head_2_last_measurement
  ph_calibration_entity: sensor.tank_ph_last_adjustment
  orp_calibration_entity: sensor.tank_orp_last_adjustment
```"""

SERVICE_YAML = """```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```"""

DEV_SH = """```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```"""

T: dict[str, dict[str, str]] = {
    "en": {
        "ecosystem_line": f"Part of the [**ReefTech Project Ecosystem**]({SITE})",
        "languages": "Supported Languages",
        "intro": (
            "Home Assistant integration behind the **aquarium card** of "
            f"[ha-reef-card]({CARD}): a living picture of your tank, lit by "
            "your real lamps, populated with animated fish and corals, and "
            "carrying your devices and entities."
        ),
        "intro2": (
            "It stores the aquariums, their pictures and their livestock, "
            "records the feedings, and keeps the species catalog up to date. "
            "Nothing vendor-specific: it works with Red Sea, Aqua Medic or any "
            "other equipment Home Assistant knows."
        ),
        "preview": "The aquarium card",
        "features_title": "Features",
        "f1": "**Your photo, alive**: outline the water on a picture of your tank, the card animates it",
        "f2": "**Real light**: the water takes the colour and the intensity of your lamps (ReefLED or any `light`), dimmed at night but still readable",
        "f3": "**Fish and corals** from the [ReefTank catalog]({catalog}): shoals, open-water swimmers, sand dwellers, gobies peeking out of their burrow, corals swaying with the pumps",
        "f4": "**Depth**: fish swim behind the rocks you outlined, and rest on the sand at night",
        "f5": "**Drawn tank**: no nice picture of the water? Draw it (water, sand, rock textures) and keep the rest of the photo",
        "f6": "**Devices and entities** dropped on the picture, clickable; zones that open another picture (the sump in the cabinet)",
        "f7": "**Feeding**: feeders, Red Sea shortcuts or a service record each feeding; the fish rush to the feeding point",
        "f8": "**Inventory**: fish and coral counts as sensors, with their history",
        "install_title": "Installation",
        "install_direct_title": "Direct installation",
        "install_direct_body": 'Click here to open the repository directly in HACS and click "Download":',
        "install_search_title": "Search in HACS",
        "install_search_body": 'Or add `{repo}` as a custom repository (Integration) and search for "ReefTank".',
        "install_add": "Restart Home Assistant, then add the integration (one entry, nothing to configure):",
        "install_card": "The aquarium card itself comes with [ha-reef-card]({card}), to install as well.",
        "start_title": "Getting started",
        "s1": "Add a **Reef Aquarium Card** to a dashboard (`custom:reef-aquarium-card`).",
        "s2": "In its editor, create an aquarium (**{new}**), then **{edit}**.",
        "s3": "**{views}**: upload a photo of your tank, outline the water, trace the sand line and the rocks.",
        "s4": "**{devices}** and **{lights}**: drop your devices and entities on the picture, place your lamps.",
        "s5": "**{livestock}**: add your fish and corals, then save.",
        "start_note": "The card configuration only holds the aquarium id; everything else is stored by the integration:",
        "editor_title": "The scene editor",
        "editor_body": "A full-screen dialog, opened from the card editor, with six tabs:",
        "h_tab": "Tab",
        "h_what": "What you do there",
        "w_aquarium": "Name, dimensions, the matching cloud aquarium, light the photos were taken under, render level, water darkness at night",
        "w_views": "Pictures; for each water: outline, sand line (front and back), rocks with their depth, clickable zones, drawn background and its textures",
        "w_devices": "Your devices and entities by floor and area, dragged onto the picture",
        "w_lights": "Lamps lighting each water and their position; pumps that make the water move",
        "w_livestock": "Fish (species, count, size, home) and corals (species, size, colours, position)",
        "w_feeding": "Entities that record a feeding, and where the food falls",
        "levels_title": "Render levels",
        "levels_body": "Each aquarium renders at one of three levels; a card can lower it, e.g. on a slow wall tablet:",
        "h_level": "Level",
        "h_shows": "Shows",
        "levels_note": "A picture of the technical room with live devices on it is a perfectly good `static` aquarium.",
        "m6": "KH moving too fast|Two consecutive KH tests differ by more than 0.5 dKH",
        "mon_kh": "With a KH tests entity (the last measurement of a ReefDose head, for instance), a recent test tells a real KH drop from a CO2 effect or a probe problem (`cause`) and, with the CO2, gives an estimated KH between two tests.",
        "e_kh": "KH estimated between two tests (needs a test and the CO2)",
        "mon_title": "Water monitoring",
        "mon_body": "ReefTank compares your tank with its own recent history, rather than with universal limits, and raises alarms when it leaves what is usual. pH and ORP can come from any numeric entity; a CO2 sensor in the room is optional. pH does not measure KH: these alarms tell you when to test.",
        "mon_h_alarm": "Alarm",
        "mon_h_when": "Fires when",
        "m1": "pH below its usual level|The 24 h mean is 0.1 below the median of the last 14 days. With a CO2 sensor, `cause` tells whether the CO2 of the room explains it",
        "m2": "pH swing wider than usual|The 24 h amplitude exceeds the usual one by 50 %",
        "m3": "pH day pattern disturbed|The last 4 hours stay away from the usual shape of the day",
        "m4": "ORP below its usual level|ORP, the pH effect taken out, stays 30 mV below its median for 12 hours",
        "m5": "Suspect probe|A value frozen for 12 hours, no value for 2 hours, repeated spikes, a jump, or pH and ORP no longer moving together for 2 days",
        "mon_note": "The alarms stay unknown for the first 14 days, while the tank is learned; only the suspect probe works from the start. All thresholds can be set.",
        "mon_setup": "Choose the entities once. This service also sets the thresholds:",
        "mon_cal": "With a calibration entity (the last adjustment date of the probe), a calibration needs no action: the readings around it are dropped and the history follows the new level after 24 hours. For a cleaning or a water change, turn the pause switch on: it turns off by itself after 6 hours.",
        "e_status": "Status of the monitoring, learning progress in the attributes",
        "e_ph": "24 h mean and amplitude of the pH",
        "e_orp": "ORP without the daily effect of the pH",
        "e_alarms": "The six alarms above",
        "e_pause": "Suspends the analysis",
        "sv_configure": "Chooses the monitored entities and the thresholds",
        "sv_reset": "Forgets the history to learn again (new probe)",
        "entities_title": "Entities",
        "entities_body": "Each aquarium is a device with:",
        "h_entity": "Entity",
        "h_state": "State",
        "e_fish": "Number of fish, per species in the attributes",
        "e_corals": "Number of corals, per species in the attributes",
        "e_feeding": "Last feeding, with its kind (feeder, shortcut, manual) and source",
        "e_today": "Feedings since midnight",
        "entities_catalog": "And the *ReefTank catalog* device:",
        "e_update": "Installed and latest catalog release",
        "e_button": "Checks for a new release right away",
        "services_title": "Services",
        "h_service": "Service",
        "h_effect": "Effect",
        "sv_feed": "Records a feeding (feeders unknown to Home Assistant, scripts)",
        "sv_add": "Adds animals to the inventory",
        "sv_remove": "Removes animals (losses, rehoming)",
        "services_note": "`aquarium` is the aquarium's name, id or device id.",
        "catalog_title": "Species catalog",
        "catalog_body": "Fish, corals and textures come from the [ReefTank catalog]({catalog}), downloaded on the first start (github.com must be reachable once), then kept up to date:",
        "c1": "a new release is installed automatically; *Settings → Devices & services → ReefTank → Configure* turns this off;",
        "c2": "`button.reeftank_catalog_check_for_updates` checks right away instead of waiting for the next check (every 12 hours);",
        "c3": "only what changed is downloaded, and an interrupted update leaves the previous catalog in place.",
        "catalog_own": "Your own species go in `<config>/reeftank/catalog/` (same layout as the catalog): they appear in the editor without restarting.",
        "tech_title": "Technical reference",
        "tech_body": "Data model, WebSocket API, rendering pipeline, fish behaviour, sprite format and catalog updates: [technical reference]({tech}) (in English).",
        "dev_title": "Development",
        "dev_body": "The test suite covers the integration fully and CI keeps it that way. `scripts/gen_readme.py` regenerates this page and its seven translations: edit it, not the generated files.",
    },
    "fr": {
        "ecosystem_line": f"Fait partie de l'[**écosystème ReefTech**]({SITE})",
        "languages": "Langues disponibles",
        "intro": (
            "Intégration Home Assistant derrière la **carte aquarium** de "
            f"[ha-reef-card]({CARD}) : une image vivante de votre bac, éclairée "
            "par vos vraies lampes, peuplée de poissons et de coraux animés, et "
            "portant vos appareils et vos entités."
        ),
        "intro2": (
            "Elle stocke les aquariums, leurs images et leur population, "
            "enregistre les nourrissages et tient le catalogue d'espèces à jour. "
            "Rien de propre à une marque : elle fonctionne avec Red Sea, Aqua "
            "Medic ou tout autre matériel connu de Home Assistant."
        ),
        "preview": "La carte aquarium",
        "features_title": "Fonctionnalités",
        "f1": "**Votre photo, vivante** : détourez l'eau sur une photo de votre bac, la carte l'anime",
        "f2": "**La vraie lumière** : l'eau prend la couleur et l'intensité de vos lampes (ReefLED ou n'importe quelle `light`), assombrie la nuit mais toujours lisible",
        "f3": "**Poissons et coraux** du [catalogue ReefTank]({catalog}) : bancs, nageurs de pleine eau, poissons de sable, gobies qui sortent la tête de leur terrier, coraux qui ondulent avec les pompes",
        "f4": "**Profondeur** : les poissons passent derrière les roches détourées et se posent sur le sable la nuit",
        "f5": "**Bac dessiné** : pas de belle photo de l'eau ? Dessinez-la (eau, sable, textures de roche) en gardant le reste de la photo",
        "f6": "**Appareils et entités** posés sur l'image, cliquables ; zones qui ouvrent une autre image (la décante dans le meuble)",
        "f7": "**Nourrissage** : nourrisseurs, raccourcis Red Sea ou un service enregistrent chaque nourrissage ; les poissons se ruent vers le point de nourrissage",
        "f8": "**Inventaire** : nombre de poissons et de coraux en capteurs, avec leur historique",
        "install_title": "Installation",
        "install_direct_title": "Installation directe",
        "install_direct_body": "Cliquez ici pour ouvrir le dépôt directement dans HACS puis cliquez sur « Télécharger » :",
        "install_search_title": "Recherche dans HACS",
        "install_search_body": "Ou ajoutez `{repo}` en dépôt personnalisé (Intégration) et cherchez « ReefTank ».",
        "install_add": "Redémarrez Home Assistant, puis ajoutez l'intégration (une seule entrée, rien à configurer) :",
        "install_card": "La carte aquarium elle-même est fournie par [ha-reef-card]({card}), à installer aussi.",
        "start_title": "Premiers pas",
        "s1": "Ajoutez une **Reef Aquarium Card** à un tableau de bord (`custom:reef-aquarium-card`).",
        "s2": "Dans son éditeur, créez un aquarium (**{new}**), puis **{edit}**.",
        "s3": "**{views}** : envoyez une photo de votre bac, détourez l'eau, tracez la ligne de sable et les roches.",
        "s4": "**{devices}** et **{lights}** : posez vos appareils et entités sur l'image, placez vos lampes.",
        "s5": "**{livestock}** : ajoutez vos poissons et coraux, puis enregistrez.",
        "start_note": "La configuration de la carte ne contient que l'identifiant de l'aquarium ; tout le reste est stocké par l'intégration :",
        "editor_title": "L'éditeur de scène",
        "editor_body": "Une fenêtre plein écran, ouverte depuis l'éditeur de la carte, en six onglets :",
        "h_tab": "Onglet",
        "h_what": "Ce qu'on y fait",
        "w_aquarium": "Nom, dimensions, l'aquarium du cloud correspondant, lumière sous laquelle les photos ont été prises, niveau de rendu, obscurité de l'eau la nuit",
        "w_views": "Les images ; pour chaque eau : contour, ligne de sable (avant et arrière), roches et leur profondeur, zones cliquables, fond dessiné et ses textures",
        "w_devices": "Vos appareils et entités par étage et par pièce, glissés sur l'image",
        "w_lights": "Les lampes qui éclairent chaque eau et leur position ; les pompes qui font bouger l'eau",
        "w_livestock": "Poissons (espèce, nombre, taille, abri) et coraux (espèce, taille, couleurs, position)",
        "w_feeding": "Les entités qui enregistrent un nourrissage, et où tombe la nourriture",
        "levels_title": "Niveaux de rendu",
        "levels_body": "Chaque aquarium s'affiche à l'un de trois niveaux ; une carte peut l'abaisser, par exemple sur une tablette murale lente :",
        "h_level": "Niveau",
        "h_shows": "Affiche",
        "levels_note": "Une photo du local technique avec ses appareils en direct est un très bon aquarium `static`.",
        "m6": "KH qui varie trop vite|Deux tests KH consécutifs diffèrent de plus de 0,5 dKH",
        "mon_kh": "Avec une entité de tests KH (la dernière mesure d'une tête ReefDose, par exemple), un test récent distingue une vraie baisse du KH d'un effet du CO2 ou d'un problème de sonde (`cause`) et, avec le CO2, donne un KH estimé entre deux tests.",
        "e_kh": "KH estimé entre deux tests (demande un test et le CO2)",
        "mon_title": "Surveillance de l'eau",
        "mon_body": "ReefTank compare votre bac à son propre historique récent plutôt qu'à des limites universelles, et déclenche des alarmes quand il s'en écarte. Le pH et l'ORP peuvent venir de n'importe quelle entité numérique ; un capteur de CO2 dans la pièce est facultatif. Le pH ne mesure pas le KH : ces alarmes vous disent quand faire un test.",
        "mon_h_alarm": "Alarme",
        "mon_h_when": "Se déclenche quand",
        "m1": "pH sous son niveau habituel|La moyenne 24 h est inférieure de 0,1 à la médiane des 14 derniers jours. Avec un capteur de CO2, `cause` indique si le CO2 de la pièce l'explique",
        "m2": "Amplitude du pH anormale|L'amplitude 24 h dépasse l'habituelle de 50 %",
        "m3": "Profil jour/nuit du pH perturbé|Les 4 dernières heures s'écartent de la forme habituelle de la journée",
        "m4": "ORP sous son niveau habituel|L'ORP, sans l'effet du pH, reste 30 mV sous sa médiane pendant 12 heures",
        "m5": "Sonde suspecte|Valeur figée 12 heures, aucune valeur pendant 2 heures, pics répétés, saut, ou pH et ORP qui ne bougent plus ensemble pendant 2 jours",
        "mon_note": "Les alarmes restent inconnues pendant les 14 premiers jours, le temps d'apprendre le bac ; seule la sonde suspecte fonctionne dès le départ. Tous les seuils sont réglables.",
        "mon_setup": "Choisissez les entités une fois. Ce service règle aussi les seuils :",
        "mon_cal": "Avec une entité d'étalonnage (la date de dernier réglage de la sonde), un étalonnage ne demande aucune action : les mesures autour sont écartées et l'historique suit le nouveau niveau au bout de 24 heures. Pour un nettoyage ou un changement d'eau, activez le switch de pause : il se coupe seul au bout de 6 heures.",
        "e_status": "État de la surveillance, progression de l'apprentissage dans les attributs",
        "e_ph": "Moyenne et amplitude 24 h du pH",
        "e_orp": "ORP sans l'effet quotidien du pH",
        "e_alarms": "Les six alarmes ci-dessus",
        "e_pause": "Suspend l'analyse",
        "sv_configure": "Choisit les entités surveillées et les seuils",
        "sv_reset": "Oublie l'historique pour réapprendre (nouvelle sonde)",
        "entities_title": "Entités",
        "entities_body": "Chaque aquarium est un appareil avec :",
        "h_entity": "Entité",
        "h_state": "État",
        "e_fish": "Nombre de poissons, par espèce dans les attributs",
        "e_corals": "Nombre de coraux, par espèce dans les attributs",
        "e_feeding": "Dernier nourrissage, avec son type (nourrisseur, raccourci, manuel) et sa source",
        "e_today": "Nourrissages depuis minuit",
        "entities_catalog": "Et l'appareil *ReefTank catalog* :",
        "e_update": "Version du catalogue installée et dernière publiée",
        "e_button": "Vérifie tout de suite si une nouvelle version existe",
        "services_title": "Services",
        "h_service": "Service",
        "h_effect": "Effet",
        "sv_feed": "Enregistre un nourrissage (nourrisseurs inconnus de Home Assistant, scripts)",
        "sv_add": "Ajoute des animaux à l'inventaire",
        "sv_remove": "Retire des animaux (pertes, cessions)",
        "services_note": "`aquarium` est le nom, l'identifiant ou l'identifiant d'appareil de l'aquarium.",
        "catalog_title": "Catalogue d'espèces",
        "catalog_body": "Poissons, coraux et textures viennent du [catalogue ReefTank]({catalog}), téléchargé au premier démarrage (github.com doit être joignable une fois), puis tenu à jour :",
        "c1": "une nouvelle version s'installe automatiquement ; *Paramètres → Appareils et services → ReefTank → Configurer* le désactive ;",
        "c2": "`button.reeftank_catalog_check_for_updates` vérifie tout de suite au lieu d'attendre la prochaine vérification (toutes les 12 heures) ;",
        "c3": "seul ce qui a changé est téléchargé, et une mise à jour interrompue laisse le catalogue précédent en place.",
        "catalog_own": "Vos propres espèces vont dans `<config>/reeftank/catalog/` (même organisation que le catalogue) : elles apparaissent dans l'éditeur sans redémarrer.",
        "tech_title": "Référence technique",
        "tech_body": "Modèle de données, API WebSocket, chaîne de rendu, comportement des poissons, format des sprites et mises à jour du catalogue : [référence technique]({tech}) (en anglais).",
        "dev_title": "Développement",
        "dev_body": "Les tests couvrent entièrement l'intégration et la CI y veille. `scripts/gen_readme.py` régénère cette page et ses sept traductions : c'est lui qu'il faut modifier, pas les fichiers générés.",
    },
    "de": {
        "ecosystem_line": f"Teil des [**ReefTech-Projekt-Ökosystems**]({SITE})",
        "languages": "Unterstützte Sprachen",
        "intro": (
            "Home-Assistant-Integration hinter der **Aquariumkarte** von "
            f"[ha-reef-card]({CARD}): ein lebendiges Bild Ihres Beckens, "
            "beleuchtet von Ihren echten Lampen, bevölkert von animierten "
            "Fischen und Korallen, mit Ihren Geräten und Entitäten darauf."
        ),
        "intro2": (
            "Sie speichert die Aquarien, ihre Bilder und ihren Besatz, "
            "protokolliert die Fütterungen und hält den Artenkatalog aktuell. "
            "Nichts Herstellerspezifisches: sie funktioniert mit Red Sea, Aqua "
            "Medic oder jedem anderen Gerät, das Home Assistant kennt."
        ),
        "preview": "Die Aquariumkarte",
        "features_title": "Funktionen",
        "f1": "**Ihr Foto, lebendig**: Wasser auf einem Foto Ihres Beckens umranden, die Karte animiert es",
        "f2": "**Echtes Licht**: das Wasser nimmt Farbe und Intensität Ihrer Lampen an (ReefLED oder jede `light`), nachts abgedunkelt, aber gut erkennbar",
        "f3": "**Fische und Korallen** aus dem [ReefTank-Katalog]({catalog}): Schwärme, Freiwasserschwimmer, Bodenbewohner, Grundeln, die aus ihrer Höhle schauen, Korallen, die sich mit den Pumpen wiegen",
        "f4": "**Tiefe**: Fische schwimmen hinter den umrandeten Steinen und ruhen nachts auf dem Sand",
        "f5": "**Gezeichnetes Becken**: kein schönes Foto vom Wasser? Zeichnen Sie es (Wasser, Sand, Gesteinstexturen) und behalten Sie den Rest des Fotos",
        "f6": "**Geräte und Entitäten** auf dem Bild, anklickbar; Zonen, die ein anderes Bild öffnen (das Technikbecken im Unterschrank)",
        "f7": "**Fütterung**: Futterautomaten, Red-Sea-Kurzbefehle oder ein Dienst protokollieren jede Fütterung; die Fische eilen zur Futterstelle",
        "f8": "**Bestand**: Anzahl der Fische und Korallen als Sensoren, mit Verlauf",
        "install_title": "Installation",
        "install_direct_title": "Direkte Installation",
        "install_direct_body": "Hier klicken, um das Repository direkt in HACS zu öffnen, dann auf „Herunterladen“ klicken:",
        "install_search_title": "Suche in HACS",
        "install_search_body": "Oder `{repo}` als benutzerdefiniertes Repository (Integration) hinzufügen und nach „ReefTank“ suchen.",
        "install_add": "Home Assistant neu starten, dann die Integration hinzufügen (ein Eintrag, nichts zu konfigurieren):",
        "install_card": "Die Aquariumkarte selbst kommt mit [ha-reef-card]({card}), ebenfalls zu installieren.",
        "start_title": "Erste Schritte",
        "s1": "Fügen Sie einem Dashboard eine **Reef Aquarium Card** hinzu (`custom:reef-aquarium-card`).",
        "s2": "Legen Sie in ihrem Editor ein Aquarium an (**{new}**), dann **{edit}**.",
        "s3": "**{views}**: ein Foto Ihres Beckens hochladen, das Wasser umranden, Sandlinie und Steine nachzeichnen.",
        "s4": "**{devices}** und **{lights}**: Geräte und Entitäten auf das Bild ziehen, Lampen platzieren.",
        "s5": "**{livestock}**: Fische und Korallen hinzufügen, dann speichern.",
        "start_note": "Die Kartenkonfiguration enthält nur die Aquarium-ID; alles andere speichert die Integration:",
        "editor_title": "Der Szeneneditor",
        "editor_body": "Ein Vollbilddialog, aus dem Karteneditor geöffnet, mit sechs Reitern:",
        "h_tab": "Reiter",
        "h_what": "Was man dort macht",
        "w_aquarium": "Name, Maße, das passende Cloud-Aquarium, Licht, unter dem die Fotos entstanden, Darstellungsstufe, Dunkelheit des Wassers nachts",
        "w_views": "Bilder; für jedes Wasser: Umriss, Sandlinie (vorne und hinten), Steine mit ihrer Tiefe, anklickbare Zonen, gezeichneter Hintergrund und seine Texturen",
        "w_devices": "Ihre Geräte und Entitäten nach Etage und Bereich, auf das Bild gezogen",
        "w_lights": "Lampen, die jedes Wasser beleuchten, und ihre Position; Pumpen, die das Wasser bewegen",
        "w_livestock": "Fische (Art, Anzahl, Größe, Revier) und Korallen (Art, Größe, Farben, Position)",
        "w_feeding": "Entitäten, die eine Fütterung protokollieren, und wo das Futter fällt",
        "levels_title": "Darstellungsstufen",
        "levels_body": "Jedes Aquarium wird in einer von drei Stufen dargestellt; eine Karte kann sie senken, z. B. auf einem langsamen Wandtablet:",
        "h_level": "Stufe",
        "h_shows": "Zeigt",
        "levels_note": "Ein Foto des Technikraums mit live angezeigten Geräten ist ein vollwertiges `static`-Aquarium.",
        "m6": "KH ändert sich zu schnell|Zwei aufeinanderfolgende KH-Tests weichen um mehr als 0,5 dKH ab",
        "mon_kh": "Mit einer KH-Test-Entität (z. B. der letzten Messung eines ReefDose-Kopfes) unterscheidet ein aktueller Test einen echten KH-Rückgang von einem CO2-Effekt oder einem Sondenproblem (`cause`) und liefert mit dem CO2 eine geschätzte KH zwischen zwei Tests.",
        "e_kh": "Geschätzte KH zwischen zwei Tests (braucht einen Test und das CO2)",
        "mon_title": "Wasserüberwachung",
        "mon_body": "ReefTank vergleicht Ihr Becken mit seinem eigenen jüngsten Verlauf statt mit allgemeinen Grenzwerten und löst Alarme aus, wenn es davon abweicht. pH und ORP können von jeder numerischen Entität stammen; ein CO2-Sensor im Raum ist optional. Der pH misst nicht die KH: Diese Alarme sagen Ihnen, wann ein Test fällig ist.",
        "mon_h_alarm": "Alarm",
        "mon_h_when": "Löst aus, wenn",
        "m1": "pH unter dem üblichen Niveau|Das 24-h-Mittel liegt 0,1 unter dem Median der letzten 14 Tage. Mit CO2-Sensor zeigt `cause`, ob das CO2 im Raum dies erklärt",
        "m2": "pH-Schwankung größer als üblich|Die 24-h-Amplitude übersteigt die übliche um 50 %",
        "m3": "pH-Tagesverlauf gestört|Die letzten 4 Stunden weichen von der üblichen Tagesform ab",
        "m4": "ORP unter dem üblichen Niveau|Der ORP ohne pH-Effekt bleibt 12 Stunden lang 30 mV unter seinem Median",
        "m5": "Verdächtige Sonde|12 Stunden eingefrorener Wert, 2 Stunden kein Wert, wiederholte Spitzen, ein Sprung, oder pH und ORP bewegen sich 2 Tage nicht mehr gemeinsam",
        "mon_note": "Die Alarme bleiben in den ersten 14 Tagen unbekannt, während das Becken gelernt wird; nur die verdächtige Sonde funktioniert von Anfang an. Alle Schwellen sind einstellbar.",
        "mon_setup": "Wählen Sie die Entitäten einmalig. Dieser Dienst setzt auch die Schwellen:",
        "mon_cal": "Mit einer Kalibrierentität (dem letzten Justierdatum der Sonde) ist bei einer Kalibrierung nichts zu tun: Die Messwerte darum herum werden verworfen, und der Verlauf folgt nach 24 Stunden dem neuen Niveau. Schalten Sie für eine Reinigung oder einen Wasserwechsel den Pausenschalter ein: Er schaltet sich nach 6 Stunden selbst aus.",
        "e_status": "Status der Überwachung, Lernfortschritt in den Attributen",
        "e_ph": "24-h-Mittel und -Amplitude des pH",
        "e_orp": "ORP ohne den täglichen pH-Effekt",
        "e_alarms": "Die sechs Alarme oben",
        "e_pause": "Setzt die Analyse aus",
        "sv_configure": "Wählt die überwachten Entitäten und die Schwellen",
        "sv_reset": "Verwirft den Verlauf, um neu zu lernen (neue Sonde)",
        "entities_title": "Entitäten",
        "entities_body": "Jedes Aquarium ist ein Gerät mit:",
        "h_entity": "Entität",
        "h_state": "Zustand",
        "e_fish": "Anzahl der Fische, pro Art in den Attributen",
        "e_corals": "Anzahl der Korallen, pro Art in den Attributen",
        "e_feeding": "Letzte Fütterung, mit Art (Futterautomat, Kurzbefehl, manuell) und Quelle",
        "e_today": "Fütterungen seit Mitternacht",
        "entities_catalog": "Und das Gerät *ReefTank catalog*:",
        "e_update": "Installierte und neueste Katalogversion",
        "e_button": "Prüft sofort, ob eine neue Version vorliegt",
        "services_title": "Dienste",
        "h_service": "Dienst",
        "h_effect": "Wirkung",
        "sv_feed": "Protokolliert eine Fütterung (Futterautomaten außerhalb von Home Assistant, Skripte)",
        "sv_add": "Fügt dem Bestand Tiere hinzu",
        "sv_remove": "Entfernt Tiere (Verluste, Abgabe)",
        "services_note": "`aquarium` ist Name, ID oder Geräte-ID des Aquariums.",
        "catalog_title": "Artenkatalog",
        "catalog_body": "Fische, Korallen und Texturen stammen aus dem [ReefTank-Katalog]({catalog}), beim ersten Start heruntergeladen (github.com muss einmal erreichbar sein) und dann aktuell gehalten:",
        "c1": "eine neue Version wird automatisch installiert; *Einstellungen → Geräte & Dienste → ReefTank → Konfigurieren* schaltet das ab;",
        "c2": "`button.reeftank_catalog_check_for_updates` prüft sofort, statt auf die nächste Prüfung (alle 12 Stunden) zu warten;",
        "c3": "nur Geändertes wird heruntergeladen, und ein abgebrochenes Update lässt den bisherigen Katalog unangetastet.",
        "catalog_own": "Eigene Arten gehören nach `<config>/reeftank/catalog/` (gleicher Aufbau wie der Katalog): sie erscheinen ohne Neustart im Editor.",
        "tech_title": "Technische Referenz",
        "tech_body": "Datenmodell, WebSocket-API, Render-Pipeline, Fischverhalten, Sprite-Format und Katalog-Updates: [technische Referenz]({tech}) (auf Englisch).",
        "dev_title": "Entwicklung",
        "dev_body": "Die Tests decken die Integration vollständig ab, und die CI sorgt dafür, dass es so bleibt. `scripts/gen_readme.py` erzeugt diese Seite und ihre sieben Übersetzungen: dort ändern, nicht in den erzeugten Dateien.",
    },
    "es": {
        "ecosystem_line": f"Parte del [**ecosistema de proyectos ReefTech**]({SITE})",
        "languages": "Idiomas disponibles",
        "intro": (
            "Integración de Home Assistant detrás de la **tarjeta de acuario** "
            f"de [ha-reef-card]({CARD}): una imagen viva de su acuario, "
            "iluminada por sus lámparas reales, poblada de peces y corales "
            "animados, y con sus dispositivos y entidades encima."
        ),
        "intro2": (
            "Guarda los acuarios, sus imágenes y su fauna, registra las "
            "alimentaciones y mantiene al día el catálogo de especies. Nada "
            "propio de una marca: funciona con Red Sea, Aqua Medic o cualquier "
            "otro equipo que Home Assistant conozca."
        ),
        "preview": "La tarjeta de acuario",
        "features_title": "Funciones",
        "f1": "**Su foto, viva**: contornee el agua en una foto de su acuario y la tarjeta la anima",
        "f2": "**Luz real**: el agua toma el color y la intensidad de sus lámparas (ReefLED o cualquier `light`), oscurecida de noche pero legible",
        "f3": "**Peces y corales** del [catálogo ReefTank]({catalog}): cardúmenes, nadadores de aguas abiertas, peces de arena, gobios que asoman de su madriguera, corales que se mecen con las bombas",
        "f4": "**Profundidad**: los peces pasan detrás de las rocas contorneadas y descansan sobre la arena de noche",
        "f5": "**Acuario dibujado**: ¿sin una buena foto del agua? Dibújela (agua, arena, texturas de roca) conservando el resto de la foto",
        "f6": "**Dispositivos y entidades** sobre la imagen, clicables; zonas que abren otra imagen (el sump en el mueble)",
        "f7": "**Alimentación**: comederos, atajos Red Sea o un servicio registran cada alimentación; los peces acuden al punto de alimentación",
        "f8": "**Inventario**: número de peces y corales como sensores, con su historial",
        "install_title": "Instalación",
        "install_direct_title": "Instalación directa",
        "install_direct_body": "Haga clic aquí para abrir el repositorio directamente en HACS y pulse «Descargar»:",
        "install_search_title": "Búsqueda en HACS",
        "install_search_body": "O añada `{repo}` como repositorio personalizado (Integración) y busque «ReefTank».",
        "install_add": "Reinicie Home Assistant y añada la integración (una sola entrada, nada que configurar):",
        "install_card": "La tarjeta de acuario viene con [ha-reef-card]({card}), que también hay que instalar.",
        "start_title": "Primeros pasos",
        "s1": "Añada una **Reef Aquarium Card** a un panel (`custom:reef-aquarium-card`).",
        "s2": "En su editor, cree un acuario (**{new}**) y luego **{edit}**.",
        "s3": "**{views}**: suba una foto de su acuario, contornee el agua, trace la línea de arena y las rocas.",
        "s4": "**{devices}** y **{lights}**: coloque sus dispositivos y entidades en la imagen, sitúe sus lámparas.",
        "s5": "**{livestock}**: añada sus peces y corales y guarde.",
        "start_note": "La configuración de la tarjeta solo contiene el id del acuario; todo lo demás lo guarda la integración:",
        "editor_title": "El editor de escena",
        "editor_body": "Un diálogo a pantalla completa, abierto desde el editor de la tarjeta, con seis pestañas:",
        "h_tab": "Pestaña",
        "h_what": "Qué se hace en ella",
        "w_aquarium": "Nombre, dimensiones, el acuario de la nube correspondiente, luz con la que se tomaron las fotos, nivel de renderizado, oscuridad del agua de noche",
        "w_views": "Las imágenes; para cada agua: contorno, línea de arena (delante y detrás), rocas y su profundidad, zonas clicables, fondo dibujado y sus texturas",
        "w_devices": "Sus dispositivos y entidades por planta y zona, arrastrados sobre la imagen",
        "w_lights": "Las lámparas que iluminan cada agua y su posición; las bombas que mueven el agua",
        "w_livestock": "Peces (especie, número, tamaño, refugio) y corales (especie, tamaño, colores, posición)",
        "w_feeding": "Las entidades que registran una alimentación, y dónde cae la comida",
        "levels_title": "Niveles de renderizado",
        "levels_body": "Cada acuario se muestra en uno de tres niveles; una tarjeta puede bajarlo, por ejemplo en una tableta de pared lenta:",
        "h_level": "Nivel",
        "h_shows": "Muestra",
        "levels_note": "Una foto del cuarto técnico con sus dispositivos en vivo es un acuario `static` perfectamente válido.",
        "m6": "KH que varía demasiado rápido|Dos pruebas de KH seguidas difieren más de 0,5 dKH",
        "mon_kh": "Con una entidad de pruebas de KH (la última medida de un cabezal ReefDose, por ejemplo), una prueba reciente distingue un descenso real del KH de un efecto del CO2 o de un problema de sonda (`cause`) y, con el CO2, da un KH estimado entre dos pruebas.",
        "e_kh": "KH estimado entre dos pruebas (necesita una prueba y el CO2)",
        "mon_title": "Vigilancia del agua",
        "mon_body": "ReefTank compara su acuario con su propio historial reciente, en lugar de con límites universales, y lanza alarmas cuando se aparta de lo habitual. El pH y el ORP pueden venir de cualquier entidad numérica; un sensor de CO2 en la habitación es opcional. El pH no mide el KH: estas alarmas le indican cuándo hacer una prueba.",
        "mon_h_alarm": "Alarma",
        "mon_h_when": "Se activa cuando",
        "m1": "pH por debajo de su nivel habitual|La media de 24 h queda 0,1 por debajo de la mediana de los últimos 14 días. Con un sensor de CO2, `cause` indica si el CO2 de la habitación lo explica",
        "m2": "Amplitud del pH mayor de lo habitual|La amplitud de 24 h supera la habitual en un 50 %",
        "m3": "Perfil diario del pH alterado|Las últimas 4 horas se alejan de la forma habitual del día",
        "m4": "ORP por debajo de su nivel habitual|El ORP, sin el efecto del pH, sigue 30 mV por debajo de su mediana durante 12 horas",
        "m5": "Sonda sospechosa|Valor congelado 12 horas, ningún valor durante 2 horas, picos repetidos, un salto, o pH y ORP que dejan de moverse juntos durante 2 días",
        "mon_note": "Las alarmas siguen desconocidas los primeros 14 días, mientras se aprende el acuario; solo la sonda sospechosa funciona desde el principio. Todos los umbrales se pueden ajustar.",
        "mon_setup": "Elija las entidades una vez. Este servicio también ajusta los umbrales:",
        "mon_cal": "Con una entidad de calibración (la fecha de último ajuste de la sonda), una calibración no requiere ninguna acción: se descartan las lecturas cercanas y el historial sigue el nuevo nivel tras 24 horas. Para una limpieza o un cambio de agua, encienda el interruptor de pausa: se apaga solo tras 6 horas.",
        "e_status": "Estado de la vigilancia, progreso del aprendizaje en los atributos",
        "e_ph": "Media y amplitud de 24 h del pH",
        "e_orp": "ORP sin el efecto diario del pH",
        "e_alarms": "Las seis alarmas anteriores",
        "e_pause": "Suspende el análisis",
        "sv_configure": "Elige las entidades vigiladas y los umbrales",
        "sv_reset": "Olvida el historial para volver a aprender (sonda nueva)",
        "entities_title": "Entidades",
        "entities_body": "Cada acuario es un dispositivo con:",
        "h_entity": "Entidad",
        "h_state": "Estado",
        "e_fish": "Número de peces, por especie en los atributos",
        "e_corals": "Número de corales, por especie en los atributos",
        "e_feeding": "Última alimentación, con su tipo (comedero, atajo, manual) y su fuente",
        "e_today": "Alimentaciones desde medianoche",
        "entities_catalog": "Y el dispositivo *ReefTank catalog*:",
        "e_update": "Versión del catálogo instalada y última publicada",
        "e_button": "Comprueba al momento si hay una versión nueva",
        "services_title": "Servicios",
        "h_service": "Servicio",
        "h_effect": "Efecto",
        "sv_feed": "Registra una alimentación (comederos desconocidos para Home Assistant, scripts)",
        "sv_add": "Añade animales al inventario",
        "sv_remove": "Retira animales (bajas, cesiones)",
        "services_note": "`aquarium` es el nombre, el id o el id de dispositivo del acuario.",
        "catalog_title": "Catálogo de especies",
        "catalog_body": "Peces, corales y texturas vienen del [catálogo ReefTank]({catalog}), descargado en el primer arranque (github.com debe ser accesible una vez) y luego mantenido al día:",
        "c1": "una versión nueva se instala automáticamente; *Ajustes → Dispositivos y servicios → ReefTank → Configurar* lo desactiva;",
        "c2": "`button.reeftank_catalog_check_for_updates` comprueba al momento en lugar de esperar a la próxima comprobación (cada 12 horas);",
        "c3": "solo se descarga lo que ha cambiado, y una actualización interrumpida deja el catálogo anterior en su sitio.",
        "catalog_own": "Sus propias especies van en `<config>/reeftank/catalog/` (misma organización que el catálogo): aparecen en el editor sin reiniciar.",
        "tech_title": "Referencia técnica",
        "tech_body": "Modelo de datos, API WebSocket, cadena de renderizado, comportamiento de los peces, formato de sprites y actualizaciones del catálogo: [referencia técnica]({tech}) (en inglés).",
        "dev_title": "Desarrollo",
        "dev_body": "Las pruebas cubren toda la integración y la CI vela por ello. `scripts/gen_readme.py` regenera esta página y sus siete traducciones: hay que modificarlo a él, no a los archivos generados.",
    },
    "it": {
        "ecosystem_line": f"Parte dell'[**ecosistema di progetti ReefTech**]({SITE})",
        "languages": "Lingue disponibili",
        "intro": (
            "Integrazione Home Assistant dietro la **scheda acquario** di "
            f"[ha-reef-card]({CARD}): un'immagine viva della vostra vasca, "
            "illuminata dalle vostre vere lampade, popolata di pesci e coralli "
            "animati, con sopra i vostri dispositivi ed entità."
        ),
        "intro2": (
            "Conserva gli acquari, le loro immagini e la loro fauna, registra "
            "le alimentazioni e tiene aggiornato il catalogo delle specie. "
            "Niente di legato a una marca: funziona con Red Sea, Aqua Medic o "
            "qualsiasi altra apparecchiatura nota a Home Assistant."
        ),
        "preview": "La scheda acquario",
        "features_title": "Funzionalità",
        "f1": "**La vostra foto, viva**: contornate l'acqua su una foto della vasca, la scheda la anima",
        "f2": "**Luce reale**: l'acqua prende colore e intensità delle vostre lampade (ReefLED o qualsiasi `light`), scurita di notte ma leggibile",
        "f3": "**Pesci e coralli** dal [catalogo ReefTank]({catalog}): banchi, nuotatori di acque libere, pesci di sabbia, ghiozzi che spuntano dalla tana, coralli che ondeggiano con le pompe",
        "f4": "**Profondità**: i pesci passano dietro le rocce contornate e di notte riposano sulla sabbia",
        "f5": "**Vasca disegnata**: nessuna bella foto dell'acqua? Disegnatela (acqua, sabbia, texture di roccia) tenendo il resto della foto",
        "f6": "**Dispositivi ed entità** sull'immagine, cliccabili; zone che aprono un'altra immagine (la sump nel mobile)",
        "f7": "**Alimentazione**: alimentatori, scorciatoie Red Sea o un servizio registrano ogni alimentazione; i pesci accorrono al punto di alimentazione",
        "f8": "**Inventario**: numero di pesci e coralli come sensori, con la loro cronologia",
        "install_title": "Installazione",
        "install_direct_title": "Installazione diretta",
        "install_direct_body": "Fate clic qui per aprire il repository direttamente in HACS, poi su «Scarica»:",
        "install_search_title": "Ricerca in HACS",
        "install_search_body": "Oppure aggiungete `{repo}` come repository personalizzato (Integrazione) e cercate «ReefTank».",
        "install_add": "Riavviate Home Assistant, poi aggiungete l'integrazione (una sola voce, niente da configurare):",
        "install_card": "La scheda acquario arriva con [ha-reef-card]({card}), da installare anch'essa.",
        "start_title": "Primi passi",
        "s1": "Aggiungete una **Reef Aquarium Card** a una plancia (`custom:reef-aquarium-card`).",
        "s2": "Nel suo editor, create un acquario (**{new}**), poi **{edit}**.",
        "s3": "**{views}**: caricate una foto della vasca, contornate l'acqua, tracciate la linea della sabbia e le rocce.",
        "s4": "**{devices}** e **{lights}**: posate dispositivi ed entità sull'immagine, posizionate le lampade.",
        "s5": "**{livestock}**: aggiungete pesci e coralli, poi salvate.",
        "start_note": "La configurazione della scheda contiene solo l'id dell'acquario; tutto il resto è conservato dall'integrazione:",
        "editor_title": "L'editor di scena",
        "editor_body": "Una finestra a schermo intero, aperta dall'editor della scheda, con sei schede:",
        "h_tab": "Scheda",
        "h_what": "Cosa si fa",
        "w_aquarium": "Nome, dimensioni, l'acquario cloud corrispondente, luce con cui sono state scattate le foto, livello di resa, oscurità dell'acqua di notte",
        "w_views": "Le immagini; per ogni acqua: contorno, linea della sabbia (davanti e dietro), rocce e loro profondità, zone cliccabili, sfondo disegnato e sue texture",
        "w_devices": "I vostri dispositivi ed entità per piano e area, trascinati sull'immagine",
        "w_lights": "Le lampade che illuminano ogni acqua e la loro posizione; le pompe che muovono l'acqua",
        "w_livestock": "Pesci (specie, numero, taglia, rifugio) e coralli (specie, taglia, colori, posizione)",
        "w_feeding": "Le entità che registrano un'alimentazione, e dove cade il cibo",
        "levels_title": "Livelli di resa",
        "levels_body": "Ogni acquario è reso a uno di tre livelli; una scheda può abbassarlo, ad esempio su un tablet a muro lento:",
        "h_level": "Livello",
        "h_shows": "Mostra",
        "levels_note": "Una foto del locale tecnico con i dispositivi in tempo reale è un ottimo acquario `static`.",
        "m6": "KH che varia troppo in fretta|Due test KH consecutivi differiscono di più di 0,5 dKH",
        "mon_kh": "Con un'entità dei test KH (l'ultima misura di una testa ReefDose, ad esempio), un test recente distingue un vero calo del KH da un effetto della CO2 o da un problema di sonda (`cause`) e, con la CO2, fornisce un KH stimato tra due test.",
        "e_kh": "KH stimato tra due test (richiede un test e la CO2)",
        "mon_title": "Monitoraggio dell'acqua",
        "mon_body": "ReefTank confronta la vasca con il suo storico recente, invece che con limiti universali, e lancia allarmi quando si allontana dal solito. pH e ORP possono provenire da qualsiasi entità numerica; un sensore di CO2 nella stanza è facoltativo. Il pH non misura il KH: questi allarmi indicano quando fare un test.",
        "mon_h_alarm": "Allarme",
        "mon_h_when": "Scatta quando",
        "m1": "pH sotto il livello abituale|La media di 24 h è 0,1 sotto la mediana degli ultimi 14 giorni. Con un sensore di CO2, `cause` indica se la CO2 della stanza lo spiega",
        "m2": "Ampiezza del pH superiore al solito|L'ampiezza di 24 h supera quella abituale del 50 %",
        "m3": "Profilo giornaliero del pH alterato|Le ultime 4 ore si allontanano dalla forma abituale della giornata",
        "m4": "ORP sotto il livello abituale|L'ORP, senza l'effetto del pH, resta 30 mV sotto la mediana per 12 ore",
        "m5": "Sonda sospetta|Valore bloccato per 12 ore, nessun valore per 2 ore, picchi ripetuti, un salto, o pH e ORP che non si muovono più insieme per 2 giorni",
        "mon_note": "Gli allarmi restano sconosciuti per i primi 14 giorni, mentre la vasca viene appresa; solo la sonda sospetta funziona da subito. Tutte le soglie sono regolabili.",
        "mon_setup": "Scegli le entità una volta. Questo servizio imposta anche le soglie:",
        "mon_cal": "Con un'entità di calibrazione (la data dell'ultima regolazione della sonda), una calibrazione non richiede azioni: le letture vicine vengono scartate e lo storico segue il nuovo livello dopo 24 ore. Per una pulizia o un cambio d'acqua, attiva l'interruttore di pausa: si spegne da solo dopo 6 ore.",
        "e_status": "Stato del monitoraggio, avanzamento dell'apprendimento negli attributi",
        "e_ph": "Media e ampiezza di 24 h del pH",
        "e_orp": "ORP senza l'effetto quotidiano del pH",
        "e_alarms": "I sei allarmi qui sopra",
        "e_pause": "Sospende l'analisi",
        "sv_configure": "Sceglie le entità monitorate e le soglie",
        "sv_reset": "Dimentica lo storico per imparare di nuovo (nuova sonda)",
        "entities_title": "Entità",
        "entities_body": "Ogni acquario è un dispositivo con:",
        "h_entity": "Entità",
        "h_state": "Stato",
        "e_fish": "Numero di pesci, per specie negli attributi",
        "e_corals": "Numero di coralli, per specie negli attributi",
        "e_feeding": "Ultima alimentazione, con tipo (alimentatore, scorciatoia, manuale) e fonte",
        "e_today": "Alimentazioni dalla mezzanotte",
        "entities_catalog": "E il dispositivo *ReefTank catalog*:",
        "e_update": "Versione del catalogo installata e ultima pubblicata",
        "e_button": "Controlla subito se c'è una nuova versione",
        "services_title": "Servizi",
        "h_service": "Servizio",
        "h_effect": "Effetto",
        "sv_feed": "Registra un'alimentazione (alimentatori sconosciuti a Home Assistant, script)",
        "sv_add": "Aggiunge animali all'inventario",
        "sv_remove": "Rimuove animali (perdite, cessioni)",
        "services_note": "`aquarium` è il nome, l'id o l'id del dispositivo dell'acquario.",
        "catalog_title": "Catalogo delle specie",
        "catalog_body": "Pesci, coralli e texture provengono dal [catalogo ReefTank]({catalog}), scaricato al primo avvio (github.com deve essere raggiungibile una volta) e poi tenuto aggiornato:",
        "c1": "una nuova versione si installa automaticamente; *Impostazioni → Dispositivi e servizi → ReefTank → Configura* lo disattiva;",
        "c2": "`button.reeftank_catalog_check_for_updates` controlla subito invece di attendere il prossimo controllo (ogni 12 ore);",
        "c3": "si scarica solo ciò che è cambiato, e un aggiornamento interrotto lascia il catalogo precedente al suo posto.",
        "catalog_own": "Le vostre specie vanno in `<config>/reeftank/catalog/` (stessa struttura del catalogo): compaiono nell'editor senza riavviare.",
        "tech_title": "Riferimento tecnico",
        "tech_body": "Modello dei dati, API WebSocket, pipeline di resa, comportamento dei pesci, formato degli sprite e aggiornamenti del catalogo: [riferimento tecnico]({tech}) (in inglese).",
        "dev_title": "Sviluppo",
        "dev_body": "I test coprono interamente l'integrazione e la CI lo garantisce. `scripts/gen_readme.py` rigenera questa pagina e le sue sette traduzioni: va modificato lui, non i file generati.",
    },
    "nl": {
        "ecosystem_line": f"Onderdeel van het [**ReefTech-projectecosysteem**]({SITE})",
        "languages": "Beschikbare talen",
        "intro": (
            "Home Assistant-integratie achter de **aquariumkaart** van "
            f"[ha-reef-card]({CARD}): een levend beeld van uw bak, verlicht "
            "door uw echte lampen, bevolkt met geanimeerde vissen en koralen, "
            "met uw apparaten en entiteiten erop."
        ),
        "intro2": (
            "Ze bewaart de aquaria, hun afbeeldingen en hun bezetting, legt de "
            "voederingen vast en houdt de soortencatalogus bij. Niets "
            "merkgebonden: ze werkt met Red Sea, Aqua Medic of elk ander "
            "apparaat dat Home Assistant kent."
        ),
        "preview": "De aquariumkaart",
        "features_title": "Functies",
        "f1": "**Uw foto, levend**: omlijn het water op een foto van uw bak, de kaart brengt het tot leven",
        "f2": "**Echt licht**: het water krijgt de kleur en de sterkte van uw lampen (ReefLED of elke `light`), 's nachts gedimd maar leesbaar",
        "f3": "**Vissen en koralen** uit de [ReefTank-catalogus]({catalog}): scholen, openwaterzwemmers, zandbewoners, grondels die uit hun hol kijken, koralen die meewiegen met de pompen",
        "f4": "**Diepte**: vissen zwemmen achter de omlijnde stenen en rusten 's nachts op het zand",
        "f5": "**Getekende bak**: geen mooie foto van het water? Teken het (water, zand, steentexturen) en houd de rest van de foto",
        "f6": "**Apparaten en entiteiten** op de afbeelding, klikbaar; zones die een andere afbeelding openen (de sump in het meubel)",
        "f7": "**Voederen**: voederautomaten, Red Sea-snelkoppelingen of een dienst leggen elke voedering vast; de vissen haasten zich naar het voederpunt",
        "f8": "**Inventaris**: aantal vissen en koralen als sensoren, met hun geschiedenis",
        "install_title": "Installatie",
        "install_direct_title": "Directe installatie",
        "install_direct_body": 'Klik hier om de repository direct in HACS te openen en klik op "Downloaden":',
        "install_search_title": "Zoeken in HACS",
        "install_search_body": 'Of voeg `{repo}` toe als aangepaste repository (Integratie) en zoek naar "ReefTank".',
        "install_add": "Herstart Home Assistant en voeg de integratie toe (één item, niets in te stellen):",
        "install_card": "De aquariumkaart zelf komt met [ha-reef-card]({card}), dat u ook installeert.",
        "start_title": "Aan de slag",
        "s1": "Voeg een **Reef Aquarium Card** toe aan een dashboard (`custom:reef-aquarium-card`).",
        "s2": "Maak in de editor een aquarium aan (**{new}**), daarna **{edit}**.",
        "s3": "**{views}**: upload een foto van uw bak, omlijn het water, trek de zandlijn en de stenen over.",
        "s4": "**{devices}** en **{lights}**: zet uw apparaten en entiteiten op de afbeelding, plaats uw lampen.",
        "s5": "**{livestock}**: voeg uw vissen en koralen toe en sla op.",
        "start_note": "De kaartconfiguratie bevat alleen het id van het aquarium; al de rest bewaart de integratie:",
        "editor_title": "De scène-editor",
        "editor_body": "Een schermvullend venster, geopend vanuit de kaarteditor, met zes tabbladen (de kaart is nog niet in het Nederlands vertaald):",
        "h_tab": "Tabblad",
        "h_what": "Wat u er doet",
        "w_aquarium": "Naam, afmetingen, het bijbehorende cloudaquarium, licht waaronder de foto's genomen zijn, weergaveniveau, duisternis van het water 's nachts",
        "w_views": "De afbeeldingen; per water: omtrek, zandlijn (voor en achter), stenen met hun diepte, klikbare zones, getekende achtergrond en zijn texturen",
        "w_devices": "Uw apparaten en entiteiten per verdieping en ruimte, naar de afbeelding gesleept",
        "w_lights": "De lampen die elk water verlichten en hun positie; de pompen die het water bewegen",
        "w_livestock": "Vissen (soort, aantal, grootte, thuis) en koralen (soort, grootte, kleuren, positie)",
        "w_feeding": "De entiteiten die een voedering vastleggen, en waar het voer valt",
        "levels_title": "Weergaveniveaus",
        "levels_body": "Elk aquarium wordt op een van drie niveaus weergegeven; een kaart kan het verlagen, bijvoorbeeld op een trage wandtablet:",
        "h_level": "Niveau",
        "h_shows": "Toont",
        "levels_note": "Een foto van de technische ruimte met live apparaten erop is een prima `static`-aquarium.",
        "m6": "KH verandert te snel|Twee opeenvolgende KH-tests verschillen meer dan 0,5 dKH",
        "mon_kh": "Met een KH-testentiteit (bijvoorbeeld de laatste meting van een ReefDose-kop) onderscheidt een recente test een echte KH-daling van een CO2-effect of een sondeprobleem (`cause`) en geeft met de CO2 een geschatte KH tussen twee tests.",
        "e_kh": "Geschatte KH tussen twee tests (vereist een test en de CO2)",
        "mon_title": "Waterbewaking",
        "mon_body": "ReefTank vergelijkt uw aquarium met zijn eigen recente geschiedenis in plaats van met algemene grenzen, en geeft alarmen wanneer het afwijkt. pH en ORP kunnen van elke numerieke entiteit komen; een CO2-sensor in de ruimte is optioneel. De pH meet de KH niet: deze alarmen vertellen wanneer u moet testen.",
        "mon_h_alarm": "Alarm",
        "mon_h_when": "Gaat af wanneer",
        "m1": "pH onder het gebruikelijke niveau|Het 24-uursgemiddelde ligt 0,1 onder de mediaan van de laatste 14 dagen. Met een CO2-sensor geeft `cause` aan of de CO2 in de ruimte dit verklaart",
        "m2": "pH-schommeling groter dan gebruikelijk|De 24-uursamplitude is 50 % groter dan gebruikelijk",
        "m3": "pH-dagpatroon verstoord|De laatste 4 uur wijken af van de gebruikelijke vorm van de dag",
        "m4": "ORP onder het gebruikelijke niveau|De ORP zonder pH-effect blijft 12 uur lang 30 mV onder de mediaan",
        "m5": "Verdachte sonde|Een waarde 12 uur bevroren, 2 uur geen waarde, herhaalde pieken, een sprong, of pH en ORP die 2 dagen niet meer samen bewegen",
        "mon_note": "De alarmen blijven de eerste 14 dagen onbekend, terwijl het aquarium wordt geleerd; alleen de verdachte sonde werkt vanaf het begin. Alle drempels zijn instelbaar.",
        "mon_setup": "Kies de entiteiten eenmalig. Deze dienst stelt ook de drempels in:",
        "mon_cal": "Met een kalibratie-entiteit (de datum van de laatste afstelling van de sonde) vraagt een kalibratie geen actie: de metingen eromheen vervallen en de geschiedenis volgt na 24 uur het nieuwe niveau. Zet bij schoonmaken of waterverversing de pauzeschakelaar aan: die gaat na 6 uur vanzelf uit.",
        "e_status": "Status van de bewaking, leervoortgang in de attributen",
        "e_ph": "24-uursgemiddelde en -amplitude van de pH",
        "e_orp": "ORP zonder het dagelijkse pH-effect",
        "e_alarms": "De zes alarmen hierboven",
        "e_pause": "Stopt de analyse tijdelijk",
        "sv_configure": "Kiest de bewaakte entiteiten en de drempels",
        "sv_reset": "Vergeet de geschiedenis om opnieuw te leren (nieuwe sonde)",
        "entities_title": "Entiteiten",
        "entities_body": "Elk aquarium is een apparaat met:",
        "h_entity": "Entiteit",
        "h_state": "Status",
        "e_fish": "Aantal vissen, per soort in de attributen",
        "e_corals": "Aantal koralen, per soort in de attributen",
        "e_feeding": "Laatste voedering, met soort (automaat, snelkoppeling, handmatig) en bron",
        "e_today": "Voederingen sinds middernacht",
        "entities_catalog": "En het apparaat *ReefTank catalog*:",
        "e_update": "Geïnstalleerde en nieuwste catalogusversie",
        "e_button": "Controleert meteen of er een nieuwe versie is",
        "services_title": "Diensten",
        "h_service": "Dienst",
        "h_effect": "Effect",
        "sv_feed": "Legt een voedering vast (automaten die Home Assistant niet kent, scripts)",
        "sv_add": "Voegt dieren toe aan de inventaris",
        "sv_remove": "Verwijdert dieren (verlies, weggegeven)",
        "services_note": "`aquarium` is de naam, het id of het apparaat-id van het aquarium.",
        "catalog_title": "Soortencatalogus",
        "catalog_body": "Vissen, koralen en texturen komen uit de [ReefTank-catalogus]({catalog}), gedownload bij de eerste start (github.com moet één keer bereikbaar zijn) en daarna bijgehouden:",
        "c1": "een nieuwe versie wordt automatisch geïnstalleerd; *Instellingen → Apparaten & diensten → ReefTank → Configureren* zet dit uit;",
        "c2": "`button.reeftank_catalog_check_for_updates` controleert meteen in plaats van te wachten op de volgende controle (elke 12 uur);",
        "c3": "alleen wat gewijzigd is wordt gedownload, en een onderbroken update laat de vorige catalogus staan.",
        "catalog_own": "Uw eigen soorten horen in `<config>/reeftank/catalog/` (zelfde indeling als de catalogus): ze verschijnen in de editor zonder herstart.",
        "tech_title": "Technische referentie",
        "tech_body": "Datamodel, WebSocket-API, weergaveketen, visgedrag, spriteformaat en catalogusupdates: [technische referentie]({tech}) (in het Engels).",
        "dev_title": "Ontwikkeling",
        "dev_body": "De tests dekken de integratie volledig af en de CI bewaakt dat. `scripts/gen_readme.py` genereert deze pagina en haar zeven vertalingen: pas dat script aan, niet de gegenereerde bestanden.",
    },
    "pl": {
        "ecosystem_line": f"Część [**ekosystemu projektów ReefTech**]({SITE})",
        "languages": "Dostępne języki",
        "intro": (
            "Integracja Home Assistant stojąca za **kartą akwarium** z "
            f"[ha-reef-card]({CARD}): żywy obraz Twojego zbiornika, oświetlony "
            "Twoimi prawdziwymi lampami, zamieszkany przez animowane ryby i "
            "koralowce, z Twoimi urządzeniami i encjami."
        ),
        "intro2": (
            "Przechowuje akwaria, ich zdjęcia i obsadę, rejestruje karmienia i "
            "aktualizuje katalog gatunków. Nic nie jest związane z marką: "
            "działa z Red Sea, Aqua Medic lub dowolnym innym sprzętem znanym "
            "Home Assistant."
        ),
        "preview": "Karta akwarium",
        "features_title": "Funkcje",
        "f1": "**Twoje zdjęcie, żywe**: obrysuj wodę na zdjęciu zbiornika, a karta ją ożywi",
        "f2": "**Prawdziwe światło**: woda przyjmuje kolor i natężenie Twoich lamp (ReefLED lub dowolne `light`), nocą przyciemniona, ale czytelna",
        "f3": "**Ryby i koralowce** z [katalogu ReefTank]({catalog}): ławice, pływaki otwartej wody, ryby piaskowe, babki wyglądające z norki, koralowce falujące z pompami",
        "f4": "**Głębia**: ryby pływają za obrysowanymi skałami, a nocą odpoczywają na piasku",
        "f5": "**Rysowany zbiornik**: brak ładnego zdjęcia wody? Narysuj ją (woda, piasek, tekstury skał), zachowując resztę zdjęcia",
        "f6": "**Urządzenia i encje** na obrazie, klikalne; strefy otwierające inny obraz (sump w szafce)",
        "f7": "**Karmienie**: karmniki, skróty Red Sea lub usługa rejestrują każde karmienie; ryby płyną do punktu karmienia",
        "f8": "**Inwentarz**: liczba ryb i koralowców jako sensory, z historią",
        "install_title": "Instalacja",
        "install_direct_title": "Instalacja bezpośrednia",
        "install_direct_body": "Kliknij tutaj, aby otworzyć repozytorium bezpośrednio w HACS, i kliknij „Pobierz”:",
        "install_search_title": "Wyszukiwanie w HACS",
        "install_search_body": "Lub dodaj `{repo}` jako niestandardowe repozytorium (Integracja) i wyszukaj „ReefTank”.",
        "install_add": "Uruchom ponownie Home Assistant, a następnie dodaj integrację (jeden wpis, nic do konfiguracji):",
        "install_card": "Sama karta akwarium pochodzi z [ha-reef-card]({card}), które również trzeba zainstalować.",
        "start_title": "Pierwsze kroki",
        "s1": "Dodaj **Reef Aquarium Card** do pulpitu (`custom:reef-aquarium-card`).",
        "s2": "W jej edytorze utwórz akwarium (**{new}**), następnie **{edit}**.",
        "s3": "**{views}**: prześlij zdjęcie zbiornika, obrysuj wodę, wyznacz linię piasku i skały.",
        "s4": "**{devices}** i **{lights}**: umieść urządzenia i encje na obrazie, ustaw lampy.",
        "s5": "**{livestock}**: dodaj ryby i koralowce, potem zapisz.",
        "start_note": "Konfiguracja karty zawiera tylko id akwarium; resztę przechowuje integracja:",
        "editor_title": "Edytor sceny",
        "editor_body": "Pełnoekranowe okno, otwierane z edytora karty, z sześcioma zakładkami:",
        "h_tab": "Zakładka",
        "h_what": "Co się w niej robi",
        "w_aquarium": "Nazwa, wymiary, odpowiadające akwarium w chmurze, światło, przy którym zrobiono zdjęcia, poziom renderowania, ciemność wody w nocy",
        "w_views": "Obrazy; dla każdej wody: obrys, linia piasku (przód i tył), skały i ich głębokość, strefy klikalne, rysowane tło i jego tekstury",
        "w_devices": "Twoje urządzenia i encje według pięter i obszarów, przeciągane na obraz",
        "w_lights": "Lampy oświetlające każdą wodę i ich położenie; pompy poruszające wodę",
        "w_livestock": "Ryby (gatunek, liczba, rozmiar, schronienie) i koralowce (gatunek, rozmiar, kolory, położenie)",
        "w_feeding": "Encje rejestrujące karmienie i miejsce, gdzie spada pokarm",
        "levels_title": "Poziomy renderowania",
        "levels_body": "Każde akwarium jest wyświetlane na jednym z trzech poziomów; karta może go obniżyć, np. na wolnym tablecie ściennym:",
        "h_level": "Poziom",
        "h_shows": "Pokazuje",
        "levels_note": "Zdjęcie pomieszczenia technicznego z urządzeniami na żywo to pełnoprawne akwarium `static`.",
        "m6": "KH zmienia się zbyt szybko|Dwa kolejne testy KH różnią się o więcej niż 0,5 dKH",
        "mon_kh": "Z encją testów KH (np. ostatnim pomiarem głowicy ReefDose) niedawny test odróżnia rzeczywisty spadek KH od wpływu CO2 lub problemu z sondą (`cause`), a wraz z CO2 daje szacowane KH między dwoma testami.",
        "e_kh": "Szacowane KH między dwoma testami (wymaga testu i CO2)",
        "mon_title": "Monitorowanie wody",
        "mon_body": "ReefTank porównuje akwarium z jego własną niedawną historią, a nie z uniwersalnymi limitami, i zgłasza alarmy, gdy odbiega ono od normy. pH i ORP mogą pochodzić z dowolnej encji liczbowej; czujnik CO2 w pomieszczeniu jest opcjonalny. pH nie mierzy KH: te alarmy mówią, kiedy wykonać test.",
        "mon_h_alarm": "Alarm",
        "mon_h_when": "Włącza się, gdy",
        "m1": "pH poniżej zwykłego poziomu|Średnia 24 h jest o 0,1 niższa od mediany z ostatnich 14 dni. Z czujnikiem CO2 `cause` wskazuje, czy wyjaśnia to CO2 w pomieszczeniu",
        "m2": "Wahania pH większe niż zwykle|Amplituda 24 h przekracza zwykłą o 50 %",
        "m3": "Zaburzony dobowy profil pH|Ostatnie 4 godziny odbiegają od zwykłego kształtu doby",
        "m4": "ORP poniżej zwykłego poziomu|ORP bez wpływu pH pozostaje o 30 mV poniżej mediany przez 12 godzin",
        "m5": "Podejrzana sonda|Wartość zamrożona przez 12 godzin, brak wartości przez 2 godziny, powtarzające się piki, skok lub pH i ORP, które przez 2 dni nie poruszają się razem",
        "mon_note": "Alarmy pozostają nieznane przez pierwsze 14 dni, gdy akwarium jest poznawane; tylko podejrzana sonda działa od początku. Wszystkie progi można ustawić.",
        "mon_setup": "Wybierz encje raz. Ta usługa ustawia także progi:",
        "mon_cal": "Z encją kalibracji (datą ostatniej regulacji sondy) kalibracja nie wymaga żadnego działania: odczyty wokół niej są odrzucane, a historia po 24 godzinach podąża za nowym poziomem. Na czas czyszczenia lub podmiany wody włącz przełącznik wstrzymania: wyłączy się sam po 6 godzinach.",
        "e_status": "Stan monitorowania, postęp nauki w atrybutach",
        "e_ph": "Średnia i amplituda 24 h pH",
        "e_orp": "ORP bez dobowego wpływu pH",
        "e_alarms": "Sześć powyższych alarmów",
        "e_pause": "Wstrzymuje analizę",
        "sv_configure": "Wybiera monitorowane encje i progi",
        "sv_reset": "Zapomina historię, aby uczyć się od nowa (nowa sonda)",
        "entities_title": "Encje",
        "entities_body": "Każde akwarium jest urządzeniem z:",
        "h_entity": "Encja",
        "h_state": "Stan",
        "e_fish": "Liczba ryb, według gatunków w atrybutach",
        "e_corals": "Liczba koralowców, według gatunków w atrybutach",
        "e_feeding": "Ostatnie karmienie, z rodzajem (karmnik, skrót, ręczne) i źródłem",
        "e_today": "Karmienia od północy",
        "entities_catalog": "Oraz urządzenie *ReefTank catalog*:",
        "e_update": "Zainstalowana i najnowsza wersja katalogu",
        "e_button": "Od razu sprawdza, czy jest nowa wersja",
        "services_title": "Usługi",
        "h_service": "Usługa",
        "h_effect": "Działanie",
        "sv_feed": "Rejestruje karmienie (karmniki nieznane Home Assistant, skrypty)",
        "sv_add": "Dodaje zwierzęta do inwentarza",
        "sv_remove": "Usuwa zwierzęta (straty, oddanie)",
        "services_note": "`aquarium` to nazwa, id lub id urządzenia akwarium.",
        "catalog_title": "Katalog gatunków",
        "catalog_body": "Ryby, koralowce i tekstury pochodzą z [katalogu ReefTank]({catalog}), pobieranego przy pierwszym uruchomieniu (github.com musi być raz osiągalny), a potem aktualizowanego:",
        "c1": "nowa wersja instaluje się automatycznie; *Ustawienia → Urządzenia i usługi → ReefTank → Konfiguruj* to wyłącza;",
        "c2": "`button.reeftank_catalog_check_for_updates` sprawdza od razu, zamiast czekać na następne sprawdzenie (co 12 godzin);",
        "c3": "pobierane jest tylko to, co się zmieniło, a przerwana aktualizacja zostawia poprzedni katalog bez zmian.",
        "catalog_own": "Własne gatunki umieść w `<config>/reeftank/catalog/` (taki sam układ jak katalog): pojawią się w edytorze bez ponownego uruchamiania.",
        "tech_title": "Dokumentacja techniczna",
        "tech_body": "Model danych, API WebSocket, potok renderowania, zachowanie ryb, format sprite'ów i aktualizacje katalogu: [dokumentacja techniczna]({tech}) (po angielsku).",
        "dev_title": "Rozwój",
        "dev_body": "Testy w pełni pokrywają integrację, a CI tego pilnuje. `scripts/gen_readme.py` generuje tę stronę i jej siedem tłumaczeń: zmieniaj ten skrypt, nie wygenerowane pliki.",
    },
    "pt": {
        "ecosystem_line": f"Parte do [**ecossistema de projetos ReefTech**]({SITE})",
        "languages": "Idiomas disponíveis",
        "intro": (
            "Integração Home Assistant por trás do **cartão de aquário** do "
            f"[ha-reef-card]({CARD}): uma imagem viva do seu aquário, iluminada "
            "pelas suas lâmpadas reais, povoada de peixes e corais animados, e "
            "com os seus dispositivos e entidades."
        ),
        "intro2": (
            "Guarda os aquários, as suas imagens e a sua fauna, regista as "
            "alimentações e mantém o catálogo de espécies atualizado. Nada de "
            "específico de uma marca: funciona com Red Sea, Aqua Medic ou "
            "qualquer outro equipamento que o Home Assistant conheça."
        ),
        "preview": "O cartão de aquário",
        "features_title": "Funcionalidades",
        "f1": "**A sua foto, viva**: contorne a água numa foto do aquário e o cartão anima-a",
        "f2": "**Luz real**: a água ganha a cor e a intensidade das suas lâmpadas (ReefLED ou qualquer `light`), escurecida à noite mas legível",
        "f3": "**Peixes e corais** do [catálogo ReefTank]({catalog}): cardumes, nadadores de águas abertas, peixes de areia, gobies a espreitar da toca, corais a ondular com as bombas",
        "f4": "**Profundidade**: os peixes passam por trás das rochas contornadas e repousam na areia à noite",
        "f5": "**Aquário desenhado**: sem uma boa foto da água? Desenhe-a (água, areia, texturas de rocha) mantendo o resto da foto",
        "f6": "**Dispositivos e entidades** na imagem, clicáveis; zonas que abrem outra imagem (a sump no móvel)",
        "f7": "**Alimentação**: alimentadores, atalhos Red Sea ou um serviço registam cada alimentação; os peixes correm para o ponto de alimentação",
        "f8": "**Inventário**: número de peixes e corais como sensores, com o seu histórico",
        "install_title": "Instalação",
        "install_direct_title": "Instalação direta",
        "install_direct_body": "Clique aqui para abrir o repositório diretamente no HACS e clique em «Transferir»:",
        "install_search_title": "Pesquisa no HACS",
        "install_search_body": "Ou adicione `{repo}` como repositório personalizado (Integração) e pesquise «ReefTank».",
        "install_add": "Reinicie o Home Assistant e adicione a integração (uma única entrada, nada a configurar):",
        "install_card": "O cartão de aquário vem com o [ha-reef-card]({card}), a instalar também.",
        "start_title": "Primeiros passos",
        "s1": "Adicione um **Reef Aquarium Card** a um painel (`custom:reef-aquarium-card`).",
        "s2": "No seu editor, crie um aquário (**{new}**) e depois **{edit}**.",
        "s3": "**{views}**: envie uma foto do aquário, contorne a água, trace a linha da areia e as rochas.",
        "s4": "**{devices}** e **{lights}**: coloque os seus dispositivos e entidades na imagem, posicione as lâmpadas.",
        "s5": "**{livestock}**: adicione os seus peixes e corais e guarde.",
        "start_note": "A configuração do cartão só contém o id do aquário; tudo o resto é guardado pela integração:",
        "editor_title": "O editor de cena",
        "editor_body": "Uma janela em ecrã inteiro, aberta a partir do editor do cartão, com seis separadores:",
        "h_tab": "Separador",
        "h_what": "O que se faz lá",
        "w_aquarium": "Nome, dimensões, o aquário da nuvem correspondente, luz com que as fotos foram tiradas, nível de renderização, escuridão da água à noite",
        "w_views": "As imagens; para cada água: contorno, linha da areia (frente e fundo), rochas e a sua profundidade, zonas clicáveis, fundo desenhado e as suas texturas",
        "w_devices": "Os seus dispositivos e entidades por piso e divisão, arrastados para a imagem",
        "w_lights": "As lâmpadas que iluminam cada água e a sua posição; as bombas que movem a água",
        "w_livestock": "Peixes (espécie, número, tamanho, abrigo) e corais (espécie, tamanho, cores, posição)",
        "w_feeding": "As entidades que registam uma alimentação, e onde cai a comida",
        "levels_title": "Níveis de renderização",
        "levels_body": "Cada aquário é mostrado num de três níveis; um cartão pode baixá-lo, por exemplo num tablet de parede lento:",
        "h_level": "Nível",
        "h_shows": "Mostra",
        "levels_note": "Uma foto da sala técnica com os dispositivos em direto é um aquário `static` perfeitamente válido.",
        "m6": "KH a variar demasiado depressa|Dois testes de KH seguidos diferem mais de 0,5 dKH",
        "mon_kh": "Com uma entidade de testes de KH (a última medida de uma cabeça ReefDose, por exemplo), um teste recente distingue uma descida real do KH de um efeito do CO2 ou de um problema de sonda (`cause`) e, com o CO2, dá um KH estimado entre dois testes.",
        "e_kh": "KH estimado entre dois testes (precisa de um teste e do CO2)",
        "mon_title": "Monitorização da água",
        "mon_body": "O ReefTank compara o aquário com o seu próprio histórico recente, em vez de limites universais, e lança alarmes quando se afasta do habitual. O pH e o ORP podem vir de qualquer entidade numérica; um sensor de CO2 na divisão é opcional. O pH não mede o KH: estes alarmes dizem-lhe quando fazer um teste.",
        "mon_h_alarm": "Alarme",
        "mon_h_when": "Dispara quando",
        "m1": "pH abaixo do nível habitual|A média de 24 h fica 0,1 abaixo da mediana dos últimos 14 dias. Com um sensor de CO2, `cause` indica se o CO2 da divisão o explica",
        "m2": "Amplitude do pH maior do que o habitual|A amplitude de 24 h excede a habitual em 50 %",
        "m3": "Perfil diário do pH alterado|As últimas 4 horas afastam-se da forma habitual do dia",
        "m4": "ORP abaixo do nível habitual|O ORP, sem o efeito do pH, fica 30 mV abaixo da mediana durante 12 horas",
        "m5": "Sonda suspeita|Valor congelado durante 12 horas, nenhum valor durante 2 horas, picos repetidos, um salto, ou pH e ORP que deixam de se mover juntos durante 2 dias",
        "mon_note": "Os alarmes ficam desconhecidos nos primeiros 14 dias, enquanto o aquário é aprendido; só a sonda suspeita funciona desde o início. Todos os limiares são ajustáveis.",
        "mon_setup": "Escolha as entidades uma vez. Este serviço também define os limiares:",
        "mon_cal": "Com uma entidade de calibração (a data do último ajuste da sonda), uma calibração não exige qualquer ação: as leituras à volta são descartadas e o histórico segue o novo nível após 24 horas. Para uma limpeza ou uma mudança de água, ligue o interruptor de pausa: desliga-se sozinho após 6 horas.",
        "e_status": "Estado da monitorização, progresso da aprendizagem nos atributos",
        "e_ph": "Média e amplitude de 24 h do pH",
        "e_orp": "ORP sem o efeito diário do pH",
        "e_alarms": "Os seis alarmes acima",
        "e_pause": "Suspende a análise",
        "sv_configure": "Escolhe as entidades monitorizadas e os limiares",
        "sv_reset": "Esquece o histórico para voltar a aprender (sonda nova)",
        "entities_title": "Entidades",
        "entities_body": "Cada aquário é um dispositivo com:",
        "h_entity": "Entidade",
        "h_state": "Estado",
        "e_fish": "Número de peixes, por espécie nos atributos",
        "e_corals": "Número de corais, por espécie nos atributos",
        "e_feeding": "Última alimentação, com o tipo (alimentador, atalho, manual) e a fonte",
        "e_today": "Alimentações desde a meia-noite",
        "entities_catalog": "E o dispositivo *ReefTank catalog*:",
        "e_update": "Versão do catálogo instalada e mais recente",
        "e_button": "Verifica de imediato se há uma versão nova",
        "services_title": "Serviços",
        "h_service": "Serviço",
        "h_effect": "Efeito",
        "sv_feed": "Regista uma alimentação (alimentadores desconhecidos do Home Assistant, scripts)",
        "sv_add": "Adiciona animais ao inventário",
        "sv_remove": "Retira animais (perdas, cedências)",
        "services_note": "`aquarium` é o nome, o id ou o id de dispositivo do aquário.",
        "catalog_title": "Catálogo de espécies",
        "catalog_body": "Peixes, corais e texturas vêm do [catálogo ReefTank]({catalog}), transferido no primeiro arranque (o github.com tem de estar acessível uma vez) e depois mantido atualizado:",
        "c1": "uma versão nova instala-se automaticamente; *Definições → Dispositivos e serviços → ReefTank → Configurar* desativa-o;",
        "c2": "`button.reeftank_catalog_check_for_updates` verifica de imediato em vez de esperar pela próxima verificação (a cada 12 horas);",
        "c3": "só é transferido o que mudou, e uma atualização interrompida deixa o catálogo anterior no lugar.",
        "catalog_own": "As suas próprias espécies vão para `<config>/reeftank/catalog/` (mesma organização do catálogo): aparecem no editor sem reiniciar.",
        "tech_title": "Referência técnica",
        "tech_body": "Modelo de dados, API WebSocket, cadeia de renderização, comportamento dos peixes, formato dos sprites e atualizações do catálogo: [referência técnica]({tech}) (em inglês).",
        "dev_title": "Desenvolvimento",
        "dev_body": "Os testes cobrem toda a integração e a CI garante-o. `scripts/gen_readme.py` regenera esta página e as suas sete traduções: é ele que se altera, não os ficheiros gerados.",
    },
}

# Labels of the card's scene editor, as the card shows them. The card has no
# Dutch locale yet: the Dutch page uses the English labels, which is what a
# Dutch user sees.
UI: dict[str, dict[str, str]] = {
    "en": {
        "new": "New aquarium",
        "edit": "Edit the scene",
        "aquarium": "Aquarium",
        "views": "Views",
        "devices": "Devices",
        "lights": "Light & flow",
        "livestock": "Livestock",
        "feeding": "Feeding",
        "static": "Static: picture, devices and entities",
        "light": "Light: plus the colour of the lamps",
        "full": "Full: plus fish and corals",
    },
    "fr": {
        "new": "Nouvel aquarium",
        "edit": "Éditer la scène",
        "aquarium": "Aquarium",
        "views": "Vues",
        "devices": "Appareils",
        "lights": "Lumière et brassage",
        "livestock": "Population",
        "feeding": "Nourrissage",
        "static": "Statique : image, appareils et entités",
        "light": "Lumière : plus la couleur des lampes",
        "full": "Complet : plus poissons et coraux",
    },
    "de": {
        "new": "Neues Aquarium",
        "edit": "Szene bearbeiten",
        "aquarium": "Aquarium",
        "views": "Ansichten",
        "devices": "Geräte",
        "lights": "Licht & Strömung",
        "livestock": "Besatz",
        "feeding": "Fütterung",
        "static": "Statisch: Bild, Geräte und Entitäten",
        "light": "Licht: plus die Farbe der Lampen",
        "full": "Voll: plus Fische und Korallen",
    },
    "es": {
        "new": "Nuevo acuario",
        "edit": "Editar la escena",
        "aquarium": "Acuario",
        "views": "Vistas",
        "devices": "Dispositivos",
        "lights": "Luz y corriente",
        "livestock": "Fauna",
        "feeding": "Alimentación",
        "static": "Estático: imagen, dispositivos y entidades",
        "light": "Luz: más el color de las lámparas",
        "full": "Completo: más peces y corales",
    },
    "it": {
        "new": "Nuovo acquario",
        "edit": "Modifica la scena",
        "aquarium": "Acquario",
        "views": "Viste",
        "devices": "Dispositivi",
        "lights": "Luce e corrente",
        "livestock": "Fauna",
        "feeding": "Alimentazione",
        "static": "Statico: immagine, dispositivi ed entità",
        "light": "Luce: più il colore delle lampade",
        "full": "Completo: più pesci e coralli",
    },
    "pl": {
        "new": "Nowe akwarium",
        "edit": "Edytuj scenę",
        "aquarium": "Akwarium",
        "views": "Widoki",
        "devices": "Urządzenia",
        "lights": "Światło i przepływ",
        "livestock": "Obsada",
        "feeding": "Karmienie",
        "static": "Statyczny: obraz, urządzenia i encje",
        "light": "Światło: plus kolor lamp",
        "full": "Pełny: plus ryby i koralowce",
    },
    "pt": {
        "new": "Novo aquário",
        "edit": "Editar a cena",
        "aquarium": "Aquário",
        "views": "Vistas",
        "devices": "Dispositivos",
        "lights": "Luz e corrente",
        "livestock": "Fauna",
        "feeding": "Alimentação",
        "static": "Estático: imagem, dispositivos e entidades",
        "light": "Luz: mais a cor das lâmpadas",
        "full": "Completo: mais peixes e corais",
    },
}
UI["nl"] = UI["en"]

ECOSYSTEM_START = "<!-- ecosystem:start -->"
ECOSYSTEM_END = "<!-- ecosystem:end -->"


def language_bar(current: str) -> str:
    """The flag row, with the current language shown but not linked."""
    parts = []
    for flag, code, path in LANGS:
        img = (
            f'<img src="https://flagicons.lipis.dev/flags/4x3/{flag}.svg" width="5%"/>'
        )
        parts.append(img if code == current else f"[{img}]({REPO}/blob/main/{path})")
    return " ".join(parts)


class _Keep(dict[str, str]):
    """Format mapping leaving the placeholders it does not know in place."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def fill(text: str) -> str:
    """Resolve the links shared by every language."""
    return text.format_map(_Keep(catalog=CATALOG, card=CARD, repo=REPO))


def render(code: str) -> str:
    """The whole page in one language."""
    t = {key: fill(value) for key, value in T[code].items()}
    ui = UI[code]
    root = "" if code == "en" else "../../"
    icon = "icon.png" if code == "en" else f"{REPO}/raw/main/icon.png"
    steps = [
        t["s1"],
        t["s2"].format(new=ui["new"], edit=ui["edit"]),
        t["s3"].format(views=ui["views"]),
        t["s4"].format(devices=ui["devices"], lights=ui["lights"]),
        t["s5"].format(livestock=ui["livestock"]),
    ]
    tabs = [
        ("aquarium", "w_aquarium"),
        ("views", "w_views"),
        ("devices", "w_devices"),
        ("lights", "w_lights"),
        ("livestock", "w_livestock"),
        ("feeding", "w_feeding"),
    ]
    features = "\n".join(f"- {t[f'f{i}']}" for i in range(1, 9))
    start = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    tab_rows = "\n".join(f"| **{ui[tab]}** | {t[what]} |" for tab, what in tabs)
    level_rows = "\n".join(
        f"| **{name.strip()}** (`{level}`) | {shows.strip()} |"
        for level in ("static", "light", "full")
        for name, shows in [ui[level].split(":", 1)]
    )
    alarm_rows = "\n".join(
        f"| **{name}** | {when} |"
        for i in range(1, 7)
        for name, when in [t[f"m{i}"].split("|", 1)]
    )
    return f"""# ReefTank 🐟
> {t["ecosystem_line"]}
<p align="center">
  <img src="{icon}"  width="50%"/>
</p>

{BADGES}

# {t["languages"]}: {language_bar(code)}

{t["intro"]}

{t["intro2"]}

<p align="center">
  <img src="{root}{PREVIEW}" width="80%" alt="{t["preview"]}"/>
</p>

## {t["features_title"]}

{features}

## {t["install_title"]}

### {t["install_direct_title"]}

{t["install_direct_body"]} {HACS_BADGE}

### {t["install_search_title"]}

{t["install_search_body"]}

{t["install_add"]} {FLOW_BADGE}

{t["install_card"]}

## {t["start_title"]}

{start}

{t["start_note"]}

{CARD_YAML}

## {t["editor_title"]}

{t["editor_body"]}

| {t["h_tab"]} | {t["h_what"]} |
|---|---|
{tab_rows}

## {t["levels_title"]}

{t["levels_body"]}

| {t["h_level"]} | {t["h_shows"]} |
|---|---|
{level_rows}

{t["levels_note"]}

## {t["mon_title"]}

{t["mon_body"]}

| {t["mon_h_alarm"]} | {t["mon_h_when"]} |
|---|---|
{alarm_rows}

{t["mon_note"]}

{t["mon_setup"]}

{MONITORING_YAML}

{t["mon_kh"]}

{t["mon_cal"]}

## {t["entities_title"]}

{t["entities_body"]}

| {t["h_entity"]} | {t["h_state"]} |
|---|---|
| `sensor.<aquarium>_fish` | {t["e_fish"]} |
| `sensor.<aquarium>_corals` | {t["e_corals"]} |
| `event.<aquarium>_feeding` | {t["e_feeding"]} |
| `sensor.<aquarium>_feedings_today` | {t["e_today"]} |
| `sensor.<aquarium>_water_monitoring` | {t["e_status"]} |
| `sensor.<aquarium>_ph_24_h_mean`, `sensor.<aquarium>_ph_swing_24_h` | {t["e_ph"]} |
| `sensor.<aquarium>_orp_without_the_ph_effect` | {t["e_orp"]} |
| `sensor.<aquarium>_kh_estimated` | {t["e_kh"]} |
| `binary_sensor.<aquarium>_*` | {t["e_alarms"]} |
| `switch.<aquarium>_pause_monitoring` | {t["e_pause"]} |

{t["entities_catalog"]}

| {t["h_entity"]} | {t["h_state"]} |
|---|---|
| `update.reeftank_catalog` | {t["e_update"]} |
| `button.reeftank_catalog_check_for_updates` | {t["e_button"]} |

## {t["services_title"]}

| {t["h_service"]} | {t["h_effect"]} |
|---|---|
| `reeftank.feed` | {t["sv_feed"]} |
| `reeftank.livestock_add` | {t["sv_add"]} |
| `reeftank.livestock_remove` | {t["sv_remove"]} |
| `reeftank.monitoring_configure` | {t["sv_configure"]} |
| `reeftank.monitoring_reset` | {t["sv_reset"]} |

{t["services_note"]}

{SERVICE_YAML}

## {t["catalog_title"]}

{t["catalog_body"]}

- {t["c1"]}
- {t["c2"]}
- {t["c3"]}

{t["catalog_own"]}

## {t["tech_title"]}

{t["tech_body"].format(tech=root + TECH)}

## {t["dev_title"]}

{t["dev_body"]}

{DEV_SH}
"""


def preserve_ecosystem(existing: str, generated: str) -> str:
    """Carry an existing "Related projects" block into the new content.

    That block is written by reeftank/scripts/gen_ecosystem.py, which lives in
    another repository and is not available in CI. It goes back where
    gen_ecosystem puts it: before the first second-level heading.
    """
    start = existing.find(ECOSYSTEM_START)
    end = existing.find(ECOSYSTEM_END)
    if start == -1 or end == -1:
        return generated
    block = existing[start : end + len(ECOSYSTEM_END)]
    at = generated.find("\n## ")
    return generated[: at + 1] + block + "\n\n" + generated[at + 1 :]


def main(argv: list[str]) -> int:
    """Write the pages, or with --check, report those out of date."""
    missing = [
        (code, key) for _, code, _ in LANGS for key in T["en"] if key not in T[code]
    ]
    if missing:
        raise SystemExit(f"untranslated keys: {missing}")

    check = "--check" in argv
    stale = []
    for _, code, path in LANGS:
        target = Path(path)
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        content = preserve_ecosystem(existing, render(code))
        if content == existing:
            continue
        stale.append(path)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print("written", path)
    if check and stale:
        print("out of date:", ", ".join(stale))
        return 1
    if not stale:
        print("READMEs up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
