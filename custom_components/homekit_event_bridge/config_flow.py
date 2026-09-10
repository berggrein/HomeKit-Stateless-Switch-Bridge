"""Config flow for the HomeKit Event Bridge integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.helpers import selector

from .const import CONF_ENTITIES, CONF_PORT, DEFAULT_PORT, DOMAIN


def _entities_schema(current: list[str] | None = None) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ENTITIES, default=current or []): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="event", multiple=True)
            ),
        }
    )


class HomeKitEventBridgeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup: pick a port, then pick entities."""

    VERSION = 1

    def __init__(self) -> None:
        self._port: int | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step: choose the local port for this bridge's HAP server."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._port = user_input[CONF_PORT]
            return await self.async_step_entities()

        schema = vol.Schema(
            {vol.Required(CONF_PORT, default=DEFAULT_PORT): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1024, max=65535, mode="box")
            )}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Second step: choose which `event` entities to expose."""
        if user_input is not None:
            entities: list[str] = user_input[CONF_ENTITIES]
            return self.async_create_entry(
                title="HomeKit Event Bridge",
                data={CONF_PORT: self._port},
                options={CONF_ENTITIES: entities},
            )

        return self.async_show_form(
            step_id="entities", data_schema=_entities_schema()
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "HomeKitEventBridgeOptionsFlow":
        return HomeKitEventBridgeOptionsFlow(config_entry)


class HomeKitEventBridgeOptionsFlow(OptionsFlow):
    """Let the user add/remove exposed `event` entities after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._config_entry.options.get(CONF_ENTITIES, [])
        return self.async_show_form(
            step_id="init", data_schema=_entities_schema(current)
        )
