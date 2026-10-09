"""Catalog updates: the update entity, automatic installs, the pack."""

from __future__ import annotations

from typing import Any

import pytest
from conftest import state_of
from homeassistant.components.update import ATTR_IN_PROGRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from release import BASE, publish, release, species

from custom_components.reeftank.compat import find_device
from custom_components.reeftank.const import CATALOG_DEVICE_ID, DOMAIN

ENTITY = "update.reeftank_catalog"


async def _check(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Run a catalog check (as the 12 h timer does) and its install."""
    await entry.runtime_data.updater.coordinator.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_nothing_published(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    state = state_of(hass, ENTITY)
    assert state.state == "off"
    assert state.attributes["installed_version"] == "0"
    assert state.attributes["latest_version"] == "0"
    assert state.attributes["title"] == "ReefTank catalog"
    assert entry.runtime_data.updater.coordinator.last_update_success is False
    assert entry.runtime_data.updater.update_available is False


async def test_automatic_install_and_incremental_update(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    aioclient_mock: Any,
    hass_ws_client: Any,
) -> None:
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "reeftank/catalog/subscribe"})
    assert (await ws.receive_json())["success"]

    manifest, blobs = release(
        "2026.10.0",
        {"fish/siganus": species("siganus"), "fish/anthias": species("anthias")},
    )
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)

    root = entry.runtime_data.pack_root
    assert (root / "fish" / "siganus" / "species.json").is_file()
    state = state_of(hass, ENTITY)
    assert state.state == "off"
    assert state.attributes["installed_version"] == "2026.10.0"
    event = await ws.receive_json()
    assert event["event"] == {"version": "2026.10.0"}

    await ws.send_json_auto_id({"type": "reeftank/catalog"})
    result = (await ws.receive_json())["result"]
    assert [e["id"] for e in result["fish"]] == ["anthias", "siganus"]
    assert result["fish"][0]["atlas"]["1x"] == (
        "/reeftank/catalog/pack/fish/anthias/anthias.webp"
    )
    assert result["pack"] == {"version": "2026.10.0", "updating": False}

    # Next release: one species changed, one removed, one added
    manifest, blobs = release(
        "2026.11.0",
        {
            "fish/siganus": species("siganus"),
            "fish/chromis": species("chromis"),
            "corals/euphyllia": {"species.json": "{}"},
        },
    )
    manifest["entries"]["fish/siganus"] = {
        **manifest["entries"]["fish/siganus"],
        "file": "unchanged.zip",
    }
    # unchanged sha256: the siganus archive is not downloaded again
    previous = entry.runtime_data.updater.installed
    assert previous is not None
    manifest["entries"]["fish/siganus"]["sha256"] = previous.entries[
        "fish/siganus"
    ].sha256
    del blobs["fish-siganus.zip"]
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    urls = [str(call[1]) for call in aioclient_mock.mock_calls]
    assert not any("unchanged" in url or "siganus" in url for url in urls)
    assert not (root / "fish" / "anthias").exists()
    assert (root / "corals" / "euphyllia" / "species.json").is_file()
    assert (root / "fish" / "siganus" / "siganus.webp").is_file()
    assert state_of(hass, ENTITY).attributes["installed_version"] == "2026.11.0"


async def test_manual_install(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    aioclient_mock: Any,
    hass_ws_client: Any,
) -> None:
    # Options: no automatic install
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"auto_update": False}
    )
    assert entry.options == {"auto_update": False}

    manifest, blobs = release("2026.10.0", {"fish/siganus": species("siganus")})
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    state = state_of(hass, ENTITY)
    assert state.state == "on"
    assert state.attributes["latest_version"] == "2026.10.0"
    assert state.attributes["release_url"] == f"{BASE}/tag/2026.10.0"
    assert state.attributes["release_summary"] is None

    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "update/release_notes", "entity_id": ENTITY})
    assert (await ws.receive_json())["result"] == "Release 2026.10.0"

    seen: list[Any] = []
    updater = entry.runtime_data.updater
    remove = updater.async_add_listener(
        lambda: seen.append((updater.in_progress, updater.progress))
    )
    await hass.services.async_call(
        "update", "install", {"entity_id": ENTITY}, blocking=True
    )
    remove()
    assert (True, 0) in seen and (True, 100) in seen
    assert state_of(hass, ENTITY).state == "off"
    assert not state_of(hass, ENTITY).attributes[ATTR_IN_PROGRESS]

    # Automatic again: an immediate check
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {"auto_update": True}
    )
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_incompatible_release(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    aioclient_mock: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manifest, blobs = release(
        "2027.1.0", {"fish/x": species("x")}, min_integration="99.0.0"
    )
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    assert "needs ReefTank 99.0.0" in caplog.text
    state = state_of(hass, ENTITY)
    assert state.state == "on"
    assert state.attributes["release_summary"] == "Needs ReefTank 99.0.0 or newer."
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "update", "install", {"entity_id": ENTITY}, blocking=True
        )
    assert err.value.translation_key == "catalog_incompatible"


async def test_check_on_demand(
    hass: HomeAssistant, entry: MockConfigEntry, aioclient_mock: Any
) -> None:
    """homeassistant.update_entity checks right away (and installs)."""
    assert await async_setup_component(hass, "homeassistant", {})
    manifest, blobs = release("2026.10.0", {"fish/siganus": species("siganus")})
    publish(aioclient_mock, manifest, blobs)
    await hass.services.async_call(
        "homeassistant", "update_entity", {"entity_id": ENTITY}, blocking=True
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert state_of(hass, ENTITY).attributes["installed_version"] == "2026.10.0"


async def test_failed_download_keeps_the_pack(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    aioclient_mock: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manifest, blobs = release("1", {"fish/a": species("a")})
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    root = entry.runtime_data.pack_root
    assert (root / "fish" / "a").is_dir()

    manifest, blobs = release("2", {"fish/b": species("b")})
    blobs["fish-b.zip"] = blobs["fish-b.zip"][:-1] + b"#"  # corrupted
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    assert "checksum mismatch" in caplog.text
    assert (root / "fish" / "a").is_dir()
    assert state_of(hass, ENTITY).attributes["installed_version"] == "1"

    # a server error
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        f"{BASE}/latest/download/manifest.json", text='{"format": 1, "version": "3"'
    )
    await _check(hass, entry)
    assert entry.runtime_data.updater.latest.version == "2"
    publish(aioclient_mock, manifest, {})
    aioclient_mock.get(f"{BASE}/download/2/fish-b.zip", status=500)
    with pytest.raises(HomeAssistantError, match="HTTP 500"):
        await entry.runtime_data.updater.async_install()


async def test_download_limits(
    hass: HomeAssistant, entry: MockConfigEntry, aioclient_mock: Any
) -> None:
    manifest, blobs = release("1", {"fish/a": species("a")})
    manifest["entries"]["fish/a"]["size"] -= 5  # the archive is bigger
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    with pytest.raises(HomeAssistantError, match="more than"):
        await entry.runtime_data.updater.async_install()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/latest/download/manifest.json", content=b"\xff")
    await _check(hass, entry)
    assert entry.runtime_data.updater.coordinator.last_update_success is False
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/latest/download/manifest.json", exc=TimeoutError())
    await _check(hass, entry)
    assert entry.runtime_data.updater.coordinator.last_update_success is False


async def test_install_guards(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    updater = entry.runtime_data.updater
    with pytest.raises(HomeAssistantError) as err:
        await updater.async_install()
    assert err.value.translation_key == "catalog_unknown"
    manifest, _ = release("1", {"fish/a": species("a")})
    from custom_components.reeftank.pack import parse_manifest

    updater.latest = parse_manifest(manifest)
    updater.in_progress = True
    await updater.async_install()  # already running: nothing
    assert updater.installed is None


async def test_installed_pack_read_at_startup(
    hass: HomeAssistant, entry: MockConfigEntry, aioclient_mock: Any
) -> None:
    manifest, blobs = release("1", {"fish/a": species("a")})
    publish(aioclient_mock, manifest, blobs)
    await _check(hass, entry)
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/latest/download/manifest.json", status=404)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    state = state_of(hass, ENTITY)
    assert state.attributes["installed_version"] == "1"
    assert state.state == "off"


async def test_catalog_device_cannot_be_removed(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: Any
) -> None:
    assert await async_setup_component(hass, "config", {})
    device = find_device(dr.async_get(hass), (DOMAIN, CATALOG_DEVICE_ID))
    assert device is not None
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id(
        {
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": entry.entry_id,
            "device_id": device.id,
        }
    )
    assert not (await ws.receive_json())["success"]


async def test_check_button(
    hass: HomeAssistant, entry: MockConfigEntry, aioclient_mock: Any
) -> None:
    button = "button.reeftank_catalog_check_for_updates"
    assert state_of(hass, button) is not None
    # nothing published (404): the press reports it
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            "button", "press", {"entity_id": button}, blocking=True
        )
    assert err.value.translation_key == "catalog_check_failed"

    # a release: found now, and installed (automatic updates)
    manifest, blobs = release("2026.10.0", {"fish/siganus": species("siganus")})
    publish(aioclient_mock, manifest, blobs)
    await hass.services.async_call(
        "button", "press", {"entity_id": button}, blocking=True
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert state_of(hass, ENTITY).attributes["installed_version"] == "2026.10.0"
