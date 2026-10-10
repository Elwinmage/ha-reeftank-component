# ReefTank 🐟
> Parte do [**ecossistema de projetos ReefTech**](https://elwinmage.github.io/reeftank/)
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

# Idiomas disponíveis: [<img src="https://flagicons.lipis.dev/flags/4x3/gb.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/README.md) [<img src="https://flagicons.lipis.dev/flags/4x3/fr.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/fr/README.fr.md) [<img src="https://flagicons.lipis.dev/flags/4x3/de.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/de/README.de.md) [<img src="https://flagicons.lipis.dev/flags/4x3/es.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/es/README.es.md) [<img src="https://flagicons.lipis.dev/flags/4x3/it.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/it/README.it.md) [<img src="https://flagicons.lipis.dev/flags/4x3/nl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/nl/README.nl.md) [<img src="https://flagicons.lipis.dev/flags/4x3/pl.svg" width="5%"/>](https://github.com/Elwinmage/ha-reeftank-component/blob/main/doc/pl/README.pl.md) <img src="https://flagicons.lipis.dev/flags/4x3/pt.svg" width="5%"/>

Integração Home Assistant por trás do **cartão de aquário** do [ha-reef-card](https://github.com/Elwinmage/ha-reef-card): uma imagem viva do seu aquário, iluminada pelas suas lâmpadas reais, povoada de peixes e corais animados, e com os seus dispositivos e entidades.

Guarda os aquários, as suas imagens e a sua fauna, regista as alimentações e mantém o catálogo de espécies atualizado. Nada de específico de uma marca: funciona com Red Sea, Aqua Medic ou qualquer outro equipamento que o Home Assistant conheça.

<p align="center">
  <img src="../../doc/img/preview.webp" width="80%" alt="O cartão de aquário"/>
</p>

<!-- ecosystem:start -->

## Projetos relacionados

Os projetos ReefTech encaixam-se entre si: as integrações trazem o seu equipamento para o Home Assistant, o cartão mostra-o e comanda-o, e o backup mantém-no a funcionar durante um corte. Cada um funciona também sozinho.

<table>
  <tr>
    <th width="100px"></th>
    <th>Projeto</th>
    <th>Função</th>
    <th>Funciona com</th>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/main/icon.png" width="64" alt="ha-reefbeat-component" /></td>
    <td>🐠<br /><a href="https://github.com/Elwinmage/ha-reefbeat-component"><b>ha-reefbeat-component</b></a></td>
    <td>Aparelhos Red Sea ReefBeat, comandados localmente sem cloud: ReefATO+, ReefControl, ReefControl-Power, ReefDose, ReefLed, ReefMat, ReefRun e ReefWave.<br />blueprint de alertas para modos anómalos, calibrações e bateria fraca. <a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://raw.githubusercontent.com/Elwinmage/ha-reefbeat-component/refs/heads/main/blueprints/automation/redsea_alerts.en.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled." /></a></td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-aquamedic-component/main/icon.png" width="64" alt="ha-aquamedic-component" /></td>
    <td>🌊<br /><a href="https://github.com/Elwinmage/ha-aquamedic-component"><b>ha-aquamedic-component</b></a></td>
    <td>Bombas Aqua Medic através da API cloud Gizwits: bombas de circulação EcoDrift e SmartDrift, bombas DC Runner de retorno e do escumador.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-maintenance-component/main/icon.png" width="64" alt="ha-reef-maintenance-component" /></td>
    <td>🐙<br /><a href="https://github.com/Elwinmage/ha-reef-maintenance-component"><b>ha-reef-maintenance-component</b></a></td>
    <td>Acompanhamento da limpeza e do desgaste do equipamento que o Home Assistant não consegue interrogar: bombas de circulação, bombas de retorno, escumadores, reatores, tudo o que trata à mão.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-card/main/icon.png" width="64" alt="ha-reef-card" /></td>
    <td>🪸<br /><a href="https://github.com/Elwinmage/ha-reef-card"><b>ha-reef-card</b></a></td>
    <td>Vista gráfica interativa de cada aparelho no seu painel, e a única forma de editar os programas avançados. Lê as três integrações através do contrato <code>reef_role</code> comum, sem configuração do lado do cartão. Desenha também os fluxos de energia do reefbeatEnergyBackup. O seu cartão de aquário dá vida ao seu aquário com o ha-reeftank-component.</td>
    <td>as três integrações, e o ha-reeftank-component para o aquário</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reeftank-component/main/icon.png" width="64" alt="ha-reeftank-component" /></td>
    <td>🐟<br /><b>ha-reeftank-component</b><br /><i>(este repositório)</i></td>
    <td>Uma imagem viva do seu aquário no painel: a sua foto, iluminada pelas suas lâmpadas reais, com peixes e corais animados, e os seus dispositivos e entidades. Guarda os aquários e a sua fauna, regista as alimentações.</td>
    <td>ha-reef-card</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reeftank-catalog/main/icon.png" width="64" alt="reeftank-catalog" /></td>
    <td>🐡<br /><a href="https://github.com/Elwinmage/reeftank-catalog"><b>reeftank-catalog</b></a></td>
    <td>Peixes, corais e texturas do cartão de aquário, transferidos e mantidos atualizados pelo ha-reeftank-component.</td>
    <td>ha-reeftank-component</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/ha-reef-blueprints/main/icon.png" width="64" alt="ha-reef-blueprints" /></td>
    <td>🐬<br /><a href="https://github.com/Elwinmage/ha-reef-blueprints"><b>ha-reef-blueprints</b></a></td>
    <td>Blueprints de notificação comuns a todo o ecossistema: manutenções em atraso encontradas pelo contrato <code>reef_role</code>, e aparelhos que ficaram inacessíveis. Oito idiomas.</td>
    <td>as três integrações</td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/Elwinmage/reefbeatEnergyBackup/main/icon.png" width="64" alt="reefbeatEnergyBackup" /></td>
    <td>⚡<br /><a href="https://github.com/Elwinmage/reefbeatEnergyBackup"><b>reefbeatEnergyBackup</b></a></td>
    <td>Backup por bateria em caso de corte. Um pack 24V LiFePO₄ comandado por um Raspberry Pi, com degradação progressiva da velocidade das bombas conforme o estado de carga.</td>
    <td>sozinho, ou a par do ha-reefbeat-component e do ha-reef-card</td>
  </tr>
</table>

Estão todos documentados em conjunto na [página do projeto ReefTech](https://elwinmage.github.io/reeftank/).

<!-- ecosystem:end -->

## Funcionalidades

- **A sua foto, viva**: contorne a água numa foto do aquário e o cartão anima-a
- **Luz real**: a água ganha a cor e a intensidade das suas lâmpadas (ReefLED ou qualquer `light`), escurecida à noite mas legível
- **Peixes e corais** do [catálogo ReefTank](https://github.com/Elwinmage/reeftank-catalog): cardumes, nadadores de águas abertas, peixes de areia, gobies a espreitar da toca, corais a ondular com as bombas
- **Profundidade**: os peixes passam por trás das rochas contornadas e repousam na areia à noite
- **Aquário desenhado**: sem uma boa foto da água? Desenhe-a (água, areia, texturas de rocha) mantendo o resto da foto
- **Dispositivos e entidades** na imagem, clicáveis; zonas que abrem outra imagem (a sump no móvel)
- **Alimentação**: alimentadores, atalhos Red Sea ou um serviço registam cada alimentação; os peixes correm para o ponto de alimentação
- **Inventário**: número de peixes e corais como sensores, com o seu histórico

## Instalação

### Instalação direta

Clique aqui para abrir o repositório diretamente no HACS e clique em «Transferir»: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Elwinmage&repository=ha-reeftank-component&category=integration)

### Pesquisa no HACS

Ou adicione `https://github.com/Elwinmage/ha-reeftank-component` como repositório personalizado (Integração) e pesquise «ReefTank».

Reinicie o Home Assistant e adicione a integração (uma única entrada, nada a configurar): [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=reeftank)

O cartão de aquário vem com o [ha-reef-card](https://github.com/Elwinmage/ha-reef-card), a instalar também.

## Primeiros passos

1. Adicione um **Reef Aquarium Card** a um painel (`custom:reef-aquarium-card`).
2. No seu editor, crie um aquário (**Novo aquário**) e depois **Editar a cena**.
3. **Vistas**: envie uma foto do aquário, contorne a água, trace a linha da areia e as rochas.
4. **Dispositivos** e **Luz e corrente**: coloque os seus dispositivos e entidades na imagem, posicione as lâmpadas.
5. **Fauna**: adicione os seus peixes e corais e guarde.

A configuração do cartão só contém o id do aquário; tudo o resto é guardado pela integração:

```yaml
type: custom:reef-aquarium-card
aquarium: a1b2        # set by the card editor
view: front           # optional
render: static        # optional: static, light or full
```

## O editor de cena

Uma janela em ecrã inteiro, aberta a partir do editor do cartão, com seis separadores:

| Separador | O que se faz lá |
|---|---|
| **Aquário** | Nome, dimensões, o aquário da nuvem correspondente, luz com que as fotos foram tiradas, nível de renderização |
| **Vistas** | As imagens; para cada água: contorno, linha da areia (frente e fundo), rochas e a sua profundidade, zonas clicáveis, fundo desenhado e as suas texturas |
| **Dispositivos** | Os seus dispositivos e entidades por piso e divisão, arrastados para a imagem |
| **Luz e corrente** | As lâmpadas que iluminam cada água e a sua posição; as bombas que movem a água |
| **Fauna** | Peixes (espécie, número, tamanho, abrigo) e corais (espécie, tamanho, cores, posição) |
| **Alimentação** | As entidades que registam uma alimentação, e onde cai a comida |

## Níveis de renderização

Cada aquário é mostrado num de três níveis; um cartão pode baixá-lo, por exemplo num tablet de parede lento:

| Nível | Mostra |
|---|---|
| **Estático** (`static`) | imagem, dispositivos e entidades |
| **Luz** (`light`) | mais a cor das lâmpadas |
| **Completo** (`full`) | mais peixes e corais |

Uma foto da sala técnica com os dispositivos em direto é um aquário `static` perfeitamente válido.

## Entidades

Cada aquário é um dispositivo com:

| Entidade | Estado |
|---|---|
| `sensor.<aquarium>_fish` | Número de peixes, por espécie nos atributos |
| `sensor.<aquarium>_corals` | Número de corais, por espécie nos atributos |
| `event.<aquarium>_feeding` | Última alimentação, com o tipo (alimentador, atalho, manual) e a fonte |
| `sensor.<aquarium>_feedings_today` | Alimentações desde a meia-noite |

E o dispositivo *ReefTank catalog*:

| Entidade | Estado |
|---|---|
| `update.reeftank_catalog` | Versão do catálogo instalada e mais recente |
| `button.reeftank_catalog_check_for_updates` | Verifica de imediato se há uma versão nova |

## Serviços

| Serviço | Efeito |
|---|---|
| `reeftank.feed` | Regista uma alimentação (alimentadores desconhecidos do Home Assistant, scripts) |
| `reeftank.livestock_add` | Adiciona animais ao inventário |
| `reeftank.livestock_remove` | Retira animais (perdas, cedências) |

`aquarium` é o nome, o id ou o id de dispositivo do aquário.

```yaml
action: reeftank.livestock_add
data:
  aquarium: Reefer 425
  species: chromis_viridis
  count: 3
```

## Catálogo de espécies

Peixes, corais e texturas vêm do [catálogo ReefTank](https://github.com/Elwinmage/reeftank-catalog), transferido no primeiro arranque (o github.com tem de estar acessível uma vez) e depois mantido atualizado:

- uma versão nova instala-se automaticamente; *Definições → Dispositivos e serviços → ReefTank → Configurar* desativa-o;
- `button.reeftank_catalog_check_for_updates` verifica de imediato em vez de esperar pela próxima verificação (a cada 12 horas);
- só é transferido o que mudou, e uma atualização interrompida deixa o catálogo anterior no lugar.

As suas próprias espécies vão para `<config>/reeftank/catalog/` (mesma organização do catálogo): aparecem no editor sem reiniciar.

## Referência técnica

Modelo de dados, API WebSocket, cadeia de renderização, comportamento dos peixes, formato dos sprites e atualizações do catálogo: [referência técnica](../../doc/en/technical.md) (em inglês).

## Desenvolvimento

Os testes cobrem toda a integração e a CI garante-o. `scripts/gen_readme.py` regenera esta página e as suas sete traduções: é ele que se altera, não os ficheiros gerados.

```bash
pip install -r requirements.test.txt
pytest -q --cov=custom_components.reeftank --cov-config=.coveragerc
ruff check . && ruff format --check .
pyright --project pyrightconfig.json
python3 scripts/check_translation.py
python3 scripts/gen_readme.py
```
