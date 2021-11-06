import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK, DOMAIN
from homeassistant.components.sensor import  STATE_CLASS_MEASUREMENT, STATE_CLASS_TOTAL_INCREASING, SensorEntity, SensorEntityDescription
from homeassistant.const import (POWER_WATT, ENERGY_WATT_HOUR, DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY, 
    DEVICE_CLASS_SIGNAL_STRENGTH, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, PERCENTAGE, DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TIMESTAMP, ELECTRIC_POTENTIAL_VOLT, ELECTRIC_CURRENT_AMPERE, DEVICE_CLASS_CURRENT, DEVICE_CLASS_VOLTAGE)
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

SENSORS = [
    SensorEntityDescription(
        key="power",
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Current Consumption",
        entity_category="diagnostic",
    ),
    SensorEntityDescription(
        key="energy",
        native_unit_of_measurement=ENERGY_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        name="Total Consumption",
        entity_category="diagnostic",
    ),
    SensorEntityDescription(
        key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Signal Strength",
        entity_category="diagnostic",
    ),
    SensorEntityDescription(
        key="batteryLevel",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_BATTERY,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Battery Level",
        entity_category="diagnostic",
    ),
        SensorEntityDescription(
        key="voltage",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=DEVICE_CLASS_VOLTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Voltage",
        entity_category="diagnostic",
    ),
        SensorEntityDescription(
        key="current",
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        device_class=DEVICE_CLASS_CURRENT,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Current",
        entity_category="diagnostic",
    ),
    SensorEntityDescription(
        key="dawnTime",
        device_class=DEVICE_CLASS_TIMESTAMP,
        name="Dawn Time",
        entity_category="diagnostic",
    ),
    SensorEntityDescription(
        key="duskTime",
        device_class=DEVICE_CLASS_TIMESTAMP,
        name="Dusk Time",
        entity_category="diagnostic",
    )
]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave sensors."""

    sensors = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, featureset in link.featuresets.items():
        for description in SENSORS:
            if featureset.has_feature(description.key):
                sensors.append(LWRF2Sensor(featureset.name, featureset_id, link, url, description))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(sensors)
    async_add_entities(sensors)

class LWRF2Sensor(SensorEntity):
    """Representation of a LightWaveRF power usage sensor."""

    def __init__(self, name, featureset_id, link, url, description):
        self._name = f"{name} {description.name}"
        self._device = name
        _LOGGER.debug("Adding sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self.entity_description = description
        self._state = self._lwlink.get_featureset_by_id(self._featureset_id).features[self.entity_description.key][1]
        if self.entity_description.key == 'duskTime' or self.entity_description.key == 'dawnTime':
            year = self._lwlink.get_featureset_by_id(self._featureset_id).features['year'][1]
            month = self._lwlink.get_featureset_by_id(self._featureset_id).features['month'][1]
            day = self._lwlink.get_featureset_by_id(self._featureset_id).features['day'][1]
            hour = self._state // 3600
            self._state = self._state - hour * 3600
            min = self._state // 60
            second = self._state - min * 60
            self._state = f'{year}-{month:02}-{day:02}T{hour:02}:{min:02}:{second:02}'
        if self.entity_description.key == 'current':
            self._state = self._state / 10
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id
        if self._lwlink.featuresets[self._featureset_id].is_energy() and not self.entity_description.key == 'rssi':
            self.entity_description.entity_category = None

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)
        if self._url is not None:
            for featurename in self._lwlink.get_featureset_by_id(self._featureset_id).features:
                featureid = self._lwlink.get_featureset_by_id(self._featureset_id).features[featurename][0]
                _LOGGER.debug("Registering webhook: %s %s", featurename, featureid.replace("+", "P"))
                req = await self._lwlink.async_register_webhook(self._url, featureid, "hass" + featureid.replace("+", "P"), overwrite = True)

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
        self._state = self._lwlink.get_featureset_by_id(self._featureset_id).features[self.entity_description.key][1]
        if self.entity_description.key == 'duskTime' or self.entity_description.key == 'dawnTime':
            hour = self._state // 3600
            self._state = self._state - hour * 3600
            min = self._state // 60
            second = self._state - min * 60
            self._state = f'T{hour:02}{min:02}{second:02}'
        if self.entity_description.key == 'current':
            self._state = self._state / 10

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
    def device_state_attributes(self):
        """Return the optional state attributes."""

        attribs = {}

        for featurename, featuredict in self._lwlink.get_featureset_by_id(self._featureset_id).features.items():
            attribs['lwrf_' + featurename] = featuredict[1]

        attribs['lrwf_product_code'] = self._lwlink.get_featureset_by_id(self._featureset_id).product_code

        return attribs

    @property
    def device_info(self):
        return {
            'identifiers': {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._featureset_id)
            },
            'name': self._device,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.get_featureset_by_id(
                self._featureset_id).product_code,
            'via_device': (DOMAIN, self._linkid)
        }
