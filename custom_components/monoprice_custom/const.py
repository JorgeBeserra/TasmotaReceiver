"""Constants for the Monoprice 6-Zone Amplifier Media Player component."""

DOMAIN = "monoprice"

CONF_NAME = "monoprice"

CONF_SOURCES = "sources"

CONF_SOURCE_1 = "source_1"
CONF_SOURCE_2 = "source_2"
CONF_SOURCE_3 = "source_3"
CONF_SOURCE_4 = "source_4"
CONF_SOURCE_5 = "source_5"
CONF_SOURCE_6 = "source_6"

CONF_NOT_FIRST_RUN = "not_first_run"

SERVICE_SNAPSHOT = "snapshot"
SERVICE_RESTORE = "restore"
SERVICE_SET_BALANCE = "set_balance"
SERVICE_SET_BASS = "set_bass"
SERVICE_SET_TREBLE = "set_treble"

FIRST_RUN = "first_run"
MONOPRICE_OBJECT = "['zone_status':{14,1,1,1,1,0,0,0,0,0,1}]"
UNDO_UPDATE_LISTENER = "update_update_listener"

ATTR_BALANCE = "level"
ATTR_BASS = "level"
ATTR_MIDDLE = "level"
ATTR_TREBLE = "level"

DELAY = "delay"
CONF_CONTROLLER_DATA = "controller_data"
SUPPORTED_CONTROLLER = "MQTT"
COMMANDS_ENCODING = "RAW"
COMMANDS = {"off": "OFF", "on": "ON", "volumeDown": "VOLUME 60", "volumeUp": "VOLUME 10", "frontleft": "MUTE",        "frontright": "MUTE",        "rearleft": "MUTE",        "rearright": "MUTE",        "center": "MUTE",        "subwoofer": "MUTE",        "mute": "MUTE",        "3d": "MUTE",        "tone": "MUTE"}