# HomeKit Event Bridge

A generic, no-hardcoded-entities Home Assistant custom integration that
exposes any `event` domain entity to Apple HomeKit as a **Stateless
Programmable Switch** (single / double / long press).

It is meant for things like the many Zigbee/Z-Wave/ESPHome buttons and
remotes that Home Assistant represents as `event` entities (e.g.
`event.living_room_button`), so you can trigger HomeKit automations from a
single button press, a double press, or a long press — the same three
gestures HomeKit natively understands for programmable switches.

## How it works

- You add the integration and pick **any number of `event` entities** via a
  Config Flow (with an Options Flow to change the selection later) — nothing
  is hardcoded.
- The integration runs **its own small independent HomeKit bridge** (built
  on [HAP-python](https://github.com/ikalchev/HAP-python), the same library
  Home Assistant's built-in `homekit` integration uses internally). It does
  **not** touch or depend on the built-in `homekit` integration, so it needs
  its own port and its own pairing in the Home app.
- Whenever a selected `event` entity fires a new state with an
  `event_type` attribute, the bridge translates it and pushes it to HomeKit:

  | HA `event_type`  | HomeKit `ProgrammableSwitchEvent` |
  |-------------------|-----------------------------------|
  | `single_press`    | `0` (Single Press)                |
  | `double_press`     | `1` (Double Press)                |
  | `long_press`       | `2` (Long Press)                  |

  Any other `event_type` value is ignored (logged at debug level) since
  HomeKit has no equivalent gesture for it.

## Installation (HACS)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add this repository's URL with category **Integration**.
3. Install **HomeKit Event Bridge**, then restart Home Assistant.

Manual install: copy
`custom_components/homekit_event_bridge` into your Home Assistant
`config/custom_components/` folder and restart.

## Setup

1. **Settings → Devices & Services → Add Integration → HomeKit Event
   Bridge**.
2. Choose a **port** for this bridge's own HAP server. Pick something that
   isn't already used by Home Assistant's built-in `homekit` integration
   (commonly `51827`) or any other HomeKit bridge on your network — e.g. the
   default `21063`.
3. Select the `event` entities you want exposed.
4. Open the **Home app** on iOS/macOS and add an accessory. Home Assistant
   logs the setup code/QR code for this bridge on startup (search the log
   for `HomeKit Event Bridge` around the time the integration loaded) —
   scan or enter it to pair.
5. Each selected entity shows up as its own programmable-switch tile, ready
   to use as a trigger in the Home app's automations.

### Changing which entities are exposed

Use **Configure** on the integration's card to add or remove entities at
any time. Applying changes reloads this integration's bridge. Because the
accessory list changes, HomeKit may treat re-added switches as "new" —
if a switch you removed and re-added stops responding in an existing Home
app automation, just re-pick it there.

## Notes & caveats

- This integration creates a **separate HomeKit bridge/pairing** from Home
  Assistant's built-in one; it is intentionally independent so it has no
  dependency on how (or whether) you've set up the core `homekit`
  integration.
- `HAP-python` pulls in `cryptography` and `zeroconf`; on most systems (and
  in the official HA containers/OS) these install as prebuilt wheels with no
  extra steps.
- Pairing state is stored per config entry under
  `config/homekit_event_bridge/<entry_id>.state` so pairing survives
  restarts.

## License

MIT — see [LICENSE](LICENSE).
