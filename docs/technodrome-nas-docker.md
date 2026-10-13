# Technodrome NAS & Docker Ecosystem

This document details the server architecture, filesystem directory structure, and container orchestration for **Technodrome** (UGREEN DXP4800 Plus NAS running UGOS Pro).

---

## 1. Hardware & Host Specifications

| Component | Specification |
| :--- | :--- |
| **Model** | UGREEN DXP4800 Plus |
| **Operating System** | UGOS Pro (Debian Linux kernel 6.x) |
| **Primary IP** | `192.168.68.79` (Static DHCP reservation) |
| **Networking** | Dual 2.5 GbE Intel Ethernet ports (eth0, eth1) |
| **Storage Architecture** | Multi-bay Btrfs storage pool on `/volume1` |
| **Hardware Transcoding** | Intel UHD Graphics (`/dev/dri` passed to Plex) |
| **SSH Management** | `ssh bclark@192.168.68.79` (Default port 22; toggled in UGOS Control Panel) |

---

## 2. Directory Structure on `/volume1`

All Docker persistent configurations are strictly isolated under `/volume1/docker/` to ensure full portability and simplified snapshot backups:

```text
/volume1/
├── docker/
│   ├── cloudflared/
│   │   └── docker-compose.yaml
│   ├── homeassistant/
│   │   ├── config/
│   │   │   ├── configuration.yaml
│   │   │   ├── automations.yaml
│   │   │   ├── scripts.yaml
│   │   │   ├── scenes.yaml
│   │   │   └── .storage/
│   │   └── docker-compose.yaml
│   ├── pihole/
│   │   ├── etc-pihole/
│   │   ├── etc-dnsmasq.d/
│   │   └── docker-compose.yaml
│   ├── plex/
│   │   ├── config/
│   │   └── docker-compose.yaml
│   ├── eufy-security-ws/
│   │   ├── data/
│   │   └── docker-compose.yaml
│   ├── wyoming/
│   │   ├── piper/
│   │   ├── whisper/
│   │   └── openwakeword/
│   └── matter-server/
│       └── data/
└── media/
    ├── movies/
    ├── tv/
    └── music/
```

---

## 3. Production Docker Compose Configurations

### A. Cloudflare Tunnel (`cloudflared`)
**Path**: `/volume1/docker/cloudflared/docker-compose.yaml`

```yaml
version: "3.8"

services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    network_mode: host
    command: tunnel run --token ${TUNNEL_TOKEN}
    environment:
      - TUNNEL_METRICS=0.0.0.0:2000
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### B. Home Assistant Core
**Path**: `/volume1/docker/homeassistant/docker-compose.yaml`

```yaml
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
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "5"
```

---

### C. Pi-hole DNS & Ad-Blocker
**Path**: `/volume1/docker/pihole/docker-compose.yaml`

```yaml
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
      - WEBPASSWORD=${PIHOLE_PASSWORD}
      - FTLCONF_LOCAL_IPV4=192.168.68.79
      - PIHOLE_DNS_=1.1.1.1;1.0.0.1
    volumes:
      - /volume1/docker/pihole/etc-pihole:/etc/pihole
      - /volume1/docker/pihole/etc-dnsmasq.d:/etc/dnsmasq.d
    cap_add:
      - NET_ADMIN
```

---

### D. Plex Media Server (with Hardware Transcoding)
**Path**: `/volume1/docker/plex/docker-compose.yaml`

```yaml
version: "3.8"

services:
  plex:
    image: lscr.io/linuxserver/plex:latest
    container_name: plex
    restart: unless-stopped
    network_mode: host
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
      - VERSION=docker
      - PLEX_CLAIM=${PLEX_CLAIM_TOKEN}
    volumes:
      - /volume1/docker/plex/config:/config
      - /volume1/media/movies:/movies:ro
      - /volume1/media/tv:/tv:ro
      - /volume1/media/music:/music:ro
    devices:
      - /dev/dri:/dev/dri
```

---

### E. Eufy Security WebSocket Bridge (`eufy-security-ws`)
**Path**: `/volume1/docker/eufy-security-ws/docker-compose.yaml`

```yaml
version: "3.8"

services:
  eufy-security-ws:
    image: bropat/eufy-security-ws:latest
    container_name: eufy-security-ws
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - USERNAME=${EUFY_USERNAME}
      - PASSWORD=${EUFY_PASSWORD}
      - COUNTRY=US
      - LANGUAGE=en
      - TRUSTED_DEVICE_NAME=Technodrome
    volumes:
      - /volume1/docker/eufy-security-ws/data:/data
```

---

## 4. Container Maintenance Commands

```bash
# Pull and update any container
cd /volume1/docker/<service-name>
docker compose pull
docker compose up -d

# Inspect container health and resource usage
docker stats --no-stream

# View real-time logs
docker logs -f --tail 100 <container-name>
```
