# Network Device & IP Inventory

This document maintains the master device inventory, static IP assignments, hardware roles, and local `.lan` DNS hostname mappings across the **1112** local network.

---

## 1. Network Infrastructure & Core Servers

| Device Name | IP Address | MAC / Interface | DNS Hostname (`.lan`) | Role & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Deco BE63 Main** | `192.168.68.1` | Gateway Interface | `router.lan` | Primary Wi-Fi 7 Router & DHCP Gateway |
| **Deco BE63 Office** | `192.168.68.x` | Mesh Backhaul | `deco-office.lan` | Satellite Mesh Node (Office) |
| **Deco BE63 Family** | `192.168.68.x` | Mesh Backhaul | `deco-family.lan` | Satellite Mesh Node (Family Room / Garage) |
| **TL-SG108E Switch** | `192.168.68.x` | Wired 2.5G/1G | `switch.lan` | 8-Port Multi-Gig Switch in Media Cabinet |
| **Technodrome NAS** | `192.168.68.79` | `eth0` (2.5 GbE) | `technodrome.lan` | UGREEN DXP4800 Plus (Docker Host, Home Assistant, Pi-hole, Plex) |

---

## 2. Personal Workstations & Computing

| Device Name | IP Address | Medium | DNS Hostname (`.lan`) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Krang (MacBook Pro)** | `192.168.68.77` | Wi-Fi 7 (6 GHz) | `Krang-MacBook-Pro.lan` | Bryan's Primary Workstation (Wi-Fi) |
| **Krang Wired** | `192.168.68.88` | 2.5 GbE Wired | `Krang-Wired.lan` | Direct Ethernet connection |
| **Krang CalDigit TS4** | `192.168.68.85` | 2.5 GbE Dock | `Krang-Dock.lan` | Thunderbolt 4 Docking Station |
| **Karai (Windows AI Host)** | `192.168.68.86` | Wi-Fi (5 GHz) | `karai.lan` | NVIDIA RTX 5070 (12 GB) running `llama.cpp` Gemma 4 E4B (`:9931`) & Prometheus Exporter (`:9835`) |
| **Bryan's Watch** | `192.168.68.80` | Wi-Fi | `Bryans-Watch.lan` | Samsung Galaxy Watch |
| **Bryan's Phone** | Dynamic DHCP | Wi-Fi 7 | `Bryans-Fold.lan` | Samsung Galaxy Z Fold |
| **Amanda's iPhone** | Dynamic DHCP | Wi-Fi | `Amandas-iPhone.lan` | Mobile device tracker |

---

## 3. Audio & Entertainment (WiiM & Smart TVs)

| Device Name | IP Address | Source / Inputs | HA Entity ID | Role & Location |
| :--- | :--- | :--- | :--- | :--- |
| **Lounge Ultra** | Static DHCP | Network, BT, Line In, Optical, TV, Phono | `media_player.lounge_ultra_2` | WiiM Ultra Streamer (Master Multiroom Hub) |
| **Lounge Amp** | Static DHCP | Network, Optical, Line In | `media_player.lounge_amp_2` | WiiM Amp (Lounge Speakers) |
| **Den Ultra** | Static DHCP | Network, BT, Line In, Optical, TV, Phono | `media_player.den_ultra_2` | WiiM Ultra Streamer (Den Audio) |
| **Den Amp** | Static DHCP | Network, Optical, Line In | `media_player.den_amp_2` | WiiM Amp (Den Speakers) |
| **Deck Speakers** | Static DHCP | Network, BT, Line In, Optical, TV | `media_player.deck_speakers_3` | WiiM Amp (Outdoor Deck Speakers) |
| **85" Neo QLED TV** | `192.168.68.91` | Ethernet / HDMI eARC | `media_player.85_neo_qled` | Samsung 85" Neo QLED TV (Lounge) |
| **Lounge Soundbar**| `192.168.68.81` | HDMI eARC / Wi-Fi | `media_player.lounge_soundbar` | Home Theater Soundbar |
| **Deck TV** | Static DHCP | Wi-Fi | `media_player.deck_tv` | Outdoor Deck Samsung TV |
| **Den TV** | Static DHCP | Wi-Fi | `media_player.den_tv` | Den TV |
| **Master Bedroom Apple TV** | Static DHCP | Wi-Fi | `media_player.master_bedroom_master_bedroom` | Apple TV 4K |
| **Living Room Apple TV** | Static DHCP | Wi-Fi | `device_tracker.*livingrmappletv` | Apple TV 4K |

