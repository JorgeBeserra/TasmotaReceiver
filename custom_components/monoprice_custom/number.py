"""Per-channel levels and tone controls."""
from homeassistant.components.number import NumberEntity
from .const import DOMAIN
from .entity import ReceiverEntity
from .protocol import CHANNELS

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ReceiverNumber(coordinator, key, command, -15, 0, 1) for key, command in CHANNELS.items()] +
                       [ReceiverNumber(coordinator, key, command, -14, 14, 2)
                        for key, command in (("Bass", "ba"), ("Middle", "md"), ("Treble", "tb"))])

class ReceiverNumber(ReceiverEntity, NumberEntity):
    _attr_native_unit_of_measurement = "dB"
    def __init__(self, coordinator, key, command, minimum, maximum, step):
        super().__init__(coordinator, key, key)
        self.command = command
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step

    @property
    def native_value(self):
        value = self.values.get(self.key)
        # Wire protocol uses 0=-15 dB and 15=0 dB; display actual dB.
        if value is None:
            return None
        return value * 2 if self._attr_native_step == 2 else value - 15

    async def async_set_native_value(self, value):
        if not self._attr_native_min_value <= value <= self._attr_native_max_value or value % self._attr_native_step:
            raise ValueError("Invalid value or step")
        await self.coordinator.async_send(self.command, int(value / 2) if self._attr_native_step == 2 else int(value + 15))
