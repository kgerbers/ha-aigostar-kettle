# AigoSmart Home Assistant integration

This is the first phase of a Home Assistant integration for Aigostar/AigoSmart
devices. It uses the reverse-engineered AigoSmart login and Alibaba Cloud IoT
API flow from the upstream Aigostar project, then polls each discovered device
for its TSL properties.

## Credits

The AigoSmart authentication flow and Alibaba Cloud IoT API client are based
on the reverse-engineered work in
[MarcoM1993/ha-aigostar](https://github.com/MarcoM1993/ha-aigostar), originally
created for Aigostar smart lights. This repository adapts that work for the
Aigostar electric kettle and adds kettle-specific temperature, mode,
keep-warm, and heating controls.

The integration exposes the current temperature, target temperature, a
keep-warm switch, an exploratory operating-mode selector, and explicit start/stop heating buttons. The heating field is
implemented as buttons because the kettle treats `HeatingSwitch` as a
momentary command and reports it back as `0` after accepting the command.

The diagnostic sensor also exposes the raw property map as state attributes.

## Install

Copy `custom_components/aigostar` into `/config/custom_components/`, restart
Home Assistant, and add **AigoSmart Devices** from Settings → Devices &
services → Add integration. Use the same account as the AigoSmart app.

## Next phase

The diagnostic sensor remains useful for checking firmware changes and future
model variants.

The operating-mode selector maps the confirmed values:

- `Met een klik koken` → `Mode = 0`
- `Koken en warm houden` → `Mode = 1`
- `Verwarmen en warm houden` → `Mode = 2`

The keep-warm duration is exposed as 1–13 hours and is converted to the API's
minute-based `Time` property. Timer scheduling is not exposed yet; its payload
still needs to be confirmed from the app.
