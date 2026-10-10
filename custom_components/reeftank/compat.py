"""Compatibility across Home Assistant versions.

Home Assistant validates with probatio since 2026.9 and types its helpers
(services, WebSocket commands, flows) with probatio schemas since 2026.10;
older versions only have voluptuous. Every module of the integration takes
its schema library from here, so the schemas, the errors they raise and the
ones Home Assistant catches always come from the same library.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers import device_registry as dr

if TYPE_CHECKING:
    import probatio as vol
else:
    try:
        import probatio as vol
    except ImportError:  # pragma: no cover - depends on the installed HA version
        import voluptuous as vol

try:
    # Home Assistant 2025.2+ exposes it from the http.server submodule.
    from homeassistant.components.http.server import StaticPathConfig
except ImportError:  # pragma: no cover - depends on the installed HA version
    # Older Home Assistant kept it in the package root.
    from homeassistant.components.http import (
        StaticPathConfig,  # pyright: ignore[reportPrivateImportUsage]
    )


def find_device(
    dev_reg: dr.DeviceRegistry, identifier: tuple[str, str]
) -> dr.DeviceEntry | None:
    """The device carrying an identifier, whatever its config entry.

    `async_get_device(identifiers=...)` is deprecated since 2026.10 (an
    identifier is only unique within a config entry): `async_get_devices`
    replaces it. Before, `devices` is a mapping of the entries by id, scanned.
    """
    lookup: Any = getattr(dev_reg, "async_get_devices", None)
    if lookup is None:  # pragma: no cover - Home Assistant before 2026.10
        devices: Any = dev_reg.devices
        found = [d for d in devices.values() if identifier in d.identifiers]
    else:
        found = lookup(identifiers={identifier})
    return found[0] if found else None


__all__ = ["StaticPathConfig", "find_device", "vol"]
