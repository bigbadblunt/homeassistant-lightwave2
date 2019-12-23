from homeassistant import config_entries
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY)
from .const import DOMAIN
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
#from .const import DOMAIN #TODO move constants to const.py

class Lightwave2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=()):

        self._errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str
            })
        )