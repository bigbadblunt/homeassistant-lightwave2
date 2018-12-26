import custom_components.lightwave2 as lightwave2

from custom_components.lightwave2 import LIGHTWAVE_LINK2
from homeassistant.components.climate import (
    STATE_AUTO, STATE_COOL, STATE_HEAT, STATE_ECO, ClimateDevice,
    PLATFORM_SCHEMA, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW,
    ATTR_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_HIGH, SUPPORT_TARGET_TEMPERATURE_LOW,
    SUPPORT_OPERATION_MODE, SUPPORT_AWAY_MODE, SUPPORT_FAN_MODE)
from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT,
    CONF_SCAN_INTERVAL, STATE_ON, STATE_OFF, STATE_UNKNOWN)
from homeassistant.core import callback
import logging

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ['lightwave2']

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave thermostats."""

    climates = []
    link = hass.data[LIGHTWAVE_LINK2]

    for device_id, name in link.get_climates():
        climates.append(LWRF2Climate(name, device_id, link))
    _LOGGER.debug(link.get_climates())
    async_add_entities(climates)

class LWRF2Climate(ClimateDevice):
    """Representation of a LightWaveRF thermostat."""

    def __init__(self, name, device_id, link):
        self._name = name
        self._device_id = device_id
        self._lwlink = link
        self._support_flags = SUPPORT_TARGET_TEMPERATURE
        self._valve_level = self._lwlink.get_device_by_id(self._device_id).features["valveLevel"][1]
        self._temperature = self._lwlink.get_device_by_id(self._device_id).features["temperature"][1] / 10
        self._target_temperature = self._lwlink.get_device_by_id(self._device_id).features["targetTemperature"][1] / 10
        self._temperature_scale = TEMP_CELSIUS

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

    @callback
    def async_update_callback(self):
        """Update the component's state."""
        self.async_schedule_update_ha_state(True)

    @property
    def should_poll(self):
        """Gen 2 hub tracks state, so we need to update"""
        return False

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._device_id

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            'product_code': self._lwlink.get_device_by_id(self._device_id).product_code
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
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._valve_level == 100:
            return STATE_HEAT
        else:
            return STATE_OFF

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs):
        _LOGGER.debug(kwargs)
        if ATTR_TEMPERATURE in kwargs:
            self._target_temperature = kwargs[ATTR_TEMPERATURE]

        await self._lwlink.async_set_temperature_by_device_id(self._device_id, self._target_temperature)

    async def async_update(self):
        """Update state"""
        self._valve_level = self._lwlink.get_device_by_id(self._device_id).features["valveLevel"][1]
        self._temperature = self._lwlink.get_device_by_id(self._device_id).features["temperature"][1] / 10
        self._target_temperature = self._lwlink.get_device_by_id(self._device_id).features["targetTemperature"][1] / 10
