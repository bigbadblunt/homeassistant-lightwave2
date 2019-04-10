import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD)

REQUIREMENTS = ['lightwave2==0.3.12']

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'lightwave2'
LIGHTWAVE_LINK2 = 'lightwave_link2'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    }
    )
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Setup Lightwave hub. Uses undocumented websocket API."""
    from lightwave2 import lightwave2
    _LOGGER.debug("Imported lightwave2 library version %s", REQUIREMENTS)

    email = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]

    link = lightwave2.LWLink2(email, password)
    await link.async_connect()

    hass.data[LIGHTWAVE_LINK2] = link
    await link.async_get_hierarchy()

    hass.async_create_task(
        async_load_platform(hass, 'switch', DOMAIN, None, config))
    hass.async_create_task(
        async_load_platform(hass, 'light', DOMAIN, None, config))
    hass.async_create_task(
        async_load_platform(hass, 'climate', DOMAIN, None, config))

    return True
