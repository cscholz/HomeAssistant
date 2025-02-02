import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from .const import DOMAIN

DATA_SCHEMA = vol.Schema({
    vol.Required("name", default="Blauberg Vento"): str,
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Required("deviceId"): str,
    vol.Required(CONF_PASSWORD): str,
})

class BlaubergVentoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blauberg Vento Fan."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Hier könnte ggf. eine Verbindung getestet werden.
            return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )
