import logging
from custom_components.lightwave2 import LIGHTWAVE_LINK2
from homeassistant.components.cover import (
    SUPPORT_CLOSE, SUPPORT_OPEN,
    SUPPORT_STOP, CoverDevice)
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)
ATTR_CURRENT_POWER_W = "current_power_w"


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave covers."""

    covers = []
    link = hass.data[LIGHTWAVE_LINK2]

    for featureset_id, name in link.get_covers():
        covers.append(LWRF2Cover(name, featureset_id, link))
    async_add_entities(covers)


class LWRF2Cover(CoverDevice):
    """Representation of a LightWaveRF cover."""

    def __init__(self, name, featureset_id, link):
        """Initialize LWRFCover entity."""
        self._name = name
        _LOGGER.debug("Adding cover: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._state = 50
        self._gen2 = self._lwlink.get_featureset_by_id(
            self._featureset_id).is_gen2()
        self._reports_power = self._lwlink.get_featureset_by_id(
            self._featureset_id).reports_power()
        self._power = None
        if self._reports_power:
            self._power = self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "power"][1]

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

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
    def device_info(self):
        """Return information about the device."""
        return {
            'product_code': self._lwlink.get_featureset_by_id(
                self._featureset_id).product_code
        }

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
    def current_power_w(self):
        """Power consumption"""
        return self._power

    @property
    def device_state_attributes(self):
        """Return the optional state attributes."""

        attribs = {}

        if self._power is not None:
            attribs[ATTR_CURRENT_POWER_W] = self._power

        return attribs

