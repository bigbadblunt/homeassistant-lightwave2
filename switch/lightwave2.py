from custom_components.lightwave2 import LIGHTWAVE_LINK2
from homeassistant.components.switch import SwitchDevice
from homeassistant.core import callback
import logging

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ['lightwave2']


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave switches."""

    switches = []
    link = hass.data[LIGHTWAVE_LINK2]

    for device_id, name in link.get_switches():
        switches.append(LWRF2Switch(name, device_id, link))
    _LOGGER.debug(link.get_switches())
    async_add_entities(switches)


class LWRF2Switch(SwitchDevice):
    """Representation of a LightWaveRF switch."""

    def __init__(self, name, device_id, link):
        """Initialize LWRFSwitch entity."""
        self._name = name
        self._device_id = device_id
        self._lwlink = link
        self._state = self._lwlink.get_device_by_id(self._device_id).features["switch"][1]

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

    @callback
    def async_update_callback(self):
        """Update the component's state."""
        _LOGGER.debug("In callback %s", self._name)
        self.async_schedule_update_ha_state(True)

    @property
    def should_poll(self):
        """Gen 2 hub tracks state, so we need to update"""
        return False
        
    async def async_update(self):
        """Update state"""
        self._state = self._lwlink.get_device_by_id(self._device_id).features["switch"][1]

    @property
    def name(self):
        """Lightwave switch name."""
        return self._name
    
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
        """Turn the LightWave switch on."""
        self._state = True
        await self._lwlink.async_turn_on_by_device_id(self._device_id)
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the LightWave switch off."""
        self._state = False
        await self._lwlink.async_turn_off_by_device_id(self._device_id)
        self.async_schedule_update_ha_state()
