"""MQTT protocol shared with Tasmota driver129 (no HA dependencies)."""
import json

SOURCES = {0: "5.1", 1: "Stereo 1", 2: "Stereo 2", 3: "Stereo 3", 4: "Stereo 4"}
CHANNELS = {"FrontLeft": "fl", "FrontRight": "fr", "Center": "ct",
            "Subwoofer": "sb", "RearLeft": "rl", "RearRight": "rr"}

def validate_topic(value):
    """Accept a Tasmota Topic, not a FullTopic or an MQTT wildcard."""
    value = value.strip()
    if not value or any(c in value for c in "/+# \t\r\n"):
        raise ValueError("Use the Topic configured in Tasmota, e.g. tasmota_4232F0")
    return value


def decode_state(payload):
    """Ignore unrelated responses; accept partial state and malformed input safely."""
    try:
        data = json.loads(payload)
    except (ValueError, TypeError, UnicodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {key: value for key, value in data.items()
            if key in ("PT2322", "PT2323") and isinstance(value, dict)}


def as_bool(value):
    """Convert Tasmota ON/OFF strings without treating OFF as true."""
    if value in (True, 1, "ON", "On", "on"):
        return True
    if value in (False, 0, "OFF", "Off", "off"):
        return False
    return None


def normalize_processor(values):
    """Normalize legacy short command responses to telemetry field names."""
    aliases = {"VL": "Volume", "FL": "FrontLeft", "FR": "FrontRight",
               "CT": "Center", "SB": "Subwoofer", "RL": "RearLeft", "RR": "RearRight"}
    return {aliases.get(key, key): value for key, value in values.items()}
