## Lightwave2

Home Assistant component for controlling LightwaveRF devices with use of a Lightwave Link Plus hub. Controls both generation 1 ("Connect Series") and generation 2 ("Smart Series") devices. Does not work with gen1 hub.

### Setup

Copy all files from lightwave2 to your `<ha_config_dir>/custom_components` directory. (i.e. you should have `<ha_config_dir>/custom_components/lightwave2/__init__.py`, `<ha_config_dir>/custom_components/lightwave2/switch.py` etc)

Tested by me and working with:

- L21 1-gang Dimmer (2nd generation)
- LW430 3-gang Dimmer (1st generation)
- LW270 2-gang Power socket (1st generation)
- LW821 In-line relay (1st generation)
- LW934 Electric switch (1st generation)

Tested by others:

- L22 2-gang Dimmer (2nd generation)

### Configuration

To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
lightwave2:
  username: example@example.co.uk
  password: hunter2
```

This should then automatically add all switches, lights and thermostats that are configured in your Lightwave app.

Credit to Warren Ashcroft whose code I used as a base https://github.com/washcroft/LightwaveRF-LinkPlus
