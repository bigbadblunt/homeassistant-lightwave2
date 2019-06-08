import logging
from custom_components.lightwave2 import LIGHTWAVE_LINK2, LIGHTWAVE_BACKEND, BACKEND_EMULATED, BACKEND_PUBLIC
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light)
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)
ATTR_CURRENT_POWER_W = "current_power_w"

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave lights."""

    lights = []
    link = hass.data[LIGHTWAVE_LINK2]

    if hass.data[LIGHTWAVE_BACKEND] == BACKEND_EMULATED:
        url = None
    else:
        hass.components.webhook.async_generate_id()
        _LOGGER.debug("Generated webhook: %s ", webhook_id)
        hass.components.webhook.async_register(
            'lightwave2', 'Lightwave lights webhook', webhook_id, handle_webhook)
        url = hass.components.webhook.async_generate_url(webhook_id)
        _LOGGER.debug("Webhook URL: %s ", url)

    for featureset_id, name in link.get_lights():
        lights.append(LWRF2Light(name, featureset_id, link, url))

    async_add_entities(lights)

async def handle_webhook(hass, webhook_id, request):
    """Handle webhook callback."""
    body = await request.json()
    _LOGGER.debug("Received webhook: %s ", body)
    # Do something with the data

class LWRF2Light(Light):
    """Representation of a LightWaveRF light."""

    def __init__(self, name, featureset_id, link, url=None):
        self._name = name
        _LOGGER.debug("Adding light: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "switch"][1]
        self._brightness = int(round(
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "dimLevel"][1] / 100 * 255))
        self._gen2 = self._lwlink.get_featureset_by_id(
            self._featureset_id).is_gen2()
        self._reports_power = self._lwlink.get_featureset_by_id(
            self._featureset_id).reports_power()
        self._power = None
        if self._reports_power:
            self._power = self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "power"][1]

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)
        if self._url is not None:
            for featurename in self._lwlink.get_featureset_by_id(self._featureset_id).features:
                featureid = self._lwlink.get_featureset_by_id(self._featureset_id).features[featurename][0]
                _LOGGER.debug("Registering webhook: %s %s", featurename, featureid)
                req = await self._lwlink.async_register_webhook(self._url, featureid, "hass" + featureid, overwrite = True)

    @callback
    def async_update_callback(self):
        """Update the component's state."""
        self.async_schedule_update_ha_state(True)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def should_poll(self):
        """Lightwave2 library will push state, no polling needed"""
        return False

    @property
    def assumed_state(self):
        """Gen 2 devices will report state changes, gen 1 doesn't"""
        return not self._gen2

    async def async_update(self):
        """Update state"""
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "switch"][1]
        self._brightness = int(round(
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "dimLevel"][1] / 100 * 255))
        if self._reports_power:
            self._power = self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "power"][1]

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the group lights."""
        return self._brightness

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            'product_code': self._lwlink.get_featureset_by_id(
                self._featureset_id).product_code
        }

    @property
    def is_on(self):
        """Lightwave switch is on state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the LightWave light on."""
        self._state = True
        _LOGGER.debug("Setting brightness %s %s", self._brightness, int(self._brightness / 255 * 100))
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        await self._lwlink.async_set_brightness_by_featureset_id(
            self._featureset_id, int(round(self._brightness / 255 * 100)))
        await self._lwlink.async_turn_on_by_featureset_id(self._featureset_id)

        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the LightWave light off."""
        self._state = False
        await self._lwlink.async_turn_off_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

    @property
    def current_power_w(self):
        """Power consumption"""
        return self._power

    @property
    def device_state_attributes(self):
        """Return the optional state attributes."""

        attribs = {}

        if self._power is not None:
            attribs[ATTR_CURRENT_POWER_W] = self._power

        return attribs