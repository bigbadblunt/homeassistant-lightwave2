import logging

from .const import DOMAIN, CONF_PUBLICAPI, CONF_DEBUG, CONF_RECONNECT, LIGHTWAVE_LINK2,  LIGHTWAVE_ENTITIES, \
    LIGHTWAVE_WEBHOOK, LIGHTWAVE_WEBHOOKID, LIGHTWAVE_LINKID
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
            if ent.hass is not None:
                ent.async_schedule_update_ha_state(True)

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

    force_reconnect_secs = config_entry.options.get(CONF_RECONNECT, False)
    _LOGGER.debug("Forced reconnection setting: %s ", force_reconnect_secs)

    if not await link.async_connect(max_tries = 1, force_keep_alive_secs=force_reconnect_secs):
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
        await link.async_register_webhook_all(url, LIGHTWAVE_WEBHOOK, overwrite = True)

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK] = url

    device_registry = await dr.async_get_registry(hass)
    for featureset_id, hubname in link.get_hubs():
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, featureset_id)},
            manufacturer= "Lightwave RF",
            name=hubname,
            model=link.featuresets[featureset_id].product_code
        )
        hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINKID] = featureset_id

    # Ensure every device associated with this config entry still exists
    # otherwise remove the device (and thus entities).
    for device_entry in dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    ):
        for identifier in device_entry.identifiers:
            _LOGGER.debug("Identifier found in config file %s ", identifier[1])
            if identifier[1] in link.featuresets:
                _LOGGER.debug("Identifier matched")
                break
        else:
            _LOGGER.debug("Identifier not matched, removing device")
            device_registry.async_remove_device(device_entry.id)

    forward_setup = hass.config_entries.async_forward_entry_setup
    hass.async_create_task(forward_setup(config_entry, "switch"))
    hass.async_create_task(forward_setup(config_entry, "light"))
    hass.async_create_task(forward_setup(config_entry, "climate"))
    hass.async_create_task(forward_setup(config_entry, "cover"))
    hass.async_create_task(forward_setup(config_entry, "binary_sensor"))
    hass.async_create_task(forward_setup(config_entry, "sensor"))
    hass.async_create_task(forward_setup(config_entry, "lock"))

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
    await hass.config_entries.async_forward_entry_unload(config_entry, "lock")

async def reload_lw(hass, config_entry):

    await async_remove_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)