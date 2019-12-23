import logging
from homeassistant import config_entries
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD)
from .const import DOMAIN
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
_LOGGER = logging.getLogger(__name__)

class Lightwave2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=()):

        self._errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Lightwave 2", data=user_input)

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str
            })
        )

    async def async_step_import(self, user_input):
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        _LOGGER.debug("yaml config flow", user_input)
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="(Imported from configuration.yaml)", data={})