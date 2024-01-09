import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES
try:
    from homeassistant.components.cover import CoverEntity
except ImportError:
    from homeassistant.components.cover import CoverDevice as CoverEntity
try:
    from homeassistant.components.cover import CoverEntityFeature
    SUPPORT_CLOSE = CoverEntityFeature.CLOSE
    SUPPORT_OPEN = CoverEntityFeature.OPEN
    SUPPORT_STOP = CoverEntityFeature.STOP
except ImportError:
    from homeassistant.components.cover import (
        SUPPORT_CLOSE, SUPPORT_OPEN,
        SUPPORT_STOP)
from homeassistant.core import callback
from .const import DOMAIN

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave covers."""

    covers = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]

    for featureset_id, name in link.get_covers():
        try:
            covers.append(LWRF2Cover(name, featureset_id, link))
        except Exception as e: _LOGGER.exception("Could not add LWRF2Cover")

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(covers)
    async_add_entities(covers)


class LWRF2Cover(CoverEntity):
    """Representation of a LightWaveRF cover."""

    def __init__(self, name, featureset_id, link):
        """Initialize LWRFCover entity."""
        self._name = name
        _LOGGER.debug("Adding cover: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._state = 50
        self._gen2 = self._lwlink.featuresets[self._featureset_id].is_gen2()
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
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

    @property
    def assumed_state(self):
        """Gen 2 devices will report state changes, gen 1 doesn't"""
        return not self._gen2

    async def async_update(self):
        """Update state"""
        self._state = 50

    @property
    def name(self):
        """Lightwave cover name."""
        return self._name

    @property
    def unique_id(self):
        """Unique identifier. Provided by hub."""
        return self._featureset_id

    @property
    def current_cover_position(self):
        """Lightwave cover position."""
        return self._state

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        is_closed = None
        return is_closed

    async def async_open_cover(self, **kwargs):
        """Open the LightWave cover."""
        await self._lwlink.async_cover_open_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close the LightWave cover."""
        await self._lwlink.async_cover_close_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

    async def async_stop_cover(self, **kwargs):
        """Open the LightWave cover."""
        await self._lwlink.async_cover_stop_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

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
            'name': self.name,
            'manufacturer': "Lightwave RF",
            'model': self._lwlink.featuresets[self._featureset_id].product_code,
            'via_device': (DOMAIN, self._linkid)
        }
