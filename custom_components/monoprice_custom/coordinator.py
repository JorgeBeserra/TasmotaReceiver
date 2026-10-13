"""Single MQTT subscription and shared confirmed state per receiver."""
import asyncio
from homeassistant.components import mqtt
from homeassistant.core import callback
from .const import CONF_TOPIC, CONF_PT2323
from .protocol import decode_state, validate_topic, normalize_processor

class ReceiverCoordinator:
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.topic = validate_topic(entry.options.get(CONF_TOPIC, entry.data[CONF_TOPIC]))
        self.has_pt2323 = entry.options.get(CONF_PT2323, entry.data.get(CONF_PT2323, False))
        self.data = {}
        self.online = False
        self.listeners = set()
        self.unsubscribers = []
        self.lock = asyncio.Lock()

    async def async_start(self):
        for topic, handler in ((f"stat/{self.topic}/RESULT", self._state),
                               (f"tele/{self.topic}/SENSOR", self._state),
                               (f"tele/{self.topic}/LWT", self._lwt),
                               ("homeassistant/status", self._ha_status)):
            self.unsubscribers.append(await mqtt.async_subscribe(self.hass, topic, handler))
        await self.async_request_state()

    @callback
    def async_stop(self):
        for unsubscribe in self.unsubscribers:
            unsubscribe()
        self.unsubscribers.clear()

    async def async_request_state(self):
        await self.async_send("status", 0)
        if self.has_pt2323:
            await self.async_send("ptstatus", 0)

    async def async_send(self, command, value):
        async with self.lock:
            await mqtt.async_publish(self.hass, f"cmnd/{self.topic}/driver129",
                                     f"{command} {int(value)}", qos=0, retain=False)

    @callback
    def _state(self, msg):
        state = decode_state(msg.payload)
        if not state:
            return
        for chip, values in state.items():
            self.data.setdefault(chip, {}).update(normalize_processor(values) if chip == "PT2322" else values)
        self.online = True
        self._notify()

    async def _lwt(self, msg):
        self.online = msg.payload == "Online"
        if not self.online:
            # A subsequent Online must wait for fresh confirmed state.
            self.data.clear()
        self._notify()
        if self.online:
            await self.async_request_state()

    async def _ha_status(self, msg):
        if msg.payload == "online":
            await self.async_request_state()

    @callback
    def async_add_listener(self, listener):
        self.listeners.add(listener)
        return lambda: self.listeners.discard(listener)

    @callback
    def _notify(self):
        for listener in tuple(self.listeners):
            listener()
