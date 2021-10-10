#TODO: expose link and attributes to HA
import logging
import voluptuous as vol

from .const import DOMAIN, CONF_PUBLICAPI, CONF_DEBUG, LIGHTWAVE_LINK2,  LIGHTWAVE_ENTITIES, \
    LIGHTWAVE_WEBHOOK, LIGHTWAVE_WEBHOOKID, SERVICE_SETLEDRGB, SERVICE_SETLOCKED, SERVICE_SETUNLOCKED, SERVICE_SETBRIGHTNESS
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD)
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)


async def handle_webhook(hass, webhook_id, request):
    """Handle webhook callback."""
    for entry_id in hass.data[DOMAIN]:
        link = hass.data[DOMAIN][entry_id][LIGHTWAVE_LINK2]
        body = await request.json()
        _LOGGER.debug("Received webhook: %s ", body)
        link.process_webhook_received(body)
        for ent in hass.data[DOMAIN][entry_id][LIGHTWAVE_ENTITIES]:
            ent.async_schedule_update_ha_state(True)

async def async_setup(hass, config):

    async def service_handle_led(call):
        entity_ids = call.data.get("entity_id")
        for entry_id in hass.data[DOMAIN]:
            entities = hass.data[DOMAIN][entry_id][LIGHTWAVE_ENTITIES]
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
        for entry_id in hass.data[DOMAIN]:
                
            entities = hass.data[DOMAIN][entry_id][LIGHTWAVE_ENTITIES]
            entities = [e for e in entities if e.entity_id in entity_ids]
            
            link = hass.data[DOMAIN][entry_id][LIGHTWAVE_LINK2]

            for ent in entities:
                feature_id = link.get_featureset_by_id(ent._featureset_id).features['protection'][0]
                _LOGGER.debug("Received service call lock")
                _LOGGER.debug("Setting feature ID: %s ", feature_id)
                await link.async_write_feature(feature_id, 1)

    async def service_handle_unlock(call):
        entity_ids = call.data.get("entity_id")
        for entry_id in hass.data[DOMAIN]:

            entities = hass.data[DOMAIN][entry_id][LIGHTWAVE_ENTITIES]
            entities = [e for e in entities if e.entity_id in entity_ids]

            link = hass.data[DOMAIN][entry_id][LIGHTWAVE_LINK2]

            for ent in entities:
                feature_id = link.get_featureset_by_id(ent._featureset_id).features['protection'][0]
                _LOGGER.debug("Received service call unlock")
                _LOGGER.debug("Setting feature ID: %s ", feature_id)
                await link.async_write_feature(feature_id, 0)

    async def service_handle_brightness(call):
        entity_ids = call.data.get("entity_id")
        for entry_id in hass.data[DOMAIN]:

            entities = hass.data[DOMAIN][entry_id][LIGHTWAVE_ENTITIES]
            entities = [e for e in entities if e.entity_id in entity_ids]
            brightness = int(round(call.data.get("brightness") / 255 * 100))

            link = hass.data[DOMAIN][entry_id][LIGHTWAVE_LINK2]

            for ent in entities:
                feature_id = link.get_featureset_by_id(ent._featureset_id).features['dimLevel'][0]
                _LOGGER.debug("Received service call set brightness")
                _LOGGER.debug("Setting feature ID: %s ", feature_id)
                await link.async_write_feature(feature_id, brightness)
                await ent.async_update()

    hass.services.async_register(DOMAIN, SERVICE_SETLEDRGB, service_handle_led)
    hass.services.async_register(DOMAIN, SERVICE_SETLOCKED, service_handle_lock)
    hass.services.async_register(DOMAIN, SERVICE_SETUNLOCKED, service_handle_unlock)
    hass.services.async_register(DOMAIN, SERVICE_SETBRIGHTNESS, service_handle_brightness)

    return True

async def async_setup_entry(hass, config_entry):
    from lightwave2 import lightwave2

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(config_entry.entry_id, {})
    email = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    config_entry.add_update_listener(reload_lw)

    publicapi = config_entry.options.get(CONF_PUBLICAPI, False)
    if publicapi:
        _LOGGER.warning("Using Public API, this is experimental - if you have issues turn this off in the integration options")
        link = lightwave2.LWLink2Public(email, password)
    else:
        link = lightwave2.LWLink2(email, password)

    debugmode = config_entry.options.get(CONF_DEBUG, False)

    if debugmode:
        _LOGGER.warning("Logging turned on")
        _LOGGER.setLevel(logging.DEBUG)
        logging.getLogger("lightwave2").setLevel(logging.DEBUG)

    if not await link.async_connect(max_tries = 1):
        return False
    await link.async_get_hierarchy()

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2] = link
    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES] = []
    if not publicapi:
        url = None
    else:
        webhook_id = hass.components.webhook.async_generate_id()
        hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOKID] = webhook_id
        _LOGGER.debug("Generated webhook: %s ", webhook_id)
        hass.components.webhook.async_register(
            'lightwave2', 'Lightwave webhook', webhook_id, handle_webhook)
        url = hass.components.webhook.async_generate_url(webhook_id)
        _LOGGER.debug("Webhook URL: %s ", url)
    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK] = url

    device_registry = await dr.async_get_registry(hass)
    for featureset_id, hubname in link.get_hubs():
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, featureset_id)},
            manufacturer= "Lightwave RF",
            name=hubname,
            model=link.get_featureset_by_id(featureset_id).product_code
        )

    forward_setup = hass.config_entries.async_forward_entry_setup
    hass.async_create_task(forward_setup(config_entry, "switch"))
    hass.async_create_task(forward_setup(config_entry, "light"))
    hass.async_create_task(forward_setup(config_entry, "climate"))
    hass.async_create_task(forward_setup(config_entry, "cover"))
    hass.async_create_task(forward_setup(config_entry, "binary_sensor"))
    hass.async_create_task(forward_setup(config_entry, "sensor"))

    return True

async def async_remove_entry(hass, config_entry):
    if hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK] is not None:
        hass.components.webhook.async_unregister(hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOKID])
    await hass.config_entries.async_forward_entry_unload(config_entry, "switch")
    await hass.config_entries.async_forward_entry_unload(config_entry, "light")
    await hass.config_entries.async_forward_entry_unload(config_entry, "climate")
    await hass.config_entries.async_forward_entry_unload(config_entry, "cover")
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")

async def reload_lw(hass, config_entry):

    await async_remove_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)