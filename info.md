## Usage:
Add to configuration.yaml:

```
lightwave2:
  username: example@example.co.uk
  password: hunter2
```

## Usage
Once configured this should then automatically add all switches, lights, thermostats and blinds/covers that are configured in your Lightwave app.

Generation 2 devices will have attributes `current_power_w` for current power usage and `led_rgb` for the color of the LED.

The color of the LED can be changed using the service call `lightwave2.set_led_rgb`.