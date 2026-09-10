"""The HomeKit Event Bridge integration.

Exposes user-chosen Home Assistant `event` entities to Apple HomeKit as
Stateless Programmable Switches, using their own small HAP-python bridge
(separate from, and independent of, Home Assistant's built-in `homekit`
integration).
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .bridge import EventBridge
from .const import CONF_ENTITIES, CONF_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HomeKit Event Bridge from a config entry."""
    port: int = entry.data[CONF_PORT]
    entities: list[str] = entry.options.get(CONF_ENTITIES, [])

    persist_file = _persist_file_path(hass, entry.entry_id)
    event_bridge = EventBridge(hass, entry.entry_id, port, persist_file)
    await event_bridge.async_start(entities)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = event_bridge
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry: stop the HAP server for this bridge."""
    event_bridge: EventBridge | None = hass.data.get(DOMAIN, {}).pop(
        entry.entry_id, None
    )
    if event_bridge is not None:
        await event_bridge.async_stop()
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options (the entity list) change.

    A full reload is used rather than mutating the running bridge in place,
    since it keeps pyhap's accessory/IID bookkeeping consistent whenever the
    set of exposed entities changes.
    """
    await hass.config_entries.async_reload(entry.entry_id)


def _persist_file_path(hass: HomeAssistant, entry_id: str):
    """Return the path used to persist this bridge's HomeKit pairing state."""
    from pathlib import Path

    return Path(hass.config.path(DOMAIN, f"{entry_id}.state"))
