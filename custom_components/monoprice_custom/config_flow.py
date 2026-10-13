"""Configure the Tasmota MQTT Topic and optional PT2323."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_TOPIC, CONF_PT2323
from .protocol import validate_topic

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                user_input[CONF_TOPIC] = validate_topic(user_input[CONF_TOPIC])
            except ValueError:
                errors[CONF_TOPIC] = "invalid_topic"
            else:
                await self.async_set_unique_id(user_input[CONF_TOPIC])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"SabidosReceiver {user_input[CONF_TOPIC]}", data=user_input)
        return self.async_show_form(step_id="user", errors=errors, data_schema=vol.Schema({
            vol.Required(CONF_TOPIC): str, vol.Optional(CONF_PT2323, default=False): bool}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ReceiverOptionsFlow()

class ReceiverOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        enabled = self.config_entry.options.get(CONF_PT2323, self.config_entry.data.get(CONF_PT2323, False))
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Optional(CONF_PT2323, default=enabled): bool}))
