from custom_components.lightwave2 import LIGHTWAVE_LINK2
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light)
from homeassistant.core import callback
import logging

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ['lightwave2']


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave lights."""

    lights = []
    link = hass.data[LIGHTWAVE_LINK2]

    for device_id, name in link.get_lights():
        lights.append(LWRF2Light(name, device_id, link))
    _LOGGER.debug(link.get_lights())
    async_add_entities(lights)


class LWRF2Light(Light):
    """Representation of a LightWaveRF light."""

    def __init__(self, name, device_id, link):
        self._name = name
        self._device_id = device_id
        self._lwlink = link
        self._state = self._lwlink.get_device_by_id(self._device_id).features["switch"][1]
        self._brightness = int(self._lwlink.get_device_by_id(self._device_id).features["dimLevel"][1] / 100 * 255)
        self._gen2 = self._lwlink.get_device_by_id(self._device_id).is_gen2()

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

    @callback
    def async_update_callback(self):
        """Update the component's state."""
        self.async_schedule_update_ha_state(True)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS
        
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
        self._state = self._lwlink.get_device_by_id(self._device_id).features["switch"][1]
        self._brightness = int(self._lwlink.get_device_by_id(self._device_id).features["dimLevel"][1] / 100 * 255)

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the group lights."""
        return self._brightness
        
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
    def is_on(self):
        """Lightwave switch is on state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the LightWave light on."""
        self._state = True
        
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        
        await self._lwlink.async_set_brightness_by_device_id(self._device_id, int(self._brightness / 255 * 100))
        await self._lwlink.async_turn_on_by_device_id(self._device_id)
        
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the LightWave light off."""
        self._state = False
        await self._lwlink.async_turn_off_by_device_id(self._device_id)
        self.async_schedule_update_ha_state()
