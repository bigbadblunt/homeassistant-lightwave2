import logging
from custom_components.lightwave2 import LIGHTWAVE_LINK2, LIGHTWAVE_BACKEND, BACKEND_EMULATED, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK
from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, HVAC_MODE_HEAT, SUPPORT_TARGET_TEMPERATURE, CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE, CURRENT_HVAC_OFF)
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT, STATE_OFF)
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave thermostats."""

    climates = []
    link = hass.data[LIGHTWAVE_LINK2]

    if hass.data[LIGHTWAVE_BACKEND] == BACKEND_EMULATED:
        url = None
    else:
        url = hass.data[LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_climates():
        climates.append(LWRF2Climate(name, featureset_id, link, url))

    hass.data[LIGHTWAVE_ENTITIES].extend(climates)
    async_add_entities(climates)


class LWRF2Climate(ClimateDevice):
    """Representation of a LightWaveRF thermostat."""

    def __init__(self, name, featureset_id, link, url=None):
        self._name = name
        _LOGGER.debug("Adding climate: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._support_flags = SUPPORT_TARGET_TEMPERATURE
        self._valve_level = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "valveLevel"][1]
        self._onoff = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "heatState"][1]
        self._temperature = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "temperature"][1] / 10
        self._target_temperature = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "targetTemperature"][1] / 10
        self._temperature_scale = TEMP_CELSIUS

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)
        if self._url is not None:
            for featurename in self._lwlink.get_featureset_by_id(self._featureset_id).features:
                featureid = self._lwlink.get_featureset_by_id(self._featureset_id).features[featurename][0]
                _LOGGER.debug("Registering webhook: %s %s", featurename, featureid.replace("+", "P"))
                req = await self._lwlink.async_register_webhook(self._url, featureid, "hass" + featureid.replace("+", "P"), overwrite = True)

    @callback
    def async_update_callback(self):
        """Update the component's state."""
        self.async_schedule_update_ha_state(True)

    @property
    def should_poll(self):
        """Lightwave2 library will push state, no polling needed"""
        return False

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

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
    def name(self):
        """Return the name, if any."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_scale

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        if self._onoff == 1:
            return HVAC_MODE_HEAT
        else:
            return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def hvac_action(self):
        if self._onoff == 0:
            return CURRENT_HVAC_OFF
        elif self._valve_level == 100:
            return CURRENT_HVAC_HEAT
        else:
            return CURRENT_HVAC_IDLE

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            self._target_temperature = kwargs[ATTR_TEMPERATURE]

        await self._lwlink.async_set_temperature_by_featureset_id(
            self._featureset_id, self._target_temperature)

    async def async_set_hvac_mode(self, hvac_mode):
        feature_id = self._lwlink.get_featureset_by_id(self._featureset_id).features['heatState'][0]
        if hvac_mode == HVAC_MODE_OFF:
            self._lwlink.async_write_feature(feature_id, 0)
        else:
            self._lwlink.async_write_feature(feature_id, 0)

    async def async_update(self):
        """Update state"""
        self._valve_level = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "valveLevel"][1]
        self._onoff = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "heatState"][1]
        self._temperature = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "temperature"][1] / 10
        self._target_temperature = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "targetTemperature"][1] / 10

    @property
    def device_state_attributes(self):
        """Return the optional state attributes."""

        attribs = {}

        for featurename, featuredict in self._lwlink.get_featureset_by_id(
                self._featureset_id).features.items():
            attribs['lwrf_' + featurename] = featuredict[1]

        attribs['lrwf_product_code'] = self._lwlink.get_featureset_by_id(
            self._featureset_id).product_code

        return attribs