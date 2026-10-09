# v0.1.0

First version.

- Aquarium documents (waters, views, decor, elements, hotspots, livestock,
  corals, feeding sources), validated and stored in `.storage/reeftank`,
  with revisions to refuse overwriting a newer document.
- Background pictures uploaded over HTTP, normalised (orientation applied,
  metadata stripped, long edge capped, WebP) and cleaned up when no longer
  used.
- Asset catalog: the species downloaded from the
  [reeftank-catalog](https://github.com/Elwinmage/reeftank-catalog) releases
  (`<config>/reeftank/pack/`) plus `<config>/reeftank/catalog/`, merged (user
  entries win). No species ship with the integration.
- Catalog updates: `update.reeftank_catalog` checks the latest release every
  12 hours and installs it automatically (option to install on demand);
  incremental (sha256 per entry), checked archives, atomic swap, minimum
  integration version honoured, pack downloaded again when its files are
  missing. `reeftank/catalog/subscribe` tells the cards.
- Ids start with a letter (an all-digit id is reordered by JavaScript).
- WebSocket API: list, get, subscribe, save, delete, catalog.
- One device per aquarium: fish and coral count sensors (count per species
  as attributes), feedings of the day, feeding event.
- Feeding sources watched server side, merged within a delay.
- Services: `reeftank.feed`, `reeftank.livestock_add`,
  `reeftank.livestock_remove`.
- Sprite atlases are built by `scripts/build_atlas.py` of reeftank-catalog.
- Works with Home Assistant 2026.10: schemas from probatio when it is
  there (voluptuous before), `StaticPathConfig` from `http.server`, devices
  looked up without the deprecated `async_get_device(identifiers=...)`
  (`compat.py`).
