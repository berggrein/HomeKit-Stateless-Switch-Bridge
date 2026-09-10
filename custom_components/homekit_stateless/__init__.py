import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from pyhap.accessory_driver import AccessoryDriver

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_PINCODE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    port = entry.data.get("port", DEFAULT_PORT)
    pincode = entry.data.get("pincode", DEFAULT_PINCODE)
    
    state_file = hass.config.path(f".storage/{DOMAIN}_{entry.entry_id}.state")

    # Importeres dynamisk eller kaldes via executor for at undgå blocking I/O
    from .bridge import HomeKitStatelessBridge

    bridge = HomeKitStatelessBridge(hass, entry)

    def _init_driver():
        driver = AccessoryDriver(
            port=port,
            persist_file=state_file,
            pincode=pincode.encode("utf-8"),
        )
        driver.add_accessory(bridge)
        return driver

    # Kør synkron fil-I/O i en separat tråd
    driver = await hass.async_add_executor_job(_init_driver)

    async def _async_start_driver(event=None):
        await hass.async_add_executor_job(driver.start)

    async def _async_stop_driver(event=None):
        await hass.async_add_executor_job(driver.stop)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop_driver)

    hass.data[DOMAIN][entry.entry_id] = {
        "driver": driver,
        "bridge": bridge,
    }

    hass.async_create_task(_async_start_driver())

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data and "driver" in data:
        await hass.async_add_executor_job(data["driver"].stop)
    return True
