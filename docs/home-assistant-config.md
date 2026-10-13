# Home Assistant Architecture, Automations & Dashboards

This document details the configuration, integrations, custom scripts, automations, and dashboards running in **Home Assistant Core** on Technodrome.

---

## 1. Core Architecture & Reverse Proxy Trust

Home Assistant operates in Docker on host networking behind Cloudflare Tunnel (`cloudflared`).

### Reverse Proxy Configuration (`.storage/http`)
To prevent HTTP 400 Bad Request errors when accessed through `https://ha.technodrome.online`, Home Assistant is configured to trust forwarded headers from local ingress proxies.

In modern Home Assistant versions, this setting is persisted in `/config/.storage/http`:

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "http",
  "data": {
    "use_x_forwarded_for": true,
    "trusted_proxies": [
      "127.0.0.1",
      "::1"
    ]
  }
}
```

> [!IMPORTANT]
> Do not add redundant `http:` blocks to `configuration.yaml`. Direct `.storage/http` management keeps Home Assistant compliant with modern UI storage migrations and eliminates deprecation repair warnings.

---

## 2. Integrated Hardware & Entity Map

### A. WiiM Multiroom Audio (Linkplay)
* **`media_player.lounge_ultra_2`**: Lounge Ultra Streamer (Designated Multiroom Master Hub).
* **`media_player.lounge_amp_2`**: Lounge Amp.
* **`media_player.den_ultra_2`**: Den Ultra Streamer.
* **`media_player.den_amp_2`**: Den Amp.
* **`media_player.deck_speakers_3`**: Deck Speakers WiiM Amp.
* **Grouping Primitive**: Hardware-synchronized playback using native `media_player.join` and `media_player.unjoin`.

### B. Samsung SmartThings & TVs
* **`media_player.85_neo_qled`**: Primary 85" Neo QLED TV.
* **`media_player.lounge_soundbar`**: Lounge Home Theater Soundbar.
* **`media_player.deck_tv`**: Outdoor Deck TV.
* **`media_player.den_tv`**: Den TV.

### C. Climate (Google Nest Learning Thermostats - 4th Gen)
* **`climate.nest_learning_thermostat_4th_gen_2`**: Bedroom Thermostat.
* **`climate.nest_learning_thermostat_4th_gen`**: Lounge Thermostat.
* **`climate.nest_learning_thermostat_4th_gen_3`**: Living Room Thermostat.
* **`climate.nest_learning_thermostat_4th_gen_4`**: Amanda's Office Thermostat.

### D. Motionblinds Motorized Covers
* **Bridge**: `192.168.68.55` (`USB-Bridge_2d22`).
* **Covers**:
  * `cover.dining_room_blinds`
  * `cover.living_room_blinds`
  * `cover.fireplace_blinds`
  * `cover.guest_room_blinds`
  * `cover.bedroom_blinds`
  * `cover.kitchen_blind`
  * `cover.entry_way`
  * `cover.bathroom`

### E. Security & Access Control (Eufy Security)
* **`alarm_control_panel.thufir`**: Eufy HomeBase 3 (Thufir).
* **`sensor.front_door_lock_status`**: FamiLock S3 Smart Deadbolt lock state (`Locked` / `Unlocked`).
* **Cameras**:
  * `camera.front_door`: Video Doorbell / FamiLock S3.
  * `camera.deck`: SoloCam S340 Solar PTZ.
  * `camera.garage`: Indoor Cam C120.
  * `camera.lounge`: S350 Dual-Lens PTZ.
  * `camera.living_room`: S350 Dual-Lens.
  * `camera.dining_room`: Indoor Cam C120.
* **Leak Sensors**:
  * `sensor.laundry_room_battery_percentage`
  * `sensor.garage_battery_percentage`

### F. Bambu Lab 3D Printers
* **`Rocksteady-Bambu-P1P`** (`192.168.68.65`): Bambu Lab P1P 3D Printer.
* **`Bebop-Bambu-P2S`** (`192.168.68.69`): Bambu Lab P2S 3D Printer.

### G. System Monitor (Technodrome Host Stats)
* **`sensor.system_monitor_processor_temperature`**: NAS CPU Temperature (°F).
* **`sensor.system_monitor_processor_use`**: CPU Utilization %.
* **`sensor.system_monitor_memory_usage`**: RAM Utilization %.
* **`sensor.system_monitor_disk_free`**: Available Free Storage Space (GiB).
* **`sensor.system_monitor_network_throughput_in_eth0`**: Real-time Download Throughput.
* **`sensor.system_monitor_network_throughput_out_eth0`**: Real-time Upload Throughput.

---

## 3. Custom Automations & Scripts

### A. WiiM Whole-Home Party Mode
#### Helper Entities:
* `input_boolean.wiim_party_mode`: Whole-Home Party Mode Master Toggle.
* `input_number.wiim_party_master_volume`: Master Party Volume Slider (0 - 100%).

#### Script: `script.start_wiim_party_mode`
```yaml
alias: "Start WiiM Party Mode"
description: "Synchronizes all 5 WiiM streamers and amps into unified multiroom audio"
mode: single
sequence:
  - action: input_boolean.turn_on
    target:
      entity_id: input_boolean.wiim_party_mode
  - action: media_player.join
    target:
      entity_id: media_player.lounge_ultra_2
    data:
      group_members:
        - media_player.lounge_amp_2
        - media_player.den_ultra_2
        - media_player.den_amp_2
        - media_player.deck_speakers_3
  - action: media_player.volume_mute
    target:
      entity_id:
        - media_player.lounge_ultra_2
        - media_player.lounge_amp_2
        - media_player.den_ultra_2
        - media_player.den_amp_2
        - media_player.deck_speakers_3
    data:
      is_volume_muted: false
  - action: media_player.volume_set
    target:
      entity_id:
        - media_player.lounge_ultra_2
        - media_player.lounge_amp_2
        - media_player.den_ultra_2
        - media_player.den_amp_2
        - media_player.deck_speakers_3
    data:
      volume_level: "{{ states('input_number.wiim_party_master_volume') | float(35) / 100 }}"
```

#### Script: `script.stop_wiim_party_mode`
```yaml
alias: "Stop WiiM Party Mode"
description: "Disbands whole-home WiiM multiroom audio sync and returns zones to independent playback"
mode: single
sequence:
  - action: input_boolean.turn_off
    target:
      entity_id: input_boolean.wiim_party_mode
  - action: media_player.unjoin
    target:
      entity_id:
        - media_player.lounge_amp_2
        - media_player.den_ultra_2
        - media_player.den_amp_2
        - media_player.deck_speakers_3
```

#### Automation: `automation.wiim_party_master_volume_sync`
```yaml
alias: "WiiM Party Master Volume Sync"
description: "Adjusts volume across all 5 synchronized WiiM zones when the master slider moves"
mode: restart
triggers:
  - trigger: state
    entity_id: input_number.wiim_party_master_volume
conditions:
  - condition: state
    entity_id: input_boolean.wiim_party_mode
    state: "on"
actions:
  - action: media_player.volume_set
    target:
      entity_id:
        - media_player.lounge_ultra_2
        - media_player.lounge_amp_2
        - media_player.den_ultra_2
        - media_player.den_amp_2
        - media_player.deck_speakers_3
    data:
      volume_level: "{{ trigger.to_state.state | float(35) / 100 }}"
```

---

### B. Deck Entertainment Sync
#### Automation: `automation.deck_entertainment_sync`
```yaml
alias: "Deck Entertainment Sync"
description: "Powering on Deck TV automatically switches Deck Speakers WiiM Amp to TV audio and unmutes"
mode: single
triggers:
  - trigger: state
    entity_id: media_player.deck_tv
    to: "on"
actions:
  - action: media_player.select_source
    target:
      entity_id: media_player.deck_speakers_3
    data:
      source: "TV"
  - action: media_player.volume_mute
    target:
      entity_id: media_player.deck_speakers_3
    data:
      is_volume_muted: false
```

---

### C. Inflatable Twilight Timer
#### Automation: `automation.inflatable_twilight_timer_donald_duck_oogie_boogie`
```yaml
alias: "Inflatable Twilight Timer (Donald Duck & Oogie Boogie)"
description: "Inflates front yard inflatables at sunset and deflates at 12:30 AM with weather safety"
mode: queued
triggers:
  - trigger: sun
    event: sunset
    id: sunset_inflate
  - trigger: time
    at: "00:30:00"
    id: night_deflate
  - trigger: numeric_state
    entity_id: weather.forecast_home
    attribute: wind_speed
    above: 25
    id: high_wind_cutoff
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: sunset_inflate
          - condition: state
            entity_id: input_boolean.inflatables_weather_override
            state: "off"
          - condition: numeric_state
            entity_id: weather.forecast_home
            attribute: wind_speed
            below: 25
          - condition: not
            conditions:
              - condition: state
                entity_id: weather.forecast_home
                state:
                  - pouring
                  - rainy
                  - lightning-rainy
                  - windy
                  - windy-variant
        sequence:
          - action: switch.turn_on
            target:
              entity_id:
                - switch.donald_duck
                - switch.oogie_boogie
      - conditions:
          - condition: trigger
            id: night_deflate
        sequence:
          - action: switch.turn_off
            target:
              entity_id:
                - switch.donald_duck
                - switch.oogie_boogie
      - conditions:
          - condition: trigger
            id: high_wind_cutoff
        sequence:
          - action: switch.turn_off
            target:
              entity_id:
                - switch.donald_duck
                - switch.oogie_boogie
