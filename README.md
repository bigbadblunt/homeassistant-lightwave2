# Lightwave2

Home Assistant (https://www.home-assistant.io/) component for controlling LightwaveRF (https://lightwaverf.com) devices with use of a Lightwave Link Plus hub. Controls both generation 1 ("Connect Series") and generation 2 ("Smart Series") devices. Does not work with gen1 hub.

Tested by me and working with:

- L21 1-gang Dimmer (2nd generation)
- LW430 3-gang Dimmer (1st generation)
- LW270 2-gang Power socket (1st generation)
- LW821 In-line relay (1st generation)
- LW934 Electric switch/thermostat (1st generation)

Tested by others:

- L22 2-gang Dimmer (2nd generation)
- L24 4-gang Dimmer (2nd generation)
- Three-way relays (for controlling blinds/covers)

## Setup
There are two ways to set up:

#### 1. Using HACS (preferred)
This component is available through the Home Assistant Community Store HACS (https://hacs.netlify.com/)

If you use this method, your component will always update to the latest version. But you'll need to set up HACS first.

#### 2. Manual
Copy all files and folders from custom_components/lightwave2 to a `<ha_config_dir>/custom_components/lightwave2` directory. (i.e. you should have `<ha_config_dir>/custom_components/lightwave2/__init__.py`, `<ha_config_dir>/custom_components/lightwave2/switch.py`, `<ha_config_dir>/custom_components/lightwave2/translations/en.json` etc)

The latest version is at https://github.com/bigbadblunt/homeassistant-lightwave2/releases/latest

If you use this method then you'll need to keep an eye on this repository to check for updates.

## Configuration:
In Home Assistant:

1. Enter configuration menu
2. Select "Integrations"
3. Click the "+" in the bottom right
4. Choose "Lightwave 2"
5. Enter username and password
6. This should automatically find all your devices

## Usage:
Once configured this should then automatically add all switches, lights, thermostats, blinds/covers, sensors and energy monitors that are configured in your Lightwave app. If you add a new device you will need to restart Home Assistant, or remove and re-add the integration.

Various sensor entities (including power consumption) and controls for the button lock and status LED are exposed within the corresponding entities.

All other attributes reported by the Lightwave devices are exposed with the names `lwrf_*`. These are all read-only.

The color of the LED for generation 2 devices can be changed using the service call `lightwave2.set_led_rgb`.
Devices can be locked/unlocked using the service calls `lightwave2.lock` and `lightwave2.unlock`.
(both the lock and the LED are now exposed as entities, so I will remove the above calls at some point - it is recommended not to use them)

For gen2 devices, the brightness can be set without turning the light on using `lightwave2.set_brightness`.

Firmware 5+ devices generate `lightwave2.click` events when the buttons are pressed. The "code" returned is the type of click:

Code|Hex|Meaning
----|----|----
257|101|Up button single press
258|102|Up button double press
259|103|Up button triple press
260|104|Up button quad press
261+||(and so on - I believe up to 20x click is supported)
512|200|Up button press and hold
768|300|Up button release after long press
4353|1101|Down button single press
4354|1102|Down button double press
4355|1103|Down button triple press
4356|1104|Down button quad press
4357+||(and so on)
4608|1200|Down button press and hold
4864|1300|Down button release after long press

For sockets the codes are the "up button" versions.

## Thanks
Credit to Warren Ashcroft whose code I used as a base https://github.com/washcroft/LightwaveRF-LinkPlus
