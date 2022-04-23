import logging
from .const import LIGHTWAVE_LINK2, LIGHTWAVE_ENTITIES, LIGHTWAVE_WEBHOOK
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from .const import DOMAIN

DEPENDENCIES = ['lightwave2']
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Find and return LightWave switches."""

    switches = []
    link = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_LINK2]
    url = hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_WEBHOOK]

    for featureset_id, name in link.get_switches():
        switches.append(LWRF2Switch(name, featureset_id, link, url, hass))

    hass.data[DOMAIN][config_entry.entry_id][LIGHTWAVE_ENTITIES].extend(switches)
    async_add_entities(switches)

class LWRF2Switch(SwitchEntity):
    """Representation of a LightWaveRF switch."""

    def __init__(self, name, featureset_id, link, url, hass):
        """Initialize LWRFSwitch entity."""
        self._name = name
        self._hass = hass
        _LOGGER.debug("Adding switch: %s ", self._name)
        self._featureset_id = featureset_id
        self._lwlink = link
        self._url = url
        self._state = \
            self._lwlink.featuresets[self._featureset_id].features["switch"].state
        self._gen2 = self._lwlink.featuresets[self._featureset_id].is_gen2()
        for featureset_id, hubname in link.get_hubs():
            self._linkid = featureset_id

    async def async_added_to_hass(self):
        """Subscribe to events."""
        await self._lwlink.async_register_callback(self.async_update_callback)

    @callback
    def async_update_callback(self, **kwargs):
        """Update the component's state."""
        if kwargs["feature"] == "uiButton" and self._lwlink.get_featureset_by_featureid(kwargs["feature_id"]).featureset_id == self._featureset_id:
            _LOGGER.debug("Button (socket) press event: %s %s", self.entity_id, kwargs["new_value"])
            self._hass.bus.fire("lightwave2.click",{"entity_id": self.entity_id, "code": kwargs["new_value"]},
        )
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
            self._lwlink.featuresets[self._featureset_id].features["switch"].state

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