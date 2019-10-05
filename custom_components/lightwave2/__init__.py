import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY)

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'lightwave2'
CONF_REFRESH_KEY = 'refresh_key'
CONF_BACKEND = 'backend'
LIGHTWAVE_LINK2 = 'lightwave_link2'
LIGHTWAVE_BACKEND = 'lightwave_backend'
BACKEND_EMULATED = 'emulated'
BACKEND_PUBLIC = 'public'
SERVICE_SETLEDRGB = 'set_led_rgb'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Any({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_BACKEND): [BACKEND_EMULATED, BACKEND_PUBLIC]
    },
        {
            vol.Required(CONF_API_KEY): cv.string,
            vol.Required(CONF_REFRESH_KEY): cv.string,
            vol.Optional(CONF_BACKEND): [BACKEND_EMULATED, BACKEND_PUBLIC]
        }
    )
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Setup Lightwave hub. Uses undocumented websocket API."""
    from lightwave2 import lightwave2
    #_LOGGER.debug("Imported lightwave2 library version %s", REQUIREMENTS)

    component = EntityComponent(
        _LOGGER, DOMAIN, hass
    )

    async def service_handle(call):
        list = await component.async_extract_from_service(call)
        _LOGGER.debug("%s", call)
        entity_ids = call.data.get("entity_id")
        rgb = call.data.get("rgb")
        _LOGGER.debug("Received service call %s, rgb %s", entity_ids, rgb )


    email = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]

    if CONF_BACKEND not in config[DOMAIN] or \
            config[DOMAIN][CONF_BACKEND] == BACKEND_EMULATED:
        hass.data[LIGHTWAVE_BACKEND] = BACKEND_EMULATED
        link = lightwave2.LWLink2(email, password)
    else:
        hass.data[LIGHTWAVE_BACKEND] = BACKEND_PUBLIC
        link = lightwave2.LWLink2Public(email, password)
    await link.async_connect()

    hass.data[LIGHTWAVE_LINK2] = link

    await link.async_get_hierarchy()

    hass.async_create_task(
        async_load_platform(hass, 'switch', DOMAIN, None, config))
    hass.async_create_task(
        async_load_platform(hass, 'light', DOMAIN, None, config))
    hass.async_create_task(
        async_load_platform(hass, 'climate', DOMAIN, None, config))
    hass.async_create_task(
        async_load_platform(hass, 'cover', DOMAIN, None, config))

    hass.services.async_register(DOMAIN, SERVICE_SETLEDRGB, service_handle)

    return True
