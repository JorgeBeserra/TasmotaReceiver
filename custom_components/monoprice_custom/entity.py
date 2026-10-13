"""Push entities displaying confirmed firmware state."""
from homeassistant.helpers.entity import Entity, DeviceInfo
from .const import DOMAIN

class ReceiverEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    chip = "PT2322"

    def __init__(self, coordinator, key, name):
        self.coordinator = coordinator
        self.key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title, manufacturer="Sabidos",
            model="SabidosReceiver")

    @property
    def values(self):
        return self.coordinator.data.get(self.chip, {})

    @property
    def available(self):
        if not self.coordinator.online or not self.values:
            return False
        if self.chip == "PT2323":
            return self.values.get("Present") is True and self.values.get("Ready") is True
        return self.values.get("Ready", True) is True

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))
