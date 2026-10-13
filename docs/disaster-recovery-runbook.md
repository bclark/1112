# Disaster Recovery Runbook: Bare-Metal Rebuild Guide

This step-by-step operational runbook guides you through rebuilding the entire **Technodrome** server, network services, Cloudflare Tunnel ingress, and **Home Assistant** smart home ecosystem from absolute zero (e.g., total drive failure or replacing hardware).

---

## 📋 Pre-Flight Checklist & Credentials

Before beginning, ensure you have:
1. **Local Network Access**: Krang MacBook connected to the Deco Wi-Fi or wired switch.
2. **This Git Repository**: Cloned or backed up locally at `/Users/bryanclark/Developer/1112`.
3. **Cloudflare Zero Trust Token**: Stored in Cloudflare Dashboard (Networks > Tunnels > Technodrome).
4. **Plex Claim Token**: Obtained from [plex.tv/claim](https://plex.tv/claim).
5. **Eufy Security Credentials**: Secondary account username and password for HomeBase 3 WebSocket bridge.

---

## Phase 1: Router & Network Foundation

1. **Verify Router Gateway**:
   * Deco BE63 Main Node IP: `192.168.68.1`.
   * Subnet: `255.255.255.0`.
   * Dynamic DHCP Pool: `192.168.68.100` – `192.168.68.250`.

2. **Set Technodrome Static DHCP Reservation**:
   * In the **TP-Link Deco App**: Network > Advanced > Address Reservation.
   * Bind Technodrome NAS MAC address to static IP: **`192.168.68.79`**.

3. **Configure DNS Server**:
   * In Deco App > Advanced > DHCP Server:
     * **Primary DNS**: `192.168.68.79` (Technodrome / Pi-hole).
     * **Secondary DNS**: `1.1.1.1` (fallback while Pi-hole is bootstrapping).

---

## Phase 2: Technodrome Host & Directory Initialization

1. **UGOS Pro Initialization**:
   * Complete initial UGREEN setup wizard.
   * Primary user: `bclark`.
   * Create NVMe Storage Pool on `/volume1` (fast storage for OS, databases, and Docker container configs).
   * Create RAID 1 Storage Pool on `/volume2` (high-capacity dual-drive mirror for media assets: movies, music, TV).
   * Enable SSH: Control Panel > Terminal & SNMP > Enable SSH service (Port 22).

2. **Provision Directory Hierarchy**:
   Open a terminal on Krang and SSH into the NAS:
   ```bash
   ssh bclark@192.168.68.79
   ```

   Run the directory provisioning script:
   ```bash
   sudo mkdir -p /volume1/docker/{cloudflared,homeassistant/config,pihole/etc-pihole,pihole/etc-dnsmasq.d,plex/{config,transcode},eufy-security-ws/data,matter-server/data}
   sudo mkdir -p /volume2/media/{movies,tv,music}
   sudo chown -R bclark:bclark /volume1/docker /volume2/media
   sudo chmod -R 775 /volume2/media
   ```

---

## Phase 3: Cloudflare Zero Trust Remote Ingress

1. **Create Compose File**:
   ```bash
   cat << 'EOF' > /volume1/docker/cloudflared/docker-compose.yaml
   version: "3.8"
   services:
     cloudflared:
       image: cloudflare/cloudflared:latest
       container_name: cloudflared
       restart: unless-stopped
       network_mode: host
       command: tunnel run --token ${TUNNEL_TOKEN}
   EOF
   ```

2. **Start the Tunnel**:
   ```bash
   cd /volume1/docker/cloudflared
   echo "TUNNEL_TOKEN=<YOUR_SAVED_CLOUDFLARE_TUNNEL_TOKEN>" > .env
   docker compose up -d
   ```

3. **Verify Connectivity**:
   ```bash
   docker logs cloudflared
   # Verify output says: "Registered tunnel connection ... Connection established"
   ```

---

## Phase 4: Pi-hole DNS & Local Resolution

1. **Deploy Pi-hole Container**:
   ```bash
   cat << 'EOF' > /volume1/docker/pihole/docker-compose.yaml
   version: "3.8"
   services:
     pihole:
       image: pihole/pihole:latest
       container_name: pihole
       restart: unless-stopped
       ports:
         - "53:53/tcp"
         - "53:53/udp"
         - "80:80/tcp"
       environment:
         - TZ=America/New_York
         - WEBPASSWORD=adminpassword
         - FTLCONF_LOCAL_IPV4=192.168.68.79
         - PIHOLE_DNS_=1.1.1.1;1.0.0.1
       volumes:
         - /volume1/docker/pihole/etc-pihole:/etc/pihole
         - /volume1/docker/pihole/etc-dnsmasq.d:/etc/dnsmasq.d
       cap_add:
         - NET_ADMIN
   EOF

   cd /volume1/docker/pihole
   docker compose up -d
   ```

2. **Restore Static DNS Mappings**:
   Write the `.lan` static hosts file directly into Pi-hole storage:
   ```bash
   cat << 'EOF' > /volume1/docker/pihole/etc-pihole/custom.list
   192.168.68.79 technodrome.lan technodrome
   192.168.68.77 Krang-MacBook-Pro.lan Krang
   192.168.68.88 Krang-Wired.lan
   192.168.68.85 Krang-Dock.lan
   192.168.68.91 85-Neo-QLED-TV.lan
   192.168.68.81 Lounge-Soundbar.lan
   192.168.68.80 Bryans-Watch.lan
   192.168.68.69 Bebop-Bambu-P2S.lan
   192.168.68.65 Rocksteady-Bambu-P1P.lan
   192.168.68.87 Lounge-Thermostat.lan
   192.168.68.89 Bedroom-Thermostat.lan
   192.168.68.86 Living-Room-Thermostat.lan
   192.168.68.84 Amandas-Office-Thermostat.lan
   192.168.68.55 Motionblinds-Bridge.lan
   EOF

   # Restart Pi-hole DNS resolver
   docker exec pihole pihole restartdns
   ```

3. **Verify Local DNS**:
   ```bash
   dig @192.168.68.79 technodrome.lan +short
   # Should return 192.168.68.79
   ```

---

## Phase 5: Home Assistant Core & Reverse Proxy Trust

1. **Deploy Home Assistant Container**:
   ```bash
   cat << 'EOF' > /volume1/docker/homeassistant/docker-compose.yaml
   version: "3.8"
   services:
     homeassistant:
       image: ghcr.io/home-assistant/home-assistant:stable
       container_name: homeassistant
       restart: unless-stopped
       network_mode: host
       privileged: true
       volumes:
         - /volume1/docker/homeassistant/config:/config
         - /etc/localtime:/etc/localtime:ro
         - /run/dbus:/run/dbus:ro
       environment:
         - TZ=America/New_York
   EOF

   cd /volume1/docker/homeassistant
   docker compose up -d
   ```

2. **Configure Reverse Proxy Trust (CRITICAL)**:
   Wait 30 seconds for HA to initialize its directory, then configure `.storage/http`:
   ```bash
   mkdir -p /volume1/docker/homeassistant/config/.storage
   cat << 'EOF' > /volume1/docker/homeassistant/config/.storage/http
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
   EOF

   # Restart Home Assistant to apply trusted proxy configuration
   docker restart homeassistant
   ```

3. **Verify Public Ingress**:
   Test accessing `https://ha.technodrome.online` in a browser. It should load with HTTP 200 and a valid Cloudflare SSL certificate.

---

## Phase 6: Hardware Integrations Setup

1. **WiiM Multiroom Audio**:
   * Navigate to Settings > Devices & Services.
   * The 5 WiiM devices (Lounge Ultra, Lounge Amp, Den Ultra, Den Amp, Deck Speakers) will appear automatically via UPnP / Linkplay discovery.
   * Click **Configure** on each.
2. **Nest Thermostats**:
   * Re-link Google Nest via the official Google Cloud project or Matter credentials.
3. **Motionblinds**:
   * Add Motionblinds integration targeting Bridge IP `192.168.68.55` with the bridge setup key.
4. **Eufy Security**:
   * Deploy `eufy-security-ws` Docker container (`/volume1/docker/eufy-security-ws`).
   * Add Eufy Security integration in Home Assistant pointing to `localhost:3000`.
5. **System Monitor**:
   * Add the built-in **System Monitor** integration in HA.
   * Enable the CPU temperature, CPU utilization, RAM usage, and disk space sensors.

---

## Phase 7: Automations, Scripts & Dashboards Restoration

Once core integrations are loaded, restore the custom automations, helpers, and dashboards documented in [`docs/home-assistant-config.md`](home-assistant-config.md):

1. **Create Helpers**:
   * `input_boolean.wiim_party_mode`
   * `input_number.wiim_party_master_volume` (0 - 100%, step 1, default 35%)
   * `input_boolean.inflatables_weather_override`
   * `input_number.sleep_target_temperature` (60 - 76°F, step 1, default 68°F)

2. **Create Scripts**:
   * `script.start_wiim_party_mode`
   * `script.stop_wiim_party_mode`
   * `script.toggle_wiim_deck_sync`
   * `script.toggle_wiim_den_sync`
   * `script.toggle_wiim_lounge_amp_sync`
   * `script.nighttime_lockdown`

3. **Create Automations**:
   * `automation.wiim_party_master_volume_sync`
   * `automation.deck_entertainment_sync`
   * `automation.inflatable_twilight_timer_donald_duck_oogie_boogie`
   * `automation.nighttime_lockdown_schedule_11_30_pm`

4. **Restore Dashboards**:
   * Create `wiim-audio` dashboard (WiiM multiroom native audio hub).
   * Create `technodrome-system` dashboard (NAS performance & hardware gauges).
   * Update `home-security` dashboard with the 1-Tap Lockdown button.

---

## Phase 8: Verification & Smoke Tests

| Step | Action | Expected Result | Pass? |
| :---: | :--- | :--- | :---: |
| 1 | Run `curl -s -o /dev/null -w "%{http_code}" https://ha.technodrome.online` | Returns `200` | [ ] |
| 2 | Run `curl -s -o /dev/null -w "%{http_code}" https://plex.technodrome.online/web` | Returns `200` | [ ] |
| 3 | Run `dig @192.168.68.79 Bebop-Bambu-P2S.lan +short` | Returns `192.168.68.69` | [ ] |
| 4 | Tap **Sync All 5 Zones** in WiiM Audio dashboard | All 5 WiiMs group to Lounge Ultra | [ ] |
| 5 | Power on Deck TV | Deck Speakers WiiM Amp switches to TV input | [ ] |
| 6 | Execute **Nighttime Lockdown** | Blinds close, TVs power off, Bedroom Nest sets to 68°F | [ ] |
| 7 | Inspect Technodrome dashboard | Live CPU temp and RAM gauges render | [ ] |
