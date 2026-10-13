"""Optional PT2323 source selection."""
from homeassistant.components.select import SelectEntity
from .const import DOMAIN
from .entity import ReceiverEntity
from .protocol import SOURCES

async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    if c.has_pt2323:
        async_add_entities([ReceiverSource(c)])

class ReceiverSource(ReceiverEntity, SelectEntity):
    chip = "PT2323"
    _attr_options = list(SOURCES.values())
    def __init__(self, coordinator):
        super().__init__(coordinator, "input", "Entrada de áudio")

    @property
    def current_option(self):
        return SOURCES.get(self.values.get("Input"))

    async def async_select_option(self, option):
        if option not in SOURCES.values():
            raise ValueError("Unknown source")
        await self.coordinator.async_send("input", next(i for i, name in SOURCES.items() if name == option))
