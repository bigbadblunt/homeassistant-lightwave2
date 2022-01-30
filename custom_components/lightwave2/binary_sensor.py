import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK
try:
    from homeassistant.components.binary_sensor import BinarySensorEntity
except ImportError:
    from homeassistant.components.binary_sensor import BinarySensorDevice as BinarySensorEntity
from homeassistant.components.binary_sensor import (DEVICE_CLASS_WINDOW, DEVICE_CLASS_PLUG)
from homeassistant.core import callback
from .const import DOMAIN

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave sensors."""

    sensors = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_windowsensors():
        sensors.append(LWRF2BinarySensor(name, featureset_id, link, url))

    for featureset_id, name in link.get_switches():
        if link.featuresets[featureset_id].has_feature('outletInUse'):
            sensors.append(LWRF2SocketBinarySensor(name, featureset_id, link, url))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(sensors)
    async_add_entities(sensors)

class LWRF2BinarySensor(BinarySensorEntity):
    """Representation of a LightWaveRF window sensor."""

    def __init__(self, name, featureset_id, link, url=None):
        self._name = name
        _LOGGER.debug("Adding sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._state = \
            self._lwlink.featuresets[self._featureset_id].features["windowPosition"].state
        self._gen2 = self._lwlink.featuresets[self._featureset_id].is_gen2()
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)
        if self._url is not None:
            for featurename in self._lwlink.featuresets[self._featureset_id].features:
                featureid = self._lwlink.featuresets[self._featureset_id].features[featurename].id
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
            self._lwlink.featuresets[self._featureset_id].features["windowPosition"].state

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

    @property
    def is_on(self):
        """Lightwave switch is on state."""
        return self._state

    @property
    def device_class(self):
        return DEVICE_CLASS_WINDOW

    @property
    def device_state_attributes(self):
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

class LWRF2SocketBinarySensor(BinarySensorEntity):
    """Representation of a LightWaveRF window sensor."""

    def __init__(self, name, featureset_id, link, url=None):
        self._name = f"{name} Plug Sensor"
        _LOGGER.debug("Adding sensor: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._state = \
            self._lwlink.featuresets[self._featureset_id].features["outletInUse"].state
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)
        if self._url is not None:
            for featurename in self._lwlink.featuresets[self._featureset_id].features:
                featureid = self._lwlink.featuresets[self._featureset_id].features[featurename][0]
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

    @property
    def entity_category(self):
        return "diagnostic"

    async def async_update(self):
        """Update state"""
        self._state = \
            self._lwlink.featuresets[self._featureset_id].features["outletInUse"].state

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

    @property
    def is_on(self):
        """Lightwave switch is on state."""
        return self._state

    @property
    def device_class(self):
        return DEVICE_CLASS_PLUG

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
            'identifiers': { (DOMAIN, self._featureset_id)},
            'name': self.name,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.featuresets[self._featureset_id].product_code,
            'via_device': (DOMAIN, self._linkid)
        }