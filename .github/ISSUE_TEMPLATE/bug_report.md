---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

Please provide output from `homeassistant.log`, preferably with additional logging enabled.

To enable additional logging, add the following to `configuration.yaml`
```
logger:
  default: warning
  logs:
    lightwave2.lightwave2: debug
    custom_components.lightwave2: debug
```
