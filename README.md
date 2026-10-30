# Joulia for Home Assistant

An unofficial Home Assistant integration for Joulia charging services, formerly Aneo Mobility. It is based on [InvisibleDuck/hass-aneo-mobility](https://github.com/InvisibleDuck/hass-aneo-mobility), with the original MIT license and copyright retained.

**Status: experimental.** Connection, charger status and the new diagnostic sensor have been checked with one Joulia-managed Easee charger. Automatic starting has repeatedly produced a queued session that ended without charging on that installation; starting a new session manually in the Joulia app worked. The cause is still under investigation. Do not rely on automated charging without checking the result.

The integration polls the Joulia service for charger and price data. It exposes charger status, connection and charging indicators, price information, start/stop and cable-lock controls. The diagnostic **Actual charger status** reports the socket status as returned by the service without mapping it to a simplified state. The existing **Raw charger status** entity retains its historical `ready`, `charging` and `stopped` values for compatibility.

The connection indicator and charging-control switch are based on an incomplete mapping of service statuses. In particular, a queued session may be shown as disconnected or off. They should not be used as the sole evidence that a charger is disconnected or that it is safe to stop/restart a session. Polling may also miss short transitions.

## Installation

1. In HACS, add this repository as a custom repository of type **Integration**, then install **Joulia**; alternatively, copy `custom_components/aneo_mobility` to the same path in your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Add **Joulia** under Settings → Devices & services and enter your Joulia account details.

The internal domain and directory remain `aneo_mobility` to preserve existing configuration entries and entity identifiers. If replacing the original integration, make a Home Assistant backup first and do not install both versions at the same time. This fork uses the existing Aneo API hostname; the hostname is a technical endpoint and has not been renamed.

## Privacy and support

Account tokens are stored in Home Assistant's integration configuration and may be present in backups. Never publish `.storage`, backups, login details, tokens, charger or subscription identifiers, or unsanitized logs. The integration communicates with a cloud service and is not affiliated with or endorsed by Joulia.

The source includes AI-assisted changes. Review the code and validate behavior with your own equipment before use. Please report issues without personal data or credentials.
