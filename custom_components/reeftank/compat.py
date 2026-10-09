"""Compatibility across Home Assistant versions.

Home Assistant validates with probatio since 2026.9 and types its helpers
(services, WebSocket commands, flows) with probatio schemas since 2026.10;
older versions only have voluptuous. Every module of the integration takes
its schema library from here, so the schemas, the errors they raise and the
ones Home Assistant catches always come from the same library.
"""

from __future__ import annotations

from collections.abc import Iterable
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


def all_devices(dev_reg: dr.DeviceRegistry) -> Iterable[dr.DeviceEntry]:
    """Every device of the registry.

    `devices` is a mapping by id before 2026.10, a plain collection since.
    """
    devices: Any = dev_reg.devices
    return devices.values() if hasattr(devices, "values") else devices


def find_device(
    dev_reg: dr.DeviceRegistry, identifier: tuple[str, str]
) -> dr.DeviceEntry | None:
    """The device carrying an identifier, whatever its config entry.

    `async_get_device(identifiers=...)` is deprecated since 2026.10 (an
    identifier is only unique within a config entry) and its replacement
    needs the entry; a plain scan works on every version.
    """
    for device in all_devices(dev_reg):
        if identifier in device.identifiers:
            return device
    return None


__all__ = ["StaticPathConfig", "all_devices", "find_device", "vol"]