```

---

### D. 1-Tap Nighttime Lockdown Routine
#### Script: `script.nighttime_lockdown`
```yaml
alias: "Nighttime Lockdown"
description: "Bedtime lockdown: arms security, verifies locks, closes Motionblinds, powers off TVs/audio, sets Bedroom sleep temp"
mode: single
sequence:
  # 1. Lower all Motionblinds
  - action: cover.close_cover
    target:
      entity_id:
        - cover.dining_room_blinds
        - cover.living_room_blinds
        - cover.fireplace_blinds
        - cover.guest_room_blinds
        - cover.bedroom_blinds
        - cover.kitchen_blind
        - cover.entry_way
        - cover.bathroom
    continue_on_error: true

  # 2. Turn off all TVs and Soundbars
  - action: media_player.turn_off
    target:
      entity_id:
        - media_player.85_neo_qled
        - media_player.lounge_soundbar
        - media_player.deck_tv
        - media_player.den_tv
        - media_player.master_bedroom_master_bedroom
        - media_player.vizio_tv_0113_tuner
        - media_player.lounge_tv
    continue_on_error: true

  # 3. Stop all audio playback
  - action: media_player.media_stop
    target:
      entity_id:
        - media_player.lounge_ultra_2
        - media_player.lounge_amp_2
        - media_player.den_ultra_2
        - media_player.den_amp_2
        - media_player.deck_speakers_3
    continue_on_error: true

  # 4. Set Bedroom Thermostat to sleep temperature
  - action: climate.set_temperature
    target:
      entity_id: climate.nest_learning_thermostat_4th_gen_2
    data:
      target_temp_low: "{{ states('input_number.sleep_target_temperature') | float(68) }}"
      target_temp_high: "{{ states('input_number.sleep_target_temperature') | float(68) + 4 }}"
    continue_on_error: true

  # 5. Arm Eufy HomeBase 3 to Home mode
  - action: alarm_control_panel.alarm_arm_home
    target:
      entity_id: alarm_control_panel.thufir
    continue_on_error: true

  # 6. Deadbolt Lock Check & Alert
  - if:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.front_door_lock_status
            state: "Locked"
    then:
      - action: persistent_notification.create
        data:
          title: "🚨 Nighttime Lockdown: Front Door Unlocked"
          message: "The Front Door smart deadbolt reported unlocked during Nighttime Lockdown. Please check and lock the door."
          notification_id: "lockdown_front_door_warning"
    else:
      - action: persistent_notification.dismiss
        data:
          notification_id: "lockdown_front_door_warning"
    continue_on_error: true

  # 7. Summary Notification & Garage Reminder
  - action: persistent_notification.create
    data:
      title: "🌙 Nighttime Lockdown Complete"
      message: "Blinds closed, entertainment off, Bedroom Thermostat set to sleep temp ({{ states('input_number.sleep_target_temperature') }}°F), and Eufy armed. (Reminder: check MyQ garage door)."
      notification_id: "nighttime_lockdown_status"
```

#### Automation: `automation.nighttime_lockdown_schedule_11_30_pm`
```yaml
alias: "Nighttime Lockdown Schedule (11:30 PM)"
description: "Runs the Nighttime Lockdown routine automatically every night at 11:30 PM"
mode: single
triggers:
  - trigger: time
    at: "23:30:00"
actions:
  - action: script.nighttime_lockdown
```

---

## 4. Custom Dashboards

* **`wiim-audio`** (`https://ha.technodrome.online/wiim-audio`):
  * 100% native Home Assistant multiroom audio control.
  * Interactive volume sliders on each zone.
  * 1-tap zone pairing buttons (`Sync All`, `Unjoin All`, `Deck ⇄ Lounge`, `Den ⇄ Lounge`, `Amp ⇄ Lounge`).
  * Live album art and source selectors.
* **`technodrome-system`** (`https://ha.technodrome.online/technodrome-system`):
  * Hardware & performance gauges (CPU utilization, CPU temperature, RAM usage %, available disk space).
  * Quick smart automations panel.
* **`home-security`** (`https://ha.technodrome.online/home-security`):
  * HomeBase 3 arm/disarm panel, guard modes, siren/chime volume.
  * Front door deadbolt status and door contact sensors.
  * Picture glance live camera streams for all outdoor and indoor security cameras.
  * 1-Tap Nighttime Lockdown button.
