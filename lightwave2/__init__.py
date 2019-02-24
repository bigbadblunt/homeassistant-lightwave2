import logging
import os

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY)

REQUIREMENTS = ['lightwave2==0.3.6']

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'lightwave2'
CONF_REFRESH_KEY = 'refresh_key'
CONF_BACKEND = 'backend'
LIGHTWAVE_LINK2 = 'lightwave_link2'
BACKEND_EMULATED = 'emulated'
BACKEND_PUBLIC = 'public'
TOKEN_FILE = '.{}.token'.format(DOMAIN)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Any({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_BACKEND): BACKEND_EMULATED
    },
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_REFRESH_KEY): cv.string,
        vol.Required(CONF_BACKEND): BACKEND_PUBLIC
    }
    )
}, extra=vol.ALLOW_EXTRA)

async def handle_webhook(hass, webhook_id, request):
    """Handle webhook callback."""
    body = await request.json()
    # Do something with the data

async def async_setup(hass, config):
    """Setup Lightwave hub. Uses undocumented websocket API."""
    from lightwave2 import lightwave2
    if CONF_BACKEND not in config[DOMAIN] or config[DOMAIN][CONF_BACKEND] == BACKEND_EMULATED:
        email = config[DOMAIN][CONF_USERNAME]
        password = config[DOMAIN][CONF_PASSWORD]
    
        link = lightwave2.LWLink2(email, password)
        await link.async_connect()
    else:
        api_key = config[DOMAIN][CONF_API_KEY]
        refresh_key = config[DOMAIN][CONF_REFRESH_KEY]

        token_file = hass.config.path(TOKEN_FILE)
        if os.path.isfile(token_file):
            with open(token_file, "r") as myfile:
                refresh_key_file = myfile.readline()
            link = lightwave2.LWLink2Public(api_key, refresh_key_file)
            await link.async_connect()
            #TODO fallback to config if can't auth
            with open(token_file, "w") as myfile:
                myfile.write(link._refresh_token)
        else:
            link = lightwave2.LWLink2Public(api_key, refresh_key)
            await link.async_connect()
            with open(token_file, "w") as myfile:
                myfile.write(link._refresh_token)

    hass.data[LIGHTWAVE_LINK2] = link
    await link.async_get_hierarchy()

    if CONF_BACKEND in config[DOMAIN] and config[DOMAIN][CONF_BACKEND] == BACKEND_PUBLIC:

        webhook_id = hass.components.webhook.async_generate_id()
        hass.components.webhook.async_register(DOMAIN, 'Name of the webhook', webhook_id, handle_webhook)
        webby = hass.components.webhook.async_generate_url(webhook_id)
        _LOGGER.debug(webby)

    hass.async_create_task(async_load_platform(hass, 'switch', DOMAIN, None, config))
    hass.async_create_task(async_load_platform(hass, 'light', DOMAIN, None, config))
    hass.async_create_task(async_load_platform(hass, 'climate', DOMAIN, None, config))

    return True


