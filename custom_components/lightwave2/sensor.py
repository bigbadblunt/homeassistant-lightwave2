import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK, DOMAIN
from homeassistant.components.sensor import  STATE_CLASS_MEASUREMENT, STATE_CLASS_TOTAL_INCREASING, SensorEntity, SensorEntityDescription
from homeassistant.const import POWER_WATT, ENERGY_KILO_WATT_HOUR, DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

ATTR_CURRENT_POWER_W = "current_power_w"
ATTR_TOTAL_ENERGY_KWH = "total_energy_kwh"

LRWF2POWERSENSORDESC = SensorEntityDescription(
        key=ATTR_CURRENT_POWER_W,
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Current Consumption",
    )

LRWF2ENERGYSENSORDESC = SensorEntityDescription(
        key=ATTR_TOTAL_ENERGY_KWH,
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=DEVICE_CLASS_ENERGY,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        name="Total Consumption",
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave sensors."""

    sensors = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_energy():
        sensors.append(LWRF2Sensor(name, featureset_id, link, url, DEVICE_CLASS_POWER))
        sensors.append(LWRF2Sensor(name, featureset_id, link, url, DEVICE_CLASS_ENERGY))

    for featureset_id, name in link.get_switches():
        if link.get_featureset_by_id(featureset_id).reports_power():
            sensors.append(LWRF2Sensor(name, featureset_id, link, url, DEVICE_CLASS_POWER))
            sensors.append(LWRF2Sensor(name, featureset_id, link, url, DEVICE_CLASS_ENERGY))

    for featureset_id, name in link.get_lights():
        if link.get_featureset_by_id(featureset_id).reports_power():
            sensors.append(LWRF2Sensor(name, featureset_id, link, url, DEVICE_CLASS_POWER))
            sensors.append(LWRF2Sensor(name, featureset_id, link, url, DEVICE_CLASS_ENERGY))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(sensors)
    async_add_entities(sensors)

class LWRF2Sensor(SensorEntity):
    """Representation of a LightWaveRF power usage sensor."""

    def __init__(self, name, featureset_id, link, url, type):
        self._name = name
        _LOGGER.debug("Adding sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._type = type
        if self._type == DEVICE_CLASS_POWER:
            self._state = self._lwlink.get_featureset_by_id(self._featureset_id).features["power"][1]
            self.entity_description = LRWF2POWERSENSORDESC
        elif self._type == DEVICE_CLASS_ENERGY:
            self._state = self._lwlink.get_featureset_by_id(self._featureset_id).features["energy"][1]
            self.entity_description = LRWF2POWERSENSORDESC
        self._gen2 = self._lwlink.get_featureset_by_id(
            self._featureset_id).is_gen2()

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
        """Gen 2 devices will report state changes, gen 1 doesn't"""
        return not self._gen2

    async def async_update(self):
        """Update state"""
        if self._type == DEVICE_CLASS_POWER:
            self._state = self._lwlink.get_featureset_by_id(self._featureset_id).features["power"][1]
        elif self._type == DEVICE_CLASS_ENERGY:
            self._state = self._lwlink.get_featureset_by_id(self._featureset_id).features["energy"][1]

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

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
                (DOMAIN, self.unique_id)
            },
            'name': self.name,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.get_featureset_by_id(
                self._featureset_id).product_code
            #TODO 'via_device': (hue.DOMAIN, self.api.bridgeid),
        }