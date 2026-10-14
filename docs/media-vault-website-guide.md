# Media Vault & Year-End Wrapped: Website Specification & Agent Prompt

Give this prompt directly to any AI coding assistant to build the **Media Vault website and interactive Wrapped experience**.

---

## 📋 Copy-and-Paste Agent Prompt

```markdown
Please build a modern, responsive, self-contained single-page web dashboard (`index.html`) for my media collection called "<NAME>'s Media Vault". 

The website is an informative media showcase that features my movie and music library, monthly listening leaderboards, and an interactive, Spotify-style Year-End Wrapped story experience.

### 1. Core Technical Constraints
* **Single Self-Contained File**: Build the entire dashboard in a single `index.html` file using Tailwind CSS (`<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>`).
* **Self-Contained Images**: All poster and album cover art should be embedded as Base64 data URIs (`data:image/jpeg;base64,...`) or load from a clean data dictionary so the file works offline and never breaks under CORS or `file://` restrictions.
* **Strictly Informative (No Media Streaming)**:
  * Do NOT include an audio player, progress scrubbers, or play buttons (`▶`).
  * The site is an archival showcase, not a streaming client. Tracklists should show durations, not play controls.
* **Privacy & Security Sanitization**:
  * Do NOT include server IP addresses, internal ports (e.g. 32400), software version numbers (Plex/Linux), or local filesystem paths (`/movies`, `/volume1`).
  * Header subtitle should read cleanly: "Curated Media Archives & Analytics".

---

### 2. Required Dashboard Sections & Features

#### A. Header & Quick Search
* **Branding**: Vault title, an "Online" status pill, and subtitle.
* **Quick Search Bar**: Live instant filtering across movie titles, album names, artists, genres, and cast members.
* **"✨ 2026 Wrapped" button**: Distinctive gradient button that launches the interactive Wrapped story modal.

#### B. Overview Metrics Cards (Top Grid)
* **Movies in Vault**: Count + resolution badge (e.g. 1080p FHD).
* **Music Library**: Total track count + album and artist count.
* **Audio Quality**: Lossless ratio badge (e.g. 93% FLAC Lossless).
* **Collection Era**: Era span (e.g. 1977 – 2026 / Classic to Modern).

#### C. Navigation Tabs
* Tabs to toggle views: **"All Media"**, **"📊 Monthly Top Lists"**, **"Cinema"**, **"Music Albums"**, and **"Recent Activity"**.

#### D. Cinema Showcase (Movies)
* Poster cards with year, runtime, resolution (1080p), codec (HEVC/H.264), and content rating.
* Clicking any movie opens a **Detail Modal** with full synopsis, director, studio, and cast member chips.

#### E. High-Fidelity Music Collection (Albums)
* Album cover cards with artist name, album title, release year, track count, and audio format badge (FLAC / AAC).
* Clicking any album opens an **Album Drawer Modal** showing:
  * Album summary / editorial review.
  * Complete tracklist with track numbers, song titles, and durations.

#### F. Monthly Top Lists View
* Dropdown selector to switch between months (e.g. Current Month, Previous Month).
* **Monthly Metric Badges**: Total listening duration (e.g. 1h 22m), total plays, top artist, and lossless ratio.
* **Top 5 Tracks Leaderboard**: Table displaying rank (#1 to #5), song title, artist, play count, and duration.
* **Listening by Client Breakdown**: Progress bars showing the percentage of listening time across rooms/devices (e.g. Living Room 58%, Patio 19%, Mobile 12%, Web 11%).

#### G. Recent Activity Log
* Clean table displaying recent plays: Track Title, Artist & Album, Date/Timestamp, Device/Client, and Audio Format (e.g. Lossless FLAC).

---

### 3. Interactive Year-End Wrapped Story Experience (Spotify Wrapped Style)

Clicking the **"✨ 2026 Wrapped"** button opens a full-screen modal styled like mobile social/music stories:
* **Story Navigation**:
  * Segmented progress bars across the top indicating the active slide.
  * Tap left to go back, tap right to advance.
  * Keyboard support (`←` and `→` arrow keys, and `Esc` to close).
  * Vibrant animated gradient backgrounds for each slide.
* **Slide 1 (Intro)**: "Ready for your 2026 Wrapped?" — Welcome retrospective.
* **Slide 2 (Listening Time)**: Total minutes streamed + top listening location and device.
* **Slide 3 (Top Artist)**: The #1 crowned artist of the year with artwork, stream count, and runner-ups (#2–#4).
* **Slide 4 (Top 5 Songs)**: Ranked list of top 5 most-played songs with durations and album titles.
* **Slide 5 (Audiophile Grade)**: Percentage of streams played in uncompressed Lossless FLAC + fun commentary on audio quality.
* **Slide 6 (Sonic Archetype / Persona)**: A creative musical persona based on the collection's genres (e.g. "The Occult Alchemist", "The Heavy Groove Wanderer") + a note that final annual stats freeze on December 20.

---

### 4. Data Structure Template
Please populate the script with data matching this JSON format:

```javascript
const moviesData = [
  {
    id: 1,
    title: "Movie Title",
    year: 2024,
    rating: "PG-13",
    duration: "2h 05m",
    resolution: "1080p",
    codec: "HEVC",
    genres: ["Action", "Sci-Fi"],
    director: "Director Name",
    studio: "Studio Name",
    poster: "data:image/jpeg;base64,...",
    summary: "Synopsis...",
    cast: ["Actor 1", "Actor 2", "Actor 3"]
  }
];

const albumsData = [
  {
    id: 1,
    title: "Album Title",
    artist: "Artist Name",
    year: 2023,
    genre: "Rock",
    tracksCount: 10,
    format: "FLAC",
    poster: "data:image/jpeg;base64,...",
    summary: "Album description...",
    tracks: [
      { num: 1, title: "Track One", duration: "04:12" },
      { num: 2, title: "Track Two", duration: "03:45" }
    ]
  }
];

const monthlyStatsData = {
  "2026-10": {
    monthName: "October 2026",
    totalMinutes: "1h 22m",
    totalPlays: 18,
    topArtist: "Artist Name",
    topArtistPlays: 11,
    topAlbum: "Album Title",
    flacPercent: "94%",
    topTracks: [
      { rank: 1, title: "Song A", artist: "Artist", album: "Album", plays: 8, duration: "04:30" }
    ],
    devices: [
      { name: "Living Room", percent: 60, duration: "45m", count: 10 }
    ]
  }
};
```
```
