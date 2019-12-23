from homeassistant import config_entries
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
#from .const import DOMAIN #TODO move constants to const.py

class Lightwave2ConfigFlow(config_entries.ConfigFlow, domain='lightwave2'):

    async def async_step_user(self, info):
        if info is not None:
            # process info

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string
            })
        )