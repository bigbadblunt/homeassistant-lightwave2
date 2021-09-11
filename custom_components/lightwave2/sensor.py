import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK, DOMAIN
from homeassistant.components.sensor import DEVICE_CLASS_POWER, STATE_CLASS_MEASUREMENT, SensorEntity, SensorEntityDescription
from homeassistant.const import POWER_WATT
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

ATTR_CURRENT_POWER_W = "current_power_w"
LRWF2SENSORDESC = SensorEntityDescription(
        key=ATTR_CURRENT_POWER_W,
        native_unit_of_measurement=POWER_WATT,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
        name="Current Consumption",
    )

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave sensors."""

    sensors = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_energy():
        sensors.append(LWRF2Sensor(name, featureset_id, link, url))

    for featureset_id, name in link.get_switches():
        if link.get_featureset_by_id(featureset_id).reports_power():
            sensors.append(LWRF2Sensor(name, featureset_id, link, url))

    for featureset_id, name in link.get_lights():
        if link.get_featureset_by_id(featureset_id).reports_power():
            sensors.append(LWRF2Sensor(name, featureset_id, link, url))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(sensors)
    async_add_entities(sensors)

class LWRF2Sensor(SensorEntity):
    """Representation of a LightWaveRF power usage sensor."""

    def __init__(self, name, featureset_id, link, url=None):
        self._name = name
        _LOGGER.debug("Adding sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "power"][1]
        _LOGGER.debug("Initial state %s ", POWER_WATT)
        self._gen2 = self._lwlink.get_featureset_by_id(
            self._featureset_id).is_gen2()
        self.entity_description = LRWF2SENSORDESC

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
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "power"][1]

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

    #@property
    #def device_class(self):
    #    return DEVICE_CLASS_POWER

    @property
    def native_value(self):
        return 12 #self._state

    #@property
    #def native_unit_of_measurement(self):
    #    """Return the unit of measurement of this entity, if any."""
     #   return POWER_WATT

    #@property
    #def state_class(self):
    #    return STATE_CLASS_MEASUREMENT

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