"""Constants for the HomeKit Event Bridge integration."""
from __future__ import annotations

DOMAIN = "homekit_event_bridge"

# --- Config / options keys -------------------------------------------------
CONF_ENTITIES = "entities"
CONF_PORT = "port"

DEFAULT_PORT = 21063
BRIDGE_NAME = "HA Event Bridge"

# --- HomeKit Stateless Programmable Switch mapping --------------------------
# Home Assistant `event` entities expose the kind of press/click that just
# happened via the `event_type` attribute on the entity's state. HomeKit's
# "Stateless Programmable Switch" service exposes an equivalent concept via
# the ProgrammableSwitchEvent characteristic, which only accepts 0, 1 or 2.
#
#   0 -> Single Press
#   1 -> Double Press
#   2 -> Long Press
#
# Any `event_type` not present in this mapping is ignored (logged at debug
# level) rather than forwarded, since HomeKit has no equivalent for it.
EVENT_TYPE_MAP: dict[str, int] = {
    "single_press": 0,
    "double_press": 1,
    "long_press": 2,
}

ATTR_EVENT_TYPE = "event_type"

# Service/characteristic names as known to pyhap's bundled resource loader.
SERVICE_STATELESS_PROGRAMMABLE_SWITCH = "StatelessProgrammableSwitch"
CHAR_PROGRAMMABLE_SWITCH_EVENT = "ProgrammableSwitchEvent"
CHAR_NAME = "Name"

# Where (relative to the HA config dir) pairing state is persisted, per
# config entry, so that pairing survives Home Assistant restarts.
STORAGE_SUBDIR = f"{DOMAIN}"

PLATFORMS: list[str] = []
