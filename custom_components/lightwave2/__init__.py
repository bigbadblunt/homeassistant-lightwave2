#TODO: expose link and attributes to HA
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_API_KEY)
from homeassistant.config_entries import SOURCE_IMPORT

_LOGGER = logging.getLogger(__name__)
CONF_REFRESH_KEY = 'refresh_key'
CONF_BACKEND = 'backend'
LIGHTWAVE_LINK2 = 'lightwave_link2'
LIGHTWAVE_BACKEND = 'lightwave_backend'
LIGHTWAVE_ENTITIES = "lightwave_entities"
LIGHTWAVE_WEBHOOK = 'lightwave_webhook'
BACKEND_EMULATED = 'emulated'
BACKEND_PUBLIC = 'public'
SERVICE_SETLEDRGB = 'set_led_rgb'
SERVICE_SETLOCKED = 'lock'
SERVICE_SETUNLOCKED = 'unlock'

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

async def handle_webhook(hass, webhook_id, request):
    """Handle webhook callback."""
    link = hass.data[LIGHTWAVE_LINK2]
    body = await request.json()
    _LOGGER.debug("Received webhook: %s ", body)
    link.process_webhook_received(body)
    for ent in hass.data[LIGHTWAVE_ENTITIES]:
        ent.async_schedule_update_ha_state(True)

async def async_setup(hass, config):
    '''This checks if there is configuration infop in configuration.yaml, if so it translates and passes it to the config handler'''
    if DOMAIN not in config:
        return True

    email = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_USERNAME: email, CONF_PASSWORD: password}
        )
    )
    return True

async def async_setup_entry(hass, config_entry):
    """Setup Lightwave hub. Uses undocumented websocket API."""
    from lightwave2 import lightwave2

    async def service_handle_led(call):
        entity_ids = call.data.get("entity_id")
        entities = hass.data[LIGHTWAVE_ENTITIES]
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

    async def service_handle_lock(call):
        entity_ids = call.data.get("entity_id")
        entities = hass.data[LIGHTWAVE_ENTITIES]
        entities = [e for e in entities if e.entity_id in entity_ids]

        for ent in entities:
            feature_id = link.get_featureset_by_id(ent._featureset_id).features['protection'][0]
            _LOGGER.debug("Received service call lock")
            _LOGGER.debug("Setting feature ID: %s ", feature_id)
            await link.async_write_feature(feature_id, 1)

    async def service_handle_unlock(call):
        entity_ids = call.data.get("entity_id")
        entities = hass.data[LIGHTWAVE_ENTITIES]
        entities = [e for e in entities if e.entity_id in entity_ids]

        for ent in entities:
            feature_id = link.get_featureset_by_id(ent._featureset_id).features['protection'][0]
            _LOGGER.debug("Received service call unlock")
            _LOGGER.debug("Setting feature ID: %s ", feature_id)
            await link.async_write_feature(feature_id, 0)

    email = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]

    hass.data[LIGHTWAVE_BACKEND] = BACKEND_EMULATED
    link = lightwave2.LWLink2(email, password)

    if not await link.async_connect(max_tries = 1):
        return False
    await link.async_get_hierarchy()

    hass.data[LIGHTWAVE_LINK2] = link
    hass.data[LIGHTWAVE_ENTITIES] = []
    if hass.data[LIGHTWAVE_BACKEND] == BACKEND_EMULATED:
        url = None
    else:
        webhook_id = hass.components.webhook.async_generate_id()
        _LOGGER.debug("Generated webhook: %s ", webhook_id)
        hass.components.webhook.async_register(
            'lightwave2', 'Lightwave webhook', webhook_id, handle_webhook)
        url = hass.components.webhook.async_generate_url(webhook_id)
        _LOGGER.debug("Webhook URL: %s ", url)
    hass.data[LIGHTWAVE_WEBHOOK] = url

    forward_setup = hass.config_entries.async_forward_entry_setup
    hass.async_create_task(forward_setup(config_entry, "switch"))
    hass.async_create_task(forward_setup(config_entry, "light"))
    hass.async_create_task(forward_setup(config_entry, "climate"))
    hass.async_create_task(forward_setup(config_entry, "cover"))

    hass.services.async_register(DOMAIN, SERVICE_SETLEDRGB, service_handle_led)
    hass.services.async_register(DOMAIN, SERVICE_SETLEDRGB, service_handle_lock)
    hass.services.async_register(DOMAIN, SERVICE_SETLEDRGB, service_handle_unlock)

    return True