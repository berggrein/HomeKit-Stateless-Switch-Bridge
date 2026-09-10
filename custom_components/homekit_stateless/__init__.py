cat << 'EOF' > custom_components/homekit_stateless/__init__.py
import logging
import threading
from datetime import datetime
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
            timestamp = datetime.now().strftime("%H:%M:%S")
            _LOGGER.info("[%s] Sendte '%s' fra %s", timestamp, event_type, self.display_name)
            self.char_event.value = None
            self.char_event.set_value(val)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="HomeKit Stateless Button Hub",
        manufacturer="ESPHome / HA Custom Bridge",
        model="Stateless Switch Bridge",
        sw_version="1.1.0",
    )

    storage_file = hass.config.path(".storage", f"{DOMAIN}_{entry.entry_id}.state")

    selected_entities = entry.options.get("entities", [])
    if not selected_entities:
        selected_entities = hass.states.async_entity_ids("event")

    entity_info = []
    for entity_id in selected_entities:
        state = hass.states.get(entity_id)
        if state:
            entity_info.append((entity_id, state.name or entity_id))

    def _build_and_init_driver():
        driver = AccessoryDriver(
            port=DEFAULT_PORT,
            pincode=DEFAULT_PIN.encode("utf-8"),
            persist_file=storage_file
        )
        bridge = Bridge(driver, "Trykknap Hub")

        accessories = {}
        aid_counter = 2

        for entity_id, name in entity_info:
            acc = StatelessButtonAccessory(driver, name, aid=aid_counter)
            bridge.add_accessory(acc)
            accessories[entity_id] = acc
            aid_counter += 1

        driver.add_accessory(bridge)
        return driver, accessories

    driver, accessories = await hass.async_add_executor_job(_build_and_init_driver)

    thread = threading.Thread(target=driver.start, daemon=True)
    thread.start()

    async def _handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if not new_state:
            return

        if old_state and new_state.last_updated == old_state.last_updated:
            return

        entity_id = event.data.get("entity_id")
        if entity_id in accessories:
            event_type = new_state.attributes.get("event_type")
            if event_type:
                accessories[entity_id].trigger_press(event_type)

    unsub = async_track_state_change_event(hass, list(accessories.keys()), _handle_state_change)
    update_listener = entry.add_update_listener(async_reload_entry)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "driver": driver,
        "thread": thread,
        "unsub": unsub,
        "update_listener": update_listener
    }

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        if "unsub" in data:
            data["unsub"]()
        if "update_listener" in data:
            data["update_listener"]()
        if "driver" in data:
            driver = data["driver"]
            def _safe_stop_driver():
                try:
                    driver.stop()
                except (AttributeError, RuntimeError) as err:
                    _LOGGER.debug("Oversprang mDNS-afmelding under stop: %s", err)

            await hass.async_add_executor_job(_safe_stop_driver)
    return True
EOF

zip -r homekit_stateless_bridge.zip hacs.json custom_components/
