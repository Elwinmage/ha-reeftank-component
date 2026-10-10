# ReefTank 🐟
> Parte dell'[**ecosistema di progetti ReefTech**](https://elwinmage.github.io/reeftank/)
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

# Lingue disponibili: [<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/README.md) [<img src="https://flagicons.lipis.dev/flags/4x3/fr.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/fr/README.fr.md) [<img src="https://flagicons.lipis.dev/flags/4x3/de.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/de/README.de.md) [<img src="https://flagicons.lipis.dev/flags/4x3/es.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/es/README.es.md) <img src="https://flagicons.lipis.dev/flags/4x3/it.svg" width="5%"/> [<img src="https://flagicons.lipis.dev/flags/4x3/nl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/nl/README.nl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pl/README.pl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pt.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pt/README.pt.md)

Integrazione Home Assistant dietro la **scheda acquario** di [ha-reef-card](https://github.com/Elwinmage/ha-reef-card): un'immagine viva della vostra vasca, illuminata dalle vostre vere lampade, popolata di pesci e coralli animati, con sopra i vostri dispositivi ed entità.

Conserva gli acquari, le loro immagini e la loro fauna, registra le alimentazioni e tiene aggiornato il catalogo delle specie. Niente di legato a una marca: funziona con Red Sea, Aqua Medic o qualsiasi altra apparecchiatura nota a Home Assistant.

<p align="center">
  <img src="../../doc/img/preview.webp" width="80%" alt="La scheda acquario"/>
</p>

<!-- ecosystem:start -->

## Progetti correlati

I progetti ReefTech si incastrano tra loro: le integrazioni portano la tua attrezzatura in Home Assistant, la scheda la mostra e la pilota, e il backup la mantiene in funzione durante un blackout. Ognuno funziona anche da solo.

<table>
  <tr>
    <th width="100px"></th>
    <th>Progetto</th>
    <th>Ruolo</th>
    <th>Funziona con</th>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/main/icon.png" width="64" alt="ha-reefbeat-component" /></td>
    <td>🐠<br /><a href="https://github.com/Elwinmage/ha-reefbeat-component"><b>ha-reefbeat-component</b></a></td>
    <td>Dispositivi Red Sea ReefBeat, pilotati in locale senza cloud: ReefATO+, ReefControl, ReefControl-Power, ReefDose, ReefLed, ReefMat, ReefRun e ReefWave.<br />blueprint di allerta per modalità anomale, calibrazioni e batteria scarica. <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/refs/heads/main/blueprints/automation/redsea_alerts.en.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a></td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-aquamedic-component/main/icon.png" width="64" alt="ha-aquamedic-component" /></td>
    <td>🌊<br /><a href="https://github.com/Elwinmage/ha-aquamedic-component"><b>ha-aquamedic-component</b></a></td>
    <td>Pompe Aqua Medic tramite l'API cloud Gizwits: pompe di movimento EcoDrift e SmartDrift, pompe DC Runner di risalita e dello schiumatoio.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-maintenance-component/main/icon.png" width="64" alt="ha-reef-maintenance-component" /></td>
    <td>🐙<br /><a href="https://github.com/Elwinmage/ha-reef-maintenance-component"><b>ha-reef-maintenance-component</b></a></td>
    <td>Tracciamento di pulizia e usura per l'attrezzatura che Home Assistant non può interrogare: pompe di movimento, pompe di risalita, schiumatoi, reattori, tutto ciò che curi a mano.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-card/main/icon.png" width="64" alt="ha-reef-card" /></td>
    <td>🪸<br /><a href="https://github.com/Elwinmage/ha-reef-card"><b>ha-reef-card</b></a></td>
    <td>Vista grafica interattiva di ogni dispositivo sulla tua dashboard, e unico modo per modificare le programmazioni avanzate. Legge le tre integrazioni tramite il contratto <code>reef_role</code> comune, senza configurazione lato scheda. Disegna anche i flussi di energia di reefbeatEnergyBackup. La sua scheda acquario dà vita alla vostra vasca con ha-reeftank-component.</td>
    <td>tutte e tre le integrazioni, e ha-reeftank-component per l'acquario</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/icon.png" width="64" alt="ha-reeftank-component" /></td>
    <td>🐟<br /><b>ha-reeftank-component</b><br /><i>(questo repository)</i></td>
    <td>Un'immagine viva della vostra vasca sulla plancia: la vostra foto, illuminata dalle vostre vere lampade, con pesci e coralli animati, e sopra i vostri dispositivi ed entità. Conserva gli acquari e la loro fauna, registra le alimentazioni.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reeftank-catalog/main/icon.png" width="64" alt="reeftank-catalog" /></td>
    <td>🐡<br /><a href="https://github.com/Elwinmage/reeftank-catalog"><b>reeftank-catalog</b></a></td>
    <td>Pesci, coralli e texture della scheda acquario, scaricati e tenuti aggiornati da ha-reeftank-component.</td>
    <td>ha-reeftank-component</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-blueprints/main/icon.png" width="64" alt="ha-reef-blueprints" /></td>
    <td>🐬<br /><a href="https://github.com/Elwinmage/ha-reef-blueprints"><b>ha-reef-blueprints</b></a></td>
    <td>Blueprint di notifica comuni a tutto l'ecosistema: manutenzioni scadute trovate tramite il contratto <code>reef_role</code>, e dispositivi diventati irraggiungibili. Otto lingue.</td>
    <td>tutte e tre le integrazioni</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reefbeatEnergyBackup/main/icon.png" width="64" alt="reefbeatEnergyBackup" /></td>
    <td>⚡<br /><a href="https://github.com/Elwinmage/reefbeatEnergyBackup"><b>reefbeatEnergyBackup</b></a></td>
    <td>Backup a batteria in caso di blackout. Un pacco 24V LiFePO₄ gestito da un Raspberry Pi, con degrado progressivo della velocità delle pompe in base allo stato di carica.</td>
    <td>da solo, o insieme a ha-reefbeat-component e ha-reef-card</td>
  </tr>
</table>

Sono tutti documentati insieme sulla [pagina del progetto ReefTech](https://elwinmage.github.io/reeftank/).

<!-- ecosystem:end -->

## Funzionalità

- **La vostra foto, viva**: contornate l'acqua su una foto della vasca, la scheda la anima
- **Luce reale**: l'acqua prende colore e intensità delle vostre lampade (ReefLED o qualsiasi `light`), scurita di notte ma leggibile
- **Pesci e coralli** dal [catalogo ReefTank](https://github.com/Elwinmage/reeftank-catalog): banchi, nuotatori di acque libere, pesci di sabbia, ghiozzi che spuntano dalla tana, coralli che ondeggiano con le pompe
- **Profondità**: i pesci passano dietro le rocce contornate e di notte riposano sulla sabbia
- **Vasca disegnata**: nessuna bella foto dell'acqua? Disegnatela (acqua, sabbia, texture di roccia) tenendo il resto della foto
- **Dispositivi ed entità** sull'immagine, cliccabili; zone che aprono un'altra immagine (la sump nel mobile)
- **Alimentazione**: alimentatori, scorciatoie Red Sea o un servizio registrano ogni alimentazione; i pesci accorrono al punto di alimentazione
- **Inventario**: numero di pesci e coralli come sensori, con la loro cronologia

## Installazione

### Installazione diretta

Fate clic qui per aprire il repository direttamente in HACS, poi su «Scarica»: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Elwinmage&repository=ha-reeftank-component&category=integration)

### Ricerca in HACS

Oppure aggiungete `https://github.com/Elwinmage/ha-reeftank-component` come repository personalizzato (Integrazione) e cercate «ReefTank».

Riavviate Home Assistant, poi aggiungete l'integrazione (una sola voce, niente da configurare): [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)

La scheda acquario arriva con [ha-reef-card](https://github.com/Elwinmage/ha-reef-card), da installare anch'essa.

## Primi passi

1. Aggiungete una **Reef Aquarium Card** a una plancia (`custom:reef-aquarium-card`).
2. Nel suo editor, create un acquario (**Nuovo acquario**), poi **Modifica la scena**.
3. **Viste**: caricate una foto della vasca, contornate l'acqua, tracciate la linea della sabbia e le rocce.
4. **Dispositivi** e **Luce e corrente**: posate dispositivi ed entità sull'immagine, posizionate le lampade.
5. **Fauna**: aggiungete pesci e coralli, poi salvate.

La configurazione della scheda contiene solo l'id dell'acquario; tutto il resto è conservato dall'integrazione:

```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```

## L'editor di scena

Una finestra a schermo intero, aperta dall'editor della scheda, con sei schede:

| Scheda | Cosa si fa |
|---|---|
| **Acquario** | Nome, dimensioni, l'acquario cloud corrispondente, luce con cui sono state scattate le foto, livello di resa |
| **Viste** | Le immagini; per ogni acqua: contorno, linea della sabbia (davanti e dietro), rocce e loro profondità, zone cliccabili, sfondo disegnato e sue texture |
| **Dispositivi** | I vostri dispositivi ed entità per piano e area, trascinati sull'immagine |
| **Luce e corrente** | Le lampade che illuminano ogni acqua e la loro posizione; le pompe che muovono l'acqua |
| **Fauna** | Pesci (specie, numero, taglia, rifugio) e coralli (specie, taglia, colori, posizione) |
| **Alimentazione** | Le entità che registrano un'alimentazione, e dove cade il cibo |

## Livelli di resa

Ogni acquario è reso a uno di tre livelli; una scheda può abbassarlo, ad esempio su un tablet a muro lento:

| Livello | Mostra |
|---|---|
| **Statico** (`static`) | immagine, dispositivi ed entità |
| **Luce** (`light`) | più il colore delle lampade |
| **Completo** (`full`) | più pesci e coralli |

Una foto del locale tecnico con i dispositivi in tempo reale è un ottimo acquario `static`.

## Entità

Ogni acquario è un dispositivo con:

| Entità | Stato |
|---|---|
| `sensor.<aquarium>_fish` | Numero di pesci, per specie negli attributi |
| `sensor.<aquarium>_corals` | Numero di coralli, per specie negli attributi |
| `event.<aquarium>_feeding` | Ultima alimentazione, con tipo (alimentatore, scorciatoia, manuale) e fonte |
| `sensor.<aquarium>_feedings_today` | Alimentazioni dalla mezzanotte |

E il dispositivo *ReefTank catalog*:

| Entità | Stato |
|---|---|
| `update.reeftank_catalog` | Versione del catalogo installata e ultima pubblicata |
| `button.reeftank_catalog_check_for_updates` | Controlla subito se c'è una nuova versione |

## Servizi

| Servizio | Effetto |
|---|---|
| `reeftank.feed` | Registra un'alimentazione (alimentatori sconosciuti a Home Assistant, script) |
| `reeftank.livestock_add` | Aggiunge animali all'inventario |
| `reeftank.livestock_remove` | Rimuove animali (perdite, cessioni) |

`aquarium` è il nome, l'id o l'id del dispositivo dell'acquario.

```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```

## Catalogo delle specie

Pesci, coralli e texture provengono dal [catalogo ReefTank](https://github.com/Elwinmage/reeftank-catalog), scaricato al primo avvio (github.com deve essere raggiungibile una volta) e poi tenuto aggiornato:

- una nuova versione si installa automaticamente; *Impostazioni → Dispositivi e servizi → ReefTank → Configura* lo disattiva;
- `button.reeftank_catalog_check_for_updates` controlla subito invece di attendere il prossimo controllo (ogni 12 ore);
- si scarica solo ciò che è cambiato, e un aggiornamento interrotto lascia il catalogo precedente al suo posto.

Le vostre specie vanno in `<config>/reeftank/catalog/` (stessa struttura del catalogo): compaiono nell'editor senza riavviare.

## Riferimento tecnico

Modello dei dati, API WebSocket, pipeline di resa, comportamento dei pesci, formato degli sprite e aggiornamenti del catalogo: [riferimento tecnico](../../doc/en/technical.md) (in inglese).

## Sviluppo

I test coprono interamente l'integrazione e la CI lo garantisce. `scripts/gen_readme.py` rigenera questa pagina e le sue sette traduzioni: va modificato lui, non i file generati.

```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```
