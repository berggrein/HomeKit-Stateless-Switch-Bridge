import logging
import threading
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_PROGRAMMABLE_SWITCH

from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_PIN

_LOGGER = logging.getLogger(__name__)

class StatelessButtonAccessory(Accessory):
    category = CATEGORY_PROGRAMMABLE_SWITCH

    def __init__(self, driver, name, aid=None):
        super().__init__(driver, name, aid=aid)
        serv_switch = self.add_preload_service('StatelessProgrammableSwitch')
        self.char_event = serv_switch.configure_char('ProgrammableSwitchEvent')

    def trigger_press(self, event_type: str):
        mapping = {
            "single_press": 0,
            "double_press": 1,
            "long_press": 2,
        }
        val = mapping.get(event_type)
        if val is not None:
            _LOGGER.info("Sender HomeKit event '%s' (%s) for %s", event_type, val, self.display_name)
            self.char_event.set_value(val)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="HomeKit Stateless Button Hub",
        manufacturer="ESPHome / HA Custom Bridge",
        model="Stateless Switch Bridge",
        sw_version="1.0.0",
    )

    storage_file = hass.config.path(".storage", f"{DOMAIN}_{entry.entry_id}.state")

    driver = AccessoryDriver(
        port=DEFAULT_PORT,
        pincode=DEFAULT_PIN.encode("utf-8"),
        persist_file=storage_file
    )
    bridge = Bridge(driver, "Trykknap Hub")

    accessories = {}
    aid_counter = 2

    event_entities = hass.states.async_entity_ids("event")

    for entity_id in event_entities:
        state = hass.states.get(entity_id)
        name = state.name if state else entity_id
        acc = StatelessButtonAccessory(driver, name, aid=aid_counter)
        bridge.add_accessory(acc)
        accessories[entity_id] = acc
        aid_counter += 1

    driver.add_accessory(bridge)

    thread = threading.Thread(target=driver.start, daemon=True)
    thread.start()

    async def _handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        if not new_state:
            return
        entity_id = event.data.get("entity_id")
        if entity_id in accessories:
            event_type = new_state.attributes.get("event_type")
            if event_type:
                accessories[entity_id].trigger_press(event_type)

    async_track_state_change_event(hass, list(accessories.keys()), _handle_state_change)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "driver": driver,
        "thread": thread
    }

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data and "driver" in data:
        data["driver"].stop()
    return True
