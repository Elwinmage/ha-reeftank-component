# v0.1.0

First version.

- Aquarium documents (waters, views, decor, elements, hotspots, livestock,
  corals, feeding sources), validated and stored in `.storage/reeftank`,
  with revisions to refuse overwriting a newer document.
- Background pictures uploaded over HTTP, normalised (orientation applied,
  metadata stripped, long edge capped, WebP) and cleaned up when no longer
  used.
- Asset catalog: bundled entries plus `<config>/reeftank/catalog/`, merged.
  Two demo species drawn by `scripts/make_demo_assets.py`.
- WebSocket API: list, get, subscribe, save, delete, catalog.
- One device per aquarium: fish and coral count sensors (count per species
  as attributes), feedings of the day, feeding event.
- Feeding sources watched server side, merged within a delay.
- Services: `reeftank.feed`, `reeftank.livestock_add`,
  `reeftank.livestock_remove`.
- `scripts/build_atlas.py`: sprite atlases and descriptors from clips.
