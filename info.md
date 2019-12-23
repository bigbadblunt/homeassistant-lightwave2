## Configuration:
Add to configuration.yaml:

```
lightwave2:
  username: example@example.co.uk
  password: hunter2
```

By default this uses a reverse engineered emulation of the Lightwave app. To use the offical API, add `backend: public`. There is no difference in functionality between the two implementations, but stability/responsiveness might differ depending on your network.

## Usage:
Once configured this should then automatically add all switches, lights, thermostats and blinds/covers that are configured in your Lightwave app.

Generation 2 devices will have the attribute `current_power_w` for current power usage.

Various other attributes are exposed with the name lwrf_*.

The color of the LED for generation 2 devices can be changed using the service call `lightwave2.set_led_rgb`.