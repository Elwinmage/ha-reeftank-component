"""Config flow: a single entry; options for the catalog updates."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .compat import vol
from .const import CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE, DOMAIN


class ReefTankConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add the ReefTank integration (aquariums are created from the card)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm, then create the single entry."""
        if user_input is not None:
            return self.async_create_entry(title="ReefTank", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Options of the entry."""
        return ReefTankOptionsFlow()


class ReefTankOptionsFlow(OptionsFlow):
    """Catalog updates: automatic or on demand."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """One switch."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_AUTO_UPDATE, default=current): bool}
            ),
        )
