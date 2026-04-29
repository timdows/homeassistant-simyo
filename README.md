# Home Assistant Simyo integration

A custom Home Assistant integration that polls the [Mijn Simyo](https://mijn.simyo.nl/)
app API and exposes balance, data, voice, SMS, and out-of-bundle costs as sensors.

## Status

Unofficial. The integration uses the same private app API that the Mijn Simyo
iOS/Android app talks to (`https://appapi.simyo.nl/simyoapi/api/v1`). Simyo
does not publish documentation for this API, so the integration may break if
they change it.

The login endpoint (`POST /sessions`) and the `balance` and `usage` endpoints
are confirmed to exist and respond to the headers and authentication scheme
this integration uses. The exact JSON shape of the `balance` and `usage`
responses, however, was not available at build time. The sensor platform
therefore probes a few likely field paths and exposes the raw payload of each
section under the `raw` attribute of the corresponding sensor — so if a
sensor stays `unknown`, look at the attribute, find the right field, and open
an issue (or patch `sensor.py`).

## Installation

1. Copy `custom_components/simyo` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and pick **Simyo**.
4. Enter your Simyo phone number (e.g. `0612345678`) and your Mijn Simyo password.

## Sensors

| Sensor | Source endpoint |
| ------ | --------------- |
| Balance | `balance` |
| Data used / remaining | `usage` |
| Voice minutes used / remaining | `usage` |
| SMS used / remaining | `usage` |
| Out-of-bundle costs | `usage` |

Each sensor also publishes the full raw section payload as the `raw`
attribute, which is useful for debugging or for building template sensors on
fields that aren't yet mapped.

## Polling

The integration polls every 5 hours. There is no way to push from Simyo.
