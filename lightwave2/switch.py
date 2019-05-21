from custom_components.lightwave2 import LIGHTWAVE_LINK2
from homeassistant.components.switch import SwitchDevice
from homeassistant.core import callback

DEPENDENCIES = ['lightwave2']


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Find and return LightWave switches."""

    switches = []
    link = hass.data[LIGHTWAVE_LINK2]

    for featureset_id, name in link.get_switches():
        switches.append(LWRF2Switch(name, featureset_id, link))
    async_add_entities(switches)


class LWRF2Switch(SwitchDevice):
    """Representation of a LightWaveRF switch."""

    def __init__(self, name, featureset_id, link):
        """Initialize LWRFSwitch entity."""
        self._name = name
        self._featureset_id = featureset_id
        self._lwlink = link
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "switch"][1]
        self._gen2 = self._lwlink.get_featureset_by_id(
            self._featureset_id).is_gen2()
        self._reports_power = self._lwlink.get_featureset_by_id(
            self._featureset_id).reports_power()
        self._power = None

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
    def assumed_state(self):
        """Gen 2 devices will report state changes, gen 1 doesn't"""
        return not self._gen2

    async def async_update(self):
        """Update state"""
        self._state = \
            self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "switch"][1]
        if self._reports_power:
            self._power = self._lwlink.get_featureset_by_id(self._featureset_id).features[
                "power"][1]

    @property
    def name(self):
        """Lightwave switch name."""
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
    def is_on(self):
        """Lightwave switch is on state."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the LightWave switch on."""
        self._state = True
        await self._lwlink.async_turn_on_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the LightWave switch off."""
        self._state = False
        await self._lwlink.async_turn_off_by_featureset_id(self._featureset_id)
        self.async_schedule_update_ha_state()

    @property
    def current_power_w(self):
        """Power consumption"""
        return self._power