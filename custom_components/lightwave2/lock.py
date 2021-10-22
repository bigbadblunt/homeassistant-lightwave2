import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK
from homeassistant.components.lock import LockEntity
from homeassistant.core import callback
from .const import DOMAIN

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave devices that are lockable."""

    locks = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_lights():
        if link.featuresets[featureset_id].has_feature('protection'):
            locks.append(LWRF2Lock(name, featureset_id, link, url, hass))

    for featureset_id, name in link.get_switches():
        if link.featuresets[featureset_id].has_feature('protection'):
            locks.append(LWRF2Lock(name, featureset_id, link, url, hass))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(locks)
    async_add_entities(locks)

class LWRF2Lock(LockEntity):
    """Representation of a LightWaveRF light."""

    def __init__(self, name, featureset_id, link, url, hass):
        self._name = f"{name} Lock"
        self._device = name
        self._hass = hass
        _LOGGER.debug("Adding lock: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "protection"][1]
        self._gen2 = self._lwlink.get_featureset_by_id(
            self._featureset_id).is_gen2()
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id

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
                "protection"][1]

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def is_locked(self):
        """Return the brightness of the group lights."""
        return self._state == 1

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

    async def async_lock(self, **kwargs):
        """Turn the LightWave lock on."""
        _LOGGER.debug("HA lock.lock received, kwargs: %s", kwargs)

        self._state = 1
        feature_id = self._lwlink.get_featureset_by_id(self._featureset_id).features['protection'][0]
        await self._lwlink.async_write_feature(feature_id, 1)

        self.async_schedule_update_ha_state()

    async def async_unlock(self, **kwargs):
        """Turn the LightWave lock off"""
        _LOGGER.debug("HA lock.unlock received, kwargs: %s", kwargs)

        self._state = 0
        feature_id = self._lwlink.get_featureset_by_id(self._featureset_id).features['protection'][0]
        await self._lwlink.async_write_feature(feature_id, 0)

        self.async_schedule_update_ha_state()

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