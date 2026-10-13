"""SabidosReceiver media player, confirmed through MQTT."""
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerDeviceClass, MediaPlayerState
from .const import DOMAIN
from .entity import ReceiverEntity
from .protocol import SOURCES, as_bool

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ReceiverPlayer(hass.data[DOMAIN][entry.entry_id])])

class ReceiverPlayer(ReceiverEntity, MediaPlayerEntity):
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    def __init__(self, coordinator):
        super().__init__(coordinator, "receiver", None)
        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET | MediaPlayerEntityFeature.VOLUME_MUTE |
            MediaPlayerEntityFeature.VOLUME_STEP | MediaPlayerEntityFeature.TURN_ON |
            MediaPlayerEntityFeature.TURN_OFF)
        if coordinator.has_pt2323:
            self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOURCE

    @property
    def state(self):
        value = as_bool(self.values.get("State"))
        return None if value is None else (MediaPlayerState.ON if value else MediaPlayerState.OFF)

    @property
    def volume_level(self):
        value = self.values.get("Volume")
        return value / 79 if isinstance(value, (int, float)) and 0 <= value <= 79 else None

    @property
    def is_volume_muted(self):
        return as_bool(self.values.get("Mute"))

    @property
    def source_list(self):
        return list(SOURCES.values()) if self.coordinator.has_pt2323 else None

    @property
    def source(self):
        return SOURCES.get(self.coordinator.data.get("PT2323", {}).get("Input"))

    async def async_select_source(self, source):
        if source not in SOURCES.values() or not self.coordinator.has_pt2323:
            raise ValueError("Unknown or unsupported source")
        await self.coordinator.async_send("input", next(i for i, name in SOURCES.items() if name == source))

    async def async_turn_on(self):
        await self.coordinator.async_send("on", 0)

    async def async_turn_off(self):
        await self.coordinator.async_send("off", 0)

    async def async_mute_volume(self, mute):
        await self.coordinator.async_send("mt", int(mute))

    async def async_set_volume_level(self, volume):
        if not 0 <= volume <= 1:
            raise ValueError("Volume must be 0..1")
        await self.coordinator.async_send("vl", round(volume * 79))

    async def async_volume_up(self):
        await self.coordinator.async_send("vl_up", 0)

    async def async_volume_down(self):
        await self.coordinator.async_send("vl_down", 0)
