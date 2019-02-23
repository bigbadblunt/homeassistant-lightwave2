import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY)

REQUIREMENTS = ['lightwave2==0.3.1']

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'lightwave2'
LIGHTWAVE_LINK2 = 'lightwave_link2'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Any({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional('backend'): 'emulated'
    },
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required('refresh_key'): cv.string,
        vol.Required('backend'): 'public'
    }
    )
})

async def async_setup(hass, config):
    """Setup Lightwave hub. Uses undocumented websocket API."""
    from lightwave2 import lightwave2

    email = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]
    
    link = lightwave2.LWLink2(email, password)
    await link.async_connect()
    hass.data[LIGHTWAVE_LINK2] = link
    await link.async_get_hierarchy()

    hass.async_create_task(async_load_platform(hass, 'switch', DOMAIN, None, config))
    hass.async_create_task(async_load_platform(hass, 'light', DOMAIN, None, config))
    hass.async_create_task(async_load_platform(hass, 'climate', DOMAIN, None, config))
    return True


