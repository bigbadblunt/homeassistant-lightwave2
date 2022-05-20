import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, DOMAIN
from homeassistant.components.sensor import  STATE_CLASS_MEASUREMENT, STATE_CLASS_TOTAL_INCREASING, SensorEntity, SensorEntityDescription
from homeassistant.const import (POWER_WATT, ENERGY_WATT_HOUR, DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY, 
    DEVICE_CLASS_SIGNAL_STRENGTH, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, PERCENTAGE, DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TIMESTAMP, ELECTRIC_POTENTIAL_VOLT, ELECTRIC_CURRENT_MILLIAMPERE, DEVICE_CLASS_CURRENT, DEVICE_CLASS_VOLTAGE)
from homeassistant.core import callback
from homeassistant.util import dt as dt_util
from homeassistant.helpers.entity import EntityCategory
from datetime import datetime
import pytz

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

SENSORS = [
    SensorEntityDescription(
        key="power",
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Current Consumption",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="energy",
        native_unit_of_measurement=ENERGY_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        name="Total Consumption",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Signal Strength",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="batteryLevel",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_BATTERY,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Battery Level",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
        SensorEntityDescription(
        key="voltage",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=DEVICE_CLASS_VOLTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
        SensorEntityDescription(
        key="current",
        native_unit_of_measurement=ELECTRIC_CURRENT_MILLIAMPERE,
        device_class=DEVICE_CLASS_CURRENT,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Current",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="dawnTime",
        device_class=DEVICE_CLASS_TIMESTAMP,
        name="Dawn Time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="duskTime",
        device_class=DEVICE_CLASS_TIMESTAMP,
        name="Dusk Time",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="lastEvent",
        name="Last Event Received",
        entity_category=EntityCategory.DIAGNOSTIC,
    )
]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave sensors."""

    sensors = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]

    for featureset_id, featureset in link.featuresets.items():
        for description in SENSORS:
            if featureset.has_feature(description.key):
                sensors.append(LWRF2Sensor(featureset.name, featureset_id, link, description, hass))
    
    for featureset_id, hubname in link.get_hubs():
        sensors.append(LWRF2EventSensor(hubname, featureset_id, link, SensorEntityDescription(
        key="lastEvent",
        device_class=DEVICE_CLASS_TIMESTAMP,
        name="Last Event Received",
        entity_category=EntityCategory.DIAGNOSTIC,
    )))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(sensors)
    async_add_entities(sensors)

class LWRF2Sensor(SensorEntity):
    """Representation of a LightWaveRF sensor."""

    def __init__(self, name, featureset_id, link, description, hass):
        self._name = f"{name} {description.name}"
        self._hass = hass
        self._device = name
        _LOGGER.debug("Adding sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self.entity_description = description
        self._state = self._lwlink.featuresets[self._featureset_id].features[self.entity_description.key].state
        if self.entity_description.key == 'duskTime' or self.entity_description.key == 'dawnTime':
            year = self._lwlink.featuresets[self._featureset_id].features['year'].state
            month = self._lwlink.featuresets[self._featureset_id].features['month'].state
            day = self._lwlink.featuresets[self._featureset_id].features['day'].state
            hour = self._state // 3600
            self._state = self._state - hour * 3600
            min = self._state // 60
            second = self._state - min * 60
            self._state = dt_util.parse_datetime(f'{year}-{month:02}-{day:02}T{hour:02}:{min:02}:{second:02}Z')
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id
        if self._lwlink.featuresets[self._featureset_id].is_energy() and not self.entity_description.key == 'rssi':
            self.entity_description.entity_category = None

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

    @callback
    def async_update_callback(self, **kwargs):
        """Update the component's state."""
        if kwargs["feature"] == "buttonPress" and self._lwlink.get_featureset_by_featureid(kwargs["feature_id"]).featureset_id == self._featureset_id:
            _LOGGER.debug("Button (light) press event: %s %s", self.entity_id, kwargs["new_value"])
            self._hass.bus.fire("lightwave2.click",{"entity_id": self.entity_id, "code": kwargs["new_value"]},
        )
        self.async_schedule_update_ha_state(True)

    @property
    def should_poll(self):
        """Lightwave2 library will push state, no polling needed"""
        return False

    @property
    def assumed_state(self):
        return False

    async def async_update(self):
        """Update state"""
        self._state = self._lwlink.featuresets[self._featureset_id].features[self.entity_description.key].state
        if self.entity_description.key == 'duskTime' or self.entity_description.key == 'dawnTime':
            year = self._lwlink.featuresets[self._featureset_id].features['year'].state
            month = self._lwlink.featuresets[self._featureset_id].features['month'].state
            day = self._lwlink.featuresets[self._featureset_id].features['day'].state
            hour = self._state // 3600
            self._state = self._state - hour * 3600
            min = self._state // 60
            second = self._state - min * 60
            self._state = dt_util.parse_datetime(f'{year}-{month:02}-{day:02}T{hour:02}:{min:02}:{second:02}Z')

    @property
    def name(self):
        """Lightwave name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return f"{self._featureset_id}_{self.entity_description.key}"

    @property
    def native_value(self):
        return self._state

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
            'identifiers': { (DOMAIN, self._featureset_id) },
            'name': self._device,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.featuresets[self._featureset_id].product_code,
            'via_device': (DOMAIN, self._linkid)
        }

class LWRF2EventSensor(SensorEntity):
    """Representation of a LightWaveRF sensor."""

    def __init__(self, name, featureset_id, link, description):
        self._name = f"{name} {description.name}"
        self._device = name
        _LOGGER.debug("Adding event sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self.entity_description = description
        self._state = datetime.now(pytz.utc)
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
    def assumed_state(self):
        return False

    async def async_update(self):
        """Update state"""
        self._state = datetime.now(pytz.utc)

    @property
    def name(self):
        """Lightwave name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return f"{self._featureset_id}_{self.entity_description.key}"

    @property
    def native_value(self):
        return self._state

    @property
    def device_info(self):
        return {
            'identifiers': { (DOMAIN, self._featureset_id) },
            'name': self._device,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.featuresets[self._featureset_id].product_code,
            'via_device': (DOMAIN, self._linkid)
        }