## Lightwave2

Prototype Home Assistant component for controlling LightwaveRF devices with use of a Lightwave Link Plus hub. Controls both generation 1 ("Connect Series") and generation 2 ("Smart Series") devices. Does not work with gen1 hub.

### Setup

Copy file `lightwave2.py`, `light/lightwave2.py`, `switch/lightwave2.py` to your `ha_config_dir/custom_components` directory.

### Configuration

To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml

lightwave2:
  username: example@example.co.uk
  password: hunter2
