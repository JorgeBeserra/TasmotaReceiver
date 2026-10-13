"""Legacy processor diagnostics and optional selector I2C error."""
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN
from .entity import ReceiverEntity
from .protocol import as_bool

async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    entities = [ReceiverSensor(c, key, "PT2322") for key in ("Mute", "3D", "Tone")]
    if c.has_pt2323:
        entities.append(ReceiverSensor(c, "Error", "PT2323"))
    async_add_entities(entities)

class ReceiverSensor(ReceiverEntity, SensorEntity):
    _attr_entity_registry_enabled_default = False
    def __init__(self, coordinator, key, chip):
        super().__init__(coordinator, f"sensor_{chip}_{key}", f"{chip} {key}")
        self.state_key = key
        self.chip = chip

    @property
    def available(self):
        # Diagnostics remain readable even after an I2C failure.
        return self.coordinator.online and bool(self.values)

    @property
    def native_value(self):
        value = self.values.get(self.state_key)
        if self.state_key == "Error":
            return value
        enabled = as_bool(value)
        if enabled is None:
            return None
        if self.state_key in ("3D", "Tone"):
            enabled = not enabled
        return "ON" if enabled else "OFF"
