"""Config flow: a single entry, nothing to configure."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


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
