"""Owns the pyhap AccessoryDriver/Bridge and wires it up to HA state changes."""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .accessory import EventEntitySwitch
from .const import ATTR_EVENT_TYPE, BRIDGE_NAME

_LOGGER = logging.getLogger(__name__)


class EventBridge:
    """Runs one HAP-python bridge and keeps it in sync with the entity list."""

    def __init__(self, hass: HomeAssistant, port: int, persist_file: Path) -> None:
        self._hass = hass
        self._port = port
        self._persist_file = persist_file

        self.driver: AccessoryDriver | None = None
        self._bridge: Bridge | None = None
        self._accessories: dict[str, EventEntitySwitch] = {}
        self._unsub: dict[str, Callable[[], None]] = {}

    async def async_start(self, entity_ids: list[str]) -> None:
        """Create the driver/bridge, add the initial accessories and start."""
        self._persist_file.parent.mkdir(parents=True, exist_ok=True)

        self.driver = AccessoryDriver(
            port=self._port,
            persist_file=str(self._persist_file),
            loop=self._hass.loop,
        )
        self._bridge = Bridge(self.driver, BRIDGE_NAME)
        self.driver.add_accessory(self._bridge)

        self._sync_entities(entity_ids)

        await self.driver.async_start()
        _LOGGER.info(
            "HomeKit Event Bridge listening on port %s (pairing state: %s)",
            self._port,
            self._persist_file,
        )

    async def async_stop(self) -> None:
        """Tear down all listeners and stop the HAP driver."""
        for entity_id in list(self._accessories):
            self._remove_entity(entity_id)

        if self.driver is not None:
            await self.driver.async_stop()

    def _sync_entities(self, entity_ids: list[str]) -> None:
        """Add/remove accessories so they match the desired entity list.

        Only used at startup here; entity-list changes made via the Options
        Flow trigger a full reload of the config entry (see __init__.py) so
        that pyhap's internal AID/IID bookkeeping is rebuilt cleanly rather
        than mutated in place.
        """
        desired = set(entity_ids)
        current = set(self._accessories)

        for entity_id in current - desired:
            self._remove_entity(entity_id)
        for entity_id in desired - current:
            self._add_entity(entity_id)

    def _add_entity(self, entity_id: str) -> None:
        assert self._bridge is not None and self.driver is not None

        state = self._hass.states.get(entity_id)
        display_name = state.name if state else entity_id

        accessory = EventEntitySwitch(self.driver, display_name, entity_id)
        self._bridge.add_accessory(accessory)
        self._accessories[entity_id] = accessory

        @callback
        def _on_state_change(event: Event[EventStateChangedData]) -> None:
            new_state = event.data.get("new_state")
            if new_state is None:
                return
            accessory.handle_event_type(new_state.attributes.get(ATTR_EVENT_TYPE))

        self._unsub[entity_id] = async_track_state_change_event(
            self._hass, [entity_id], _on_state_change
        )
        _LOGGER.debug("Added HomeKit accessory for %s", entity_id)

    def _remove_entity(self, entity_id: str) -> None:
        unsub = self._unsub.pop(entity_id, None)
        if unsub is not None:
            unsub()

        accessory = self._accessories.pop(entity_id, None)
        if accessory is not None and self._bridge is not None:
            self._bridge.accessories.pop(accessory.aid, None)
        _LOGGER.debug("Removed HomeKit accessory for %s", entity_id)
