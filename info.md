## Configuration:
In Home Assistant:

1. Enter configuration menu
2. Select "Integrations"
3. Click the "+" in the bottom right
4. Choose "Lightwave 2"
5. Enter username and password
6. This should automatically find all your devices

## Usage:
Once configured this should then automatically add all switches, lights, thermostats and blinds/covers that are configured in your Lightwave app. If you add a new device you will need to restart Home Assistant, or remove and re-add the integration.

Generation 2 devices have the attribute `current_power_w` for current power usage.

Various other attributes are exposed with the names `lwrf_*`.

The color of the LED for generation 2 devices can be changed using the service call `lightwave2.set_led_rgb`.

Devices can be locked/unlocked using the service calls `lightwave2.lock` and `lightwave2.unlock`.