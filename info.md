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

There are further service calls:

`lightwave2.reconnect`: Force a reconnect to the Lightwave servers (only for non-public API, has no effect on public API)
`lightwave2.whdelete`: Delete a webhook registration (use this if you get "Received message for unregistered webhook" log messages)
`lightwave2.update_states`: Force a read of all states of devices