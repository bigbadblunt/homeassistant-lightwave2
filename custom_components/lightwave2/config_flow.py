import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD)
from .const import DOMAIN, CONF_PUBLICAPI
import voluptuous as vol
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

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="(Imported from configuration.yaml)", data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return Lightwave2OptionsFlowHandler(config_entry)

class Lightwave2OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        if self.config_entry.options:
            options = self.config_entry.options
        else:
            options = {
                CONF_PUBLICAPI: False,
            }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({
                vol.Optional(CONF_PUBLICAPI, options.get(CONF_PUBLICAPI)): bool
            })
        )