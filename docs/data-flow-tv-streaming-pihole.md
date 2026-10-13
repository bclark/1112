# Data Flow Architecture: Streaming, Audio & Pi-hole Telemetry Blocking

This document illustrates the end-to-end network, data, and audio paths for the following scenario:
> *You turn on your Samsung 85" Neo QLED TV, stream a movie from Amazon Prime Video, listen to the audio through your Lounge Soundbar, and your Samsung TV attempts to track your viewing activity.*

---

## 1. Complete System Flowchart

```mermaid
flowchart TD
    subgraph WAN ["External Internet & Cloud"]
        PrimeCDN["Amazon Prime Video CDN\n(Streaming Content)"]
        SamsungCloud["Samsung Telemetry & ACR Servers\n(Tracking / Viewing Data)"]
        CFDNS["Upstream DNS\n(Cloudflare 1.1.1.1)"]
    end

    subgraph Perimeter ["Home Network Ingress"]
        Modem["Fiber ONT / ISP Modem"]
        Deco["TP-Link Deco BE63 Router\n(Gateway: 192.168.68.1)"]
        Modem -->|Fiber / Ethernet| Deco
    end

    subgraph WiredCore ["Core Wired Infrastructure"]
        Switch["TL-SG108E Multi-Gig Switch"]
        Deco -->|2.5 Gbps Ethernet| Switch
    end

    subgraph NAS ["Technodrome NAS (192.168.68.79)"]
        PiHole["Pi-hole DNS Container\n(:53 UDP/TCP)"]
        Switch -->|2.5 Gbps Ethernet| PiHole
    end

    subgraph LivingRoom ["Lounge Entertainment Center"]
        TV["Samsung 85' Neo QLED TV\n(192.168.68.91)"]
        Soundbar["Lounge Soundbar\n(192.168.68.81)"]
        Switch -->|Ethernet Cable| TV
        TV -->|High-Speed HDMI eARC Cable| Soundbar
    end

    %% Step 1: Prime Video DNS
    TV -.->|1. DNS Query: 'primevideo.com'| PiHole
    PiHole -.->|2. Resolve via Upstream| CFDNS
    CFDNS -.->|3. IP Address| PiHole
    PiHole -.->|4. Resolved IP| TV

    %% Step 2: Streaming Video & Audio Payload
    PrimeCDN ==>|5. Encrypted TLS Movie Stream| Modem
    Modem ==> Deco
    Deco ==> Switch
    Switch ==>|Bulk Video/Audio Data| TV

    %% Step 3: Audio eARC Passthrough
    TV ==>|6. Dolby Atmos / 5.1 Digital Audio (eARC)| Soundbar
    Soundbar ==>|7. Immersive Audio Output| Ears["🔊 Lounge Speakers"]

    %% Step 4: Samsung Tracking Blocked
    TV -.-x|8. DNS Query: 'samsungacr.com' / 'samsungqbe.com'| PiHole
    PiHole --x|9. SINKHOLE: 0.0.0.0 (BLOCKED)| TV
    PiHole -.-x|10. Telemetry Drop: Blocked locally, never leaves LAN| SamsungCloud

    classDef allowed fill:#1e3a5f,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef blocked fill:#5c1d1d,stroke:#ef4444,stroke-width:2px,color:#fff;
    classDef hardware fill:#1f2937,stroke:#9ca3af,stroke-width:2px,color:#fff;
    classDef audio fill:#1e4620,stroke:#22c55e,stroke-width:2px,color:#fff;

    class PrimeCDN,CFDNS,TV allowed;
    class SamsungCloud,PiHole blocked;
    class Modem,Deco,Switch hardware;
    class Soundbar,Ears audio;
```

---

## 2. Sequence Diagram (Step-by-Step Chronology)

```mermaid
sequenceDiagram
    autonumber
    actor User as Bryan
    participant TV as Samsung 85" Neo QLED (192.168.68.91)
    participant Switch as TL-SG108E Switch
    participant Deco as Deco BE63 (192.168.68.1)
    participant PiHole as Pi-hole on NAS (192.168.68.79)
    participant Soundbar as Lounge Soundbar (HDMI eARC)
    participant Modem as ISP Modem / ONT
    participant Prime as Amazon Prime Video CDN
    participant Samsung as Samsung Telemetry Servers

    Note over User,TV: Step A: Turning on TV & Launching Prime Video
    User->>TV: Power On & Select Prime Video Movie

    Note over TV,PiHole: Step B: DNS Lookup for Amazon Prime Video
    TV->>Switch: DNS Request: "Where is aiv-delivery.net?"
    Switch->>PiHole: Forward DNS query (Port 53)
    PiHole->>PiHole: Check blocklists (Clean domain: ALLOW)
    PiHole-->>TV: Return IP: 54.239.x.x (Amazon CloudFront / CDN)

    Note over TV,Prime: Step C: Video Stream Ingress
    TV->>Switch: HTTPS Request to 54.239.x.x
    Switch->>Deco: Route outbound request
    Deco->>Modem: Forward to WAN
    Modem->>Prime: Request video & audio bitstream
    Prime-->>Modem: Inbound 4K HDR Video & Dolby Audio Packets
    Modem-->>Deco: 4K Stream payload
    Deco-->>Switch: Route to TV IP (192.168.68.91)
    Switch-->>TV: Deliver raw video/audio packets

    Note over TV,Soundbar: Step D: Audio Separation & HDMI eARC
    TV->>TV: Decode 4K HDR Video & Display on Neo QLED Panel
    TV->>Soundbar: Transmit Dolby Atmos / Digital Plus over HDMI eARC Cable
    Soundbar-->>User: Immersive Surround Sound Playback

    Note over TV,Samsung: Step E: Samsung TV Tries to Track You (ACR / Telemetry)
    TV->>TV: Background Tizen ACR service triggers: "Report what Bryan is watching"
    TV->>Switch: DNS Request: "Where is log-config.samsungcloudsolution.net?"
    Switch->>PiHole: Forward DNS query
    PiHole->>PiHole: Gravity check: Matches Samsung Smart TV telemetry blocklist!
    PiHole-->>TV: SINKHOLE: Return 0.0.0.0 (Domain Blocked)
    TV--xTV: Connection refused / Abort tracking upload
    Note over TV,Samsung: Telemetry is terminated locally; zero tracking data reaches Samsung!
```

---

## 3. Technical Breakdown of Each Stage

### 1. The DNS Fork (Why DNS $\neq$ Data Stream)
When your TV needs to talk to the internet, it asks **Pi-hole on Technodrome (`192.168.68.79`)** to translate the server name into an IP address:
* The TV received `192.168.68.79` as its sole DNS server during DHCP initialization from the Deco BE63 router.
* **DNS lookup is tiny** (a few hundred bytes). Once your TV knows Amazon's IP address, the multi-gigabyte video stream travels directly between the Deco router, switch, and TV.
* The Technodrome NAS **never bottlenecks your streaming bandwidth** because media packets never flow through the NAS—only the initial address lookup does.

---

### 2. High-Speed Video Ingress
* **The Route**: Fiber ISP $\rightarrow$ Modem/ONT $\rightarrow$ Deco BE63 Gateway $\rightarrow$ TL-SG108E Multi-Gig Switch $\rightarrow$ Samsung 85" Neo QLED.
* The TV receives the combined container file (typically MPEG-DASH or HLS over TLS), containing synchronized H.265/HEVC video frames and Dolby Atmos audio channels.

---

### 3. Audio Extraction & The HDMI eARC Pipeline
* **Separation**: The TV’s internal media processor demuxes the stream:
  * Video signals are sent directly to the **Neo Quantum Mini-LED display panel** for 4K local dimming and HDR tone mapping.
  * Audio signals bypass the TV's internal tinny speakers entirely.
* **HDMI eARC (enhanced Audio Return Channel)**:
  * The TV passes the bitstream across the dedicated HDMI 2.1 eARC port directly into the **Lounge Soundbar (`192.168.68.81`)**.
  * eARC provides up to **37 Mbps** of audio bandwidth—far superior to traditional optical cables—enabling uncompressed 24-bit/192kHz multi-channel Dolby TrueHD and uncompressed Dolby Atmos spatial audio.

---

### 4. Telemetry Snooping & Pi-hole Neutralization
Samsung Smart TVs run a background service called **Automated Content Recognition (ACR)** and Tizen diagnostic telemetry:
* Every time you open an app or watch video, the TV fingerprints the content and attempts to upload your viewing habits to Samsung ad-tracking servers:
  * `samsungcloudsolution.com`
  * `log-config.samsungcloudsolution.net`
  * `samsungqbe.com`
  * `samsungacr.com`
* **The Interception**:
  1. The TV asks Pi-hole: *"Where is `log-config.samsungcloudsolution.net`?"*
  2. Pi-hole scans its 72,500+ domain Gravity database.
  3. Pi-hole recognizes the domain as a known tracking server and **sinkholes** it, returning `0.0.0.0`.
  4. The TV's tracking request dies inside your local network. It cannot report what movie you are watching, what time you started it, or your viewing duration.
  5. Your movie continues streaming smoothly without buffering or interruptions.
