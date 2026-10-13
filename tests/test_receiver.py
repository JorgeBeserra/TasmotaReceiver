"""Protocol and entity contract tests with a minimal HA/MQTT test double.

These tests do not substitute for loading the integration in a real HA instance.
"""
import asyncio
import importlib
import json
from pathlib import Path
import sys
import types
import unittest
from enum import IntFlag

ROOT = Path(__file__).resolve().parents[1]

def module(name):
    item = types.ModuleType(name)
    item.__path__ = []
    sys.modules[name] = item
    return item

for name in ('homeassistant', 'homeassistant.components', 'homeassistant.helpers'):
    module(name)
core = module('homeassistant.core')
core.callback = lambda f: f
mqtt = module('homeassistant.components.mqtt')
entity = module('homeassistant.helpers.entity')
class Entity:
    def __init__(self):
        self.removers = []
    def async_on_remove(self, f):
        if not hasattr(self, 'removers'):
            self.removers = []
        self.removers.append(f)
    async def async_added_to_hass(self):
        pass
    def async_write_ha_state(self):
        self.writes = getattr(self, 'writes', 0) + 1
entity.Entity = Entity
entity.DeviceInfo = dict
for platform, classname in (('number','NumberEntity'),('switch','SwitchEntity'),('sensor','SensorEntity'),('select','SelectEntity')):
    setattr(module('homeassistant.components.' + platform), classname, type(classname, (Entity,), {}))
mp = module('homeassistant.components.media_player')
mp.MediaPlayerEntity = type('MediaPlayerEntity', (Entity,), {})
mp.MediaPlayerEntityFeature = IntFlag('MediaPlayerEntityFeature', {n:1<<i for i,n in enumerate(('VOLUME_SET','VOLUME_MUTE','VOLUME_STEP','TURN_ON','TURN_OFF','SELECT_SOURCE'))})
mp.MediaPlayerDeviceClass = types.SimpleNamespace(RECEIVER='receiver')
mp.MediaPlayerState = types.SimpleNamespace(ON='on', OFF='off')
pkg = module('monoprice_custom')
pkg.__path__ = [str(ROOT/'custom_components/monoprice_custom')]
protocol = importlib.import_module('monoprice_custom.protocol')
Coordinator = importlib.import_module('monoprice_custom.coordinator').ReceiverCoordinator
Player = importlib.import_module('monoprice_custom.media_player').ReceiverPlayer
Number = importlib.import_module('monoprice_custom.number').ReceiverNumber
Switch = importlib.import_module('monoprice_custom.switch').ReceiverSwitch
Select = importlib.import_module('monoprice_custom.select').ReceiverSource

def message(payload):
    return types.SimpleNamespace(payload=payload)

class ReceiverTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.sent = []
        self.handlers = {}
        self.unsubscribed = []
        async def subscribe(hass, topic, handler):
            self.handlers[topic] = handler
            return lambda: self.unsubscribed.append(topic)
        async def publish(hass, topic, payload, **kwargs):
            self.sent.append((topic, payload, kwargs))
        mqtt.async_subscribe = subscribe
        mqtt.async_publish = publish
        entry = types.SimpleNamespace(data={'topic':'receiver_one', 'pt2323':True},options={},entry_id='id1',title='Sala')
        self.c = Coordinator(object(), entry)
        await self.c.async_start()

    async def test_setup_topics_and_unload(self):
        self.assertEqual(len(self.handlers), 4)
        self.assertEqual([x[1] for x in self.sent], ['status 0','ptstatus 0'])
        self.c.async_stop(); self.c.async_stop()
        self.assertEqual(len(self.unsubscribed), 4)

    async def test_invalid_and_unrelated_payloads_do_not_change_state(self):
        for payload in ('bad', '[]', 'null', '{"PT2322": []}', '{"POWER":"ON"}'):
            self.c._state(message(payload))
        self.assertEqual(self.c.data,{})
        self.assertFalse(self.c.online)
        self.c._state(message(b'{"PT2322":{"VL":35,"CT":4}}'))
        self.assertEqual(self.c.data['PT2322']['Volume'],35)
        self.assertEqual(self.c.data['PT2322']['Center'],4)
        self.c._state(message('{"PT2322":{"Bass":7}}'))
        self.assertEqual(self.c.data['PT2322']['Volume'],35)

    async def test_confirmed_state_and_offline_reconnect(self):
        p = Player(self.c)
        await p.async_added_to_hass()
        self.c._state(message('{"PT2322":{"Ready":true,"State":1,"Volume":35,"Mute":0}}'))
        self.assertTrue(p.available); self.assertEqual(p.state,'on')
        self.assertEqual(p.volume_level,35/79)
        await p.async_set_volume_level(1)
        self.assertEqual(p.volume_level,35/79) # no optimistic success before device response
        await self.c._lwt(message('Offline'))
        self.assertFalse(p.available)
        await self.c._lwt(message('Online'))
        self.assertFalse(p.available) # wait for fresh state, not stale cached values
        self.assertEqual(self.sent[-2][1], 'status 0')
        self.c._state(message('{"PT2322":{"Ready":true,"Volume":79}}'))
        self.assertTrue(p.available)
        for f in p.removers: f()
        self.assertEqual(len(self.c.listeners),0)

    async def test_sources_and_absent_selector(self):
        s = Select(self.c)
        self.c._state(message('{"PT2323":{"Present":false,"Ready":false,"Input":0}}'))
        self.assertFalse(s.available)
        self.c._state(message('{"PT2323":{"Present":true,"Ready":true,"Input":4}}'))
        self.assertEqual(s.current_option, 'Stereo 4')
        await s.async_select_option('Stereo 1')
        self.assertEqual(self.sent[-1][:2], ('cmnd/receiver_one/driver129','input 1'))
        with self.assertRaises(ValueError): await s.async_select_option('invalid')

    async def test_switch_disable_semantics_and_channel_mask(self):
        s = Switch(self.c,'3D','3d','PT2322',True)
        self.c._state(message('{"PT2322":{"3D":1}}'))
        self.assertFalse(s.is_on)
        await s.async_turn_on(); self.assertEqual(self.sent[-1][1],'3d 0')
        await s.async_turn_off(); self.assertEqual(self.sent[-1][1],'3d 1')
        m = Switch(self.c,'Mute Center','pm_ct','PT2323',bit=2)
        self.c._state(message('{"PT2323":{"ChannelMute":4}}'))
        self.assertTrue(m.is_on)

    async def test_tone_db_and_channel_db(self):
        tone = Number(self.c,'Bass','ba',-14,14,2)
        trim = Number(self.c,'Center','ct',-15,0,1)
        self.c._state(message('{"PT2322":{"Bass":7,"Center":4}}'))
        self.assertEqual(tone.native_value,14)
        self.assertEqual(trim.native_value,-11)
        await tone.async_set_native_value(-14); self.assertEqual(self.sent[-1][1],'ba -7')
        await trim.async_set_native_value(0); self.assertEqual(self.sent[-1][1],'ct 15')
        with self.assertRaises(ValueError): await tone.async_set_native_value(3)

    async def test_publish_failure_propagates(self):
        async def fail(*args,**kwargs): raise RuntimeError('broker failure')
        mqtt.async_publish = fail
        with self.assertRaises(RuntimeError): await self.c.async_send('input',1)
        self.assertEqual(self.c.data,{})

    async def test_separate_devices_and_nonretained_commands(self):
        other = Coordinator(object(),types.SimpleNamespace(data={'topic':'receiver_two'},options={},entry_id='id2',title='Quarto'))
        await other.async_send('on',0)
        self.assertEqual(self.sent[-1][0],'cmnd/receiver_two/driver129')
        self.assertFalse(self.sent[-1][2]['retain'])
        self.assertEqual(self.c.topic,'receiver_one')

class ProtocolTests(unittest.TestCase):
    def test_topic_validation(self):
        self.assertEqual(protocol.validate_topic(' room '),'room')
        for topic in ('','cmnd/room/driver129','a+','a#','a b','a\nb'):
            with self.assertRaises(ValueError): protocol.validate_topic(topic)
    def test_boolean_and_manifest_domain(self):
        self.assertFalse(protocol.as_bool('OFF'))
        self.assertTrue(protocol.as_bool('ON'))
        self.assertIsNone(protocol.as_bool('unknown'))
        data = json.loads((ROOT/'custom_components/monoprice_custom/manifest.json').read_text())
        self.assertEqual(data['domain'],'monoprice_custom')
        self.assertIn('mqtt',data['dependencies'])

if __name__ == '__main__': unittest.main()
