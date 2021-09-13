import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK
try:
    from homeassistant.components.light import LightEntity
except ImportError:
    from homeassistant.components.light import Light as LightEntity
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS)
from homeassistant.core import callback
from .const import DOMAIN

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)
ATTR_CURRENT_POWER_W = "current_power_w"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave lights."""

    lights = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_lights():
        lights.append(LWRF2Light(name, featureset_id, link, url, hass))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(lights)
    async_add_entities(lights)

class LWRF2Light(LightEntity):
    """Representation of a LightWaveRF light."""

    def __init__(self, name, featureset_id, link, url, hass):
        self._name = name
        self._hass = hass
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
        self._has_led = self._lwlink.get_featureset_by_id(
            self._featureset_id).has_led()
        self._ledrgb = None
        if self._has_led:
            self._ledrgb = self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "rgbColor"][1]

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)
        if self._url is not None:
            for featurename in self._lwlink.get_featureset_by_id(self._featureset_id).features:
                featureid = self._lwlink.get_featureset_by_id(self._featureset_id).features[featurename][0]
                _LOGGER.debug("Registering webhook: %s %s", featurename, featureid.replace("+", "P"))
                req = await self._lwlink.async_register_webhook(self._url, featureid, "hass" + featureid.replace("+", "P"), overwrite = True)

    #TODO add async_will_remove_from_hass() to clean up

    @callback
    def async_update_callback(self, **kwargs):
        """Update the component's state."""
        _LOGGER.debug(kwargs["feature"])
        _LOGGER.debug(self._lwlink.get_featureset_by_featureid(kwargs["feature_id"]))
        _LOGGER.debug(self._featureset_id)
        _LOGGER.debug(self._lwlink.get_featureset_by_featureid(kwargs["feature_id"]) == self._featureset_id)
        if kwargs["feature"] == "uiButtonPair" and self._lwlink.get_featureset_by_featureid(kwargs["feature_id"]) == self._featureset_id:
            self._hass.bus.fire(
            "lightwave2.click",
            {"entity_id": self.entity_id, "code": kwargs["new_value"]},
        )
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
        if self._has_led:
            self._ledrgb = self._lwlink.get_featureset_by_id(
                self._featureset_id).features[
                "rgbColor"][1]

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
    def is_on(self):
        """Lightwave switch is on state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the LightWave light on."""
        _LOGGER.debug("HA light.turn_on received, kwargs: %s", kwargs)

        if ATTR_BRIGHTNESS in kwargs:
            _LOGGER.debug("Changing brightness from %s to %s (%s%%)", self._brightness, kwargs[ATTR_BRIGHTNESS], int(kwargs[ATTR_BRIGHTNESS] / 255 * 100))
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            await self._lwlink.async_set_brightness_by_featureset_id(
                self._featureset_id, int(round(self._brightness / 255 * 100)))

        self._state = True
        await self._lwlink.async_turn_on_by_featureset_id(self._featureset_id)

        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the LightWave light off."""
        _LOGGER.debug("HA light.turn_off received, kwargs: %s", kwargs)

        self._state = False
        await self._lwlink.async_turn_off_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

    async def async_set_rgb(self, led_rgb):
        self._ledrgb = led_rgb
        await self._lwlink.async_set_led_rgb_by_featureset_id(self._featureset_id, self._ledrgb)

    @property
    def current_power_w(self):
        """Power consumption"""
        return self._power

    @property
    def device_state_attributes(self):
        """Return the optional state attributes."""

        attribs = {}

        for featurename, featuredict in self._lwlink.get_featureset_by_id(self._featureset_id).features.items():
            attribs['lwrf_' + featurename] = featuredict[1]

        attribs['lrwf_product_code'] = self._lwlink.get_featureset_by_id(self._featureset_id).product_code

        if self._power is not None:
            attribs[ATTR_CURRENT_POWER_W] = self._power

        return attribs

    @property
    def device_info(self):
        return {
            'identifiers': {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            'name': self.name,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.get_featureset_by_id(
                self._featureset_id).product_code
            #TODO 'via_device': (hue.DOMAIN, self.api.bridgeid),
        }