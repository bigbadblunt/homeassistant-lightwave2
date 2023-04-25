import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES
try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, HVAC_MODE_HEAT, SUPPORT_TARGET_HUMIDITY, SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE, CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE, CURRENT_HVAC_OFF)
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT, STATE_OFF)
from homeassistant.core import callback
from .const import DOMAIN

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)
PRESET_NAMES = {"Auto": None, "20%": 20, "40%": 40, "60%": 60, "80%": 80, "100%": 100}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave thermostats."""

    climates = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]

    for featureset_id, name in link.get_climates():
        climates.append(LWRF2Climate(name, featureset_id, link))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(climates)
    async_add_entities(climates)


class LWRF2Climate(ClimateEntity):
    """Representation of a LightWaveRF thermostat."""

    def __init__(self, name, featureset_id, link):
        self._name = name
        _LOGGER.debug("Adding climate: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._trv = self._lwlink.featuresets[self._featureset_id].is_trv()
        self._has_humidity = 'targetHumidity' in self._lwlink.featuresets[self._featureset_id].features.keys()
        if self._has_humidity:
            self._support_flags = SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_HUMIDITY
        elif self._trv:
            self._support_flags = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
        else:
            self._support_flags = SUPPORT_TARGET_TEMPERATURE
        self._gen2 = self._lwlink.featuresets[self._featureset_id].is_gen2()

        if 'heatState' in self._lwlink.featuresets[self._featureset_id].features.keys():
            self._thermostat = False
        else:
            self._thermostat = True
            
        if 'valveLevel' in self._lwlink.featuresets[self._featureset_id].features.keys():
            self._valve_level = \
                self._lwlink.featuresets[self._featureset_id].features["valveLevel"].state
        elif self._thermostat:
            if self._lwlink.featuresets[self._featureset_id].features["callForHeat"].state is None:
                self._valve_level = 0
            else:    
                self._valve_level = \
                    self._lwlink.featuresets[self._featureset_id].features["callForHeat"].state * 100
        else:
            self._valve_level = 100

        if self._thermostat:
            self._onoff = 1
        else:
            self._onoff = \
                self._lwlink.featuresets[self._featureset_id].features["heatState"].state

        if self._lwlink.featuresets[self._featureset_id].features["temperature"].state is None:
            self._temperature = None
        else:
            self._temperature = \
                self._lwlink.featuresets[self._featureset_id].features["temperature"].state / 10

        if self._lwlink.featuresets[self._featureset_id].features["targetTemperature"].state is None:
            self._target_temperature = None
        else:
            self._target_temperature = \
                self._lwlink.featuresets[self._featureset_id].features["targetTemperature"].state / 10
        self._last_tt = self._target_temperature #Used to store the target temperature to revert to after boosting
        self._temperature_scale = TEMP_CELSIUS

        if self._has_humidity:
            self._humidity = \
                self._lwlink.featuresets[self._featureset_id].features["humidity"].state
            self._target_humidity = \
                self._lwlink.featuresets[self._featureset_id].features["targetHumidity"].state

        if self._valve_level == 100 and self._target_temperature < 40:
            self._preset_mode = "Auto"
        elif self._valve_level == 100:
            self._preset_mode = "100%"
        elif self._valve_level == 80:
            self._preset_mode = "80%"
        elif self._valve_level == 60:
            self._preset_mode = "60%"
        elif self._valve_level == 40:
            self._preset_mode = "40%"
        elif self._valve_level == 20:
            self._preset_mode = "20%"
        else:
            self._preset_mode = "Auto"
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

    @callback
    def async_update_callback(self, **kwargs):
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
    def current_humidity(self):
        """Return the current temperature."""
        if self._has_humidity:
            return self._humidity
        else:
            return False

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
        if self._thermostat:
            return [HVAC_MODE_HEAT]
        else:
            return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def hvac_action(self):
        if self._onoff == 0:
            return CURRENT_HVAC_OFF
        elif self._valve_level > 0:
            return CURRENT_HVAC_HEAT
        else:
            return CURRENT_HVAC_IDLE

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_humidity(self):
        """Return the temperature we try to reach."""
        if self._has_humidity:
            return self._target_humidity
        else:
            return False

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            self._target_temperature = kwargs[ATTR_TEMPERATURE]
            self._last_tt = self._target_temperature

        await self._lwlink.async_set_temperature_by_featureset_id(
            self._featureset_id, self._target_temperature)

    async def async_set_humidity(self, humidity):
        feature_id = self._lwlink.featuresets[self._featureset_id].features['targetHumidity'].id
        await self._lwlink.async_write_feature(feature_id, humidity)

    async def async_set_hvac_mode(self, hvac_mode):
        feature_id = self._lwlink.featuresets[self._featureset_id].features['heatState'].id
        _LOGGER.debug("Received mode set request: %s ", hvac_mode)
        _LOGGER.debug("Setting feature ID: %s ", feature_id)
        if hvac_mode == HVAC_MODE_OFF:
            await self._lwlink.async_write_feature(feature_id, 0)
        else:
            await self._lwlink.async_write_feature(feature_id, 1)

    async def async_update(self):
        """Update state"""
        if 'valveLevel' in self._lwlink.featuresets[self._featureset_id].features.keys():
            self._valve_level = \
                self._lwlink.featuresets[self._featureset_id].features["valveLevel"].state
        elif self._thermostat:
            self._valve_level = \
                self._lwlink.featuresets[self._featureset_id].features["callForHeat"].state * 100
        else:
            self._valve_level = 100

        if self._thermostat:
            self._onoff = 1
        else:
            self._onoff = \
                self._lwlink.featuresets[self._featureset_id].features["heatState"].state
                    
        self._temperature = \
            self._lwlink.featuresets[self._featureset_id].features["temperature"].state / 10
        self._target_temperature = \
            self._lwlink.featuresets[self._featureset_id].features["targetTemperature"].state / 10
        if self._valve_level == 100 and self._target_temperature < 40:
            self._preset_mode = "Auto"
            self._last_tt = self._target_temperature

        if self._has_humidity:
            self._humidity = \
                self._lwlink.featuresets[self._featureset_id].features["humidity"].state
            self._target_humidity = \
                self._lwlink.featuresets[self._featureset_id].features["targetHumidity"].state

        elif self._valve_level == 100:
            self._preset_mode = "100%"
        elif self._valve_level == 80:
            self._preset_mode = "80%"
        elif self._valve_level == 60:
            self._preset_mode = "60%"
        elif self._valve_level == 40:
            self._preset_mode = "40%"
        elif self._valve_level == 20:
            self._preset_mode = "20%"
        else:
            self._preset_mode = "Auto"

    @property
    def preset_mode(self):
        """Return the preset_mode."""
        return self._preset_mode

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        if preset_mode == "Auto":
            self._target_temperature = self._last_tt
            await self._lwlink.async_set_temperature_by_featureset_id(
                self._featureset_id, self._target_temperature)
        else:
            feature_id = self._lwlink.featuresets[self._featureset_id].features['valveLevel'].id
            _LOGGER.debug("Received preset set request: %s ", preset_mode)
            _LOGGER.debug("Setting feature ID: %s ", feature_id)
            await self._lwlink.async_write_feature(feature_id, PRESET_NAMES[preset_mode])

    @property
    def preset_modes(self):
        """List of available preset modes."""
        return list(PRESET_NAMES)

    @property
    def min_temp(self):
        return 0

    @property
    def max_temp(self):
        return 40

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""

        attribs = {}

        for featurename, feature in self._lwlink.featuresets[self._featureset_id].features.items():
            attribs['lwrf_' + featurename] = feature.state

        attribs['lrwf_product_code'] = self._lwlink.featuresets[self._featureset_id].product_code

        return attribs

    @property
    def device_info(self):
        return {
            'identifiers': {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._featureset_id)
            },
            'name': self.name,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.featuresets[self._featureset_id].product_code,
            'via_device': (DOMAIN, self._linkid)
        }