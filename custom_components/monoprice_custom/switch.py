"""Processor functions and optional selector controls."""
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN
from .entity import ReceiverEntity
from .protocol import as_bool

async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    entities = [ReceiverSwitch(c, "3D", "3d", "PT2322", True),
                ReceiverSwitch(c, "Tone", "tn", "PT2322", True)]
    if c.has_pt2323:
        entities += [ReceiverSwitch(c, key, cmd, "PT2323") for key, cmd in (
            ("Surround", "surround"), ("MixBoost", "mixboost"), ("Mute", "pmute"))]
        entities += [ReceiverSwitch(c, name, cmd, "PT2323", bit=i) for i, (name, cmd) in enumerate((
            ("Mute FL", "pm_fl"), ("Mute FR", "pm_fr"), ("Mute Center", "pm_ct"),
            ("Mute Subwoofer", "pm_sb"), ("Mute SL", "pm_rl"), ("Mute SR", "pm_rr")))]
    async_add_entities(entities)

class ReceiverSwitch(ReceiverEntity, SwitchEntity):
    def __init__(self, coordinator, key, command, chip, inverse=False, bit=None):
        super().__init__(coordinator, f"{chip}_{key}", key if chip == "PT2322" else f"PT2323 {key}")
        self.state_key = key
        self.command = command
        self.chip = chip
        self.inverse = inverse
        self.bit = bit

    @property
    def is_on(self):
        if self.bit is not None:
            mask = self.values.get("ChannelMute")
            return bool(mask & (1 << self.bit)) if isinstance(mask, int) else None
        value = as_bool(self.values.get(self.state_key))
        return not value if value is not None and self.inverse else value

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_send(self.command, 0 if self.inverse else 1)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_send(self.command, 1 if self.inverse else 0)
