# Bundled catalog

One folder per entry, named after its id:

- `fish/<id>/species.json` + atlas;
- `corals/<id>/species.json` + shade and mask atlases;
- `presets/<id>/preset.json` + view pictures.

Build atlases with `scripts/build_atlas.py`. The `demo_*` species are drawn by
`scripts/make_demo_assets.py`. See the main README, §10 to §14.
