"""SabidosReceiver MQTT integration."""
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN, PLATFORMS
from .coordinator import ReceiverCoordinator

async def async_setup_entry(hass, entry):
    coordinator = ReceiverCoordinator(hass, entry)
    try:
        await coordinator.async_start()
    except Exception as err:
        coordinator.async_stop()
        raise ConfigEntryNotReady(str(err)) from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        coordinator.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    return True

async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id).async_stop()
        return True
    return False

async def _async_reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)
