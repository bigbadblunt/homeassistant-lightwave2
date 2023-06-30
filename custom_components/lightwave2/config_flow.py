import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD)
from .const import DOMAIN, CONF_PUBLICAPI, CONF_HOMEKIT
import voluptuous as vol
_LOGGER = logging.getLogger(__name__)

class Lightwave2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=()):

        self._errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            return self.async_create_entry(title=user_input[CONF_USERNAME], data=user_input)

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str
            })
        )

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
            _LOGGER.debug("Received user input: %s ", user_input)
            return self.async_create_entry(title="", data=user_input)

        if self.config_entry.options:
            options = self.config_entry.options
            _LOGGER.debug("Creating options form using existing options: %s ", options)
        else:
            options = {
                CONF_PUBLICAPI: False,
                CONF_HOMEKIT: False
            }
            _LOGGER.debug("Creating options form using default options")

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({
                vol.Optional(CONF_PUBLICAPI, default=options.get(CONF_PUBLICAPI)): bool,
                vol.Optional(CONF_HOMEKIT, default=options.get(CONF_HOMEKIT)): bool
            })
        )