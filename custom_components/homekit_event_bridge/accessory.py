"""A single HomeKit Stateless Programmable Switch backed by an HA `event` entity."""
from __future__ import annotations

import logging

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_PROGRAMMABLE_SWITCH

from .const import (
    CHAR_NAME,
    CHAR_PROGRAMMABLE_SWITCH_EVENT,
    EVENT_TYPE_MAP,
    SERVICE_STATELESS_PROGRAMMABLE_SWITCH,
)

_LOGGER = logging.getLogger(__name__)


class EventEntitySwitch(Accessory):
    """Expose one HA `event` entity as a HomeKit Stateless Programmable Switch.

    This accessory holds no state of its own: it just forwards translated
    `event_type` values onto the ProgrammableSwitchEvent characteristic,
    which is how HomeKit represents a stateless button press.
    """

    category = CATEGORY_PROGRAMMABLE_SWITCH

    def __init__(self, driver, display_name: str, entity_id: str) -> None:
        # `unique_id` on the preloaded service keeps IIDs stable and unique
        # per entity, which matters once more than one switch lives on the
        # same bridge.
        super().__init__(driver, display_name)
        self.entity_id = entity_id

        serv_switch = self.add_preload_service(
            SERVICE_STATELESS_PROGRAMMABLE_SWITCH,
            chars=[CHAR_PROGRAMMABLE_SWITCH_EVENT, CHAR_NAME],
            unique_id=entity_id,
        )
        serv_switch.configure_char(CHAR_NAME, value=display_name)
        self.char_event = serv_switch.configure_char(
            CHAR_PROGRAMMABLE_SWITCH_EVENT, value=0
        )

    def handle_event_type(self, event_type: str | None) -> None:
        """Forward a translated HA `event_type` to HomeKit, if mappable."""
        if event_type is None:
            return

        hk_value = EVENT_TYPE_MAP.get(event_type)
        if hk_value is None:
            _LOGGER.debug(
                "%s: unmapped event_type %r, not forwarding to HomeKit",
                self.entity_id,
                event_type,
            )
            return

        _LOGGER.debug(
            "%s: forwarding event_type %r as HomeKit value %s",
            self.entity_id,
            event_type,
            hk_value,
        )
        self.char_event.set_value(hk_value)

    # This accessory is purely event-driven; it has nothing to poll and
    # nothing to clean up beyond what the bridge/driver already handle.
    async def run(self) -> None:  # noqa: D102
        return

    async def stop(self) -> None:  # noqa: D102
        return
