import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.exceptions import PlatformNotReady
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY)

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'lightwave2'
CONF_REFRESH_KEY = 'refresh_key'
CONF_BACKEND = 'backend'
LIGHTWAVE_LINK2 = 'lightwave_link2'
LIGHTWAVE_BACKEND = 'lightwave_backend'
LIGHTWAVE_ENTITIES = "lightwave_entities"
BACKEND_EMULATED = 'emulated'
BACKEND_PUBLIC = 'public'
SERVICE_SETLEDRGB = 'set_led_rgb'


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Any({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_BACKEND): vol.In([BACKEND_EMULATED, BACKEND_PUBLIC])
    },
        {
            vol.Required(CONF_API_KEY): cv.string,
            vol.Required(CONF_REFRESH_KEY): cv.string,
            vol.Optional(CONF_BACKEND): vol.In([BACKEND_EMULATED, BACKEND_PUBLIC])
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
        entity_ids = call.data.get("entity_id")
        entities =  hass.data[LIGHTWAVE_ENTITIES]
        entities = [e for e in entities if e.entity_id in entity_ids]
        rgb = call.data.get("rgb")
        if str(rgb)[0:1] == "#":
            rgb = int("0x" + rgb[1:7], 16)
        else:
            rgb = int(str(rgb), 0)
        _LOGGER.debug("Received service call %s, rgb %s, rgb as hex %s", entity_ids, rgb, hex(rgb) )
        for ent in entities:
            _LOGGER.debug("Matched entites %s", ent)
            await ent.async_set_rgb(led_rgb=rgb)

    email = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]

    if CONF_BACKEND not in config[DOMAIN] or \
            config[DOMAIN][CONF_BACKEND] == BACKEND_EMULATED:
        hass.data[LIGHTWAVE_BACKEND] = BACKEND_EMULATED
        link = lightwave2.LWLink2(email, password)
    else:
        hass.data[LIGHTWAVE_BACKEND] = BACKEND_PUBLIC
        link = lightwave2.LWLink2Public(email, password)

    connected = await link.async_connect(max_tries = 1)
    if not connected:
        return False
    await link.async_get_hierarchy()

    hass.data[LIGHTWAVE_LINK2] = link
    hass.data[LIGHTWAVE_ENTITIES] = []

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