---

## 4. Climate Control (Nest Learning Thermostats 4th Gen)

| Location | IP Address | DNS Hostname (`.lan`) | HA Entity ID |
| :--- | :--- | :--- | :--- |
| **Lounge Thermostat** | `192.168.68.87` | `Lounge-Thermostat.lan` | `climate.nest_learning_thermostat_4th_gen` |
| **Bedroom Thermostat** | `192.168.68.89` | `Bedroom-Thermostat.lan` | `climate.nest_learning_thermostat_4th_gen_2` |
| **Living Room Thermostat**| `192.168.68.86` | `Living-Room-Thermostat.lan` | `climate.nest_learning_thermostat_4th_gen_3` |
| **Amanda's Office Thermostat**| `192.168.68.84` | `Amandas-Office-Thermostat.lan` | `climate.nest_learning_thermostat_4th_gen_4` |

---

## 5. Security & Access Control (Eufy)

| Device Name | Model | HA Entity ID | Role & Location |
| :--- | :--- | :--- | :--- |
| **Thufir (HomeBase 3)** | S380 HomeBase | `alarm_control_panel.thufir` | Central Eufy Security Hub & Local AI Storage |
| **Front Door FamiLock S3**| Smart Video Deadbolt | `sensor.front_door_lock_status` | Deadbolt status & video doorbell |
| **Deck Camera** | SoloCam S340 | `camera.deck` | Outdoor Solar PTZ Camera |
| **Garage Camera** | Indoor Cam C120 | `camera.garage` | Garage interior monitoring |
| **Lounge Camera** | S350 Dual-Lens | `camera.lounge` | Lounge PTZ security camera |
| **Living Room Camera** | S350 Dual-Lens | `camera.living_room` | Living room indoor camera |
| **Dining Room Camera** | Indoor Cam C120 | `camera.dining_room` | Dining room indoor camera |
| **Laundry Leak Sensor** | Water Sensor | `sensor.laundry_room_battery_percentage` | Flood / freeze sensor under washing machine |
| **Garage Leak Sensor** | Water Sensor | `sensor.garage_battery_percentage` | Flood / freeze sensor near water heater |
| **X10 Pro Omni** | Robovac | `vacuum.eufy_clean_x10_pro_omni` | Autonomous mopping / vacuum robot |

---

## 6. Smart Home Fabric & 3D Fabrication

| Device Name | IP Address | DNS Hostname (`.lan`) | Role & Notes |
| :--- | :--- | :--- | :--- |
| **Motionblinds Bridge** | `192.168.68.55` | `Motionblinds-Bridge.lan` | USB Bridge controlling 9 motorized shades |
| **Bebop (Bambu P2S)** | `192.168.68.69` | `Bebop-Bambu-P2S.lan` | Bambu Lab P2S 3D Printer |
| **Rocksteady (Bambu P1P)**| `192.168.68.65` | `Rocksteady-Bambu-P1P.lan` | Bambu Lab P1P 3D Printer |
| **Donald Duck Inflatable**| Dynamic DHCP | `switch.donald_duck` | GE Cync Outdoor Smart Plug (Front Yard) |
| **Oogie Boogie Inflatable**| Dynamic DHCP | `switch.oogie_boogie` | GE Cync Outdoor Smart Plug (Front Yard) |
| **Fellow Stagg EKG Pro** | Dynamic DHCP | `sensor.fellow_stagg_ekg_pro_*` | Precision electric kettle |
