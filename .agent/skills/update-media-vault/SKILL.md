---
name: update-media-vault
description: Syncs and updates the Technodrome Media Vault web dashboard (media.technodrome.online) with the latest movies, television series, music albums, play history, and 2026 Wrapped analytics directly from the Plex server.
---

# Update Media Vault Skill

Use this skill whenever new movies, TV shows, anime episodes, or music albums have been added to the Plex Media Server ("Technodrome"), or when you want to refresh the live website (`https://media.technodrome.online`) with the latest playback logs, monthly top charts, and 2026 Wrapped statistics.

---

## 🚀 Quick Execution

Run the automated sync engine from the workspace root:

```bash
python3 scripts/update_media_vault.py
```

Then commit and push the updated bundle to GitHub:

```bash
git add index.html assets_b64.json wrapped_2026.json assets/ assets_opt/
git commit -m "feat(vault): sync latest media library and 2026 Wrapped stats"
git push origin main
```

Within ~60 seconds, GitHub Pages will automatically deploy the changes to `https://media.technodrome.online`.

---

## 🛠️ What the Engine Does

1. **Connects to Technodrome Plex**:
   * Uses `PLEX_URL` (default: `http://192.168.68.79:32400`) and `PLEX_TOKEN`.
   * Queries **Movies** (Section 1), **Music** (Section 2), and **TV Shows** (Section 3).
2. **Aggregates Analytics & History**:
   * Reads play history from `/status/sessions/history/all`.
   * Calculates monthly stats (top artists, top tracks, listening duration, device breakdown).
   * Generates annual 2026 Wrapped stats and writes `wrapped_2026.json`.
3. **Downloads & Optimizes Artwork**:
   * Downloads any new posters or album covers from Plex into `assets/`.
   * Resizes to 500x500px JPEG (quality 80) into `assets_opt/`.
   * Converts images to Base64 data URIs and saves to `assets_b64.json`.
4. **Rebuilds Self-Contained Dashboard (`index.html`)**:
   * Updates `moviesData`, `showsData`, `albumsData`, `historyData`, `monthlyStatsData`, and the `IMG` Base64 dictionary.
   * Updates top metrics cards (total counts, lossless percentage, era).
   * Ensures the site remains strictly informative (no media playback ports, no server IPs, no hardware telemetry leaks).

---

## 📋 Verification Checklist

After running the sync, verify:
* [ ] `index.html` size is ~3.5MB to 4MB (indicating all images are embedded as Base64).
* [ ] No broken image links or `file://` / CORS errors when opened locally.
* [ ] Navigation tabs reflect the exact library counts: Cinema, Television & Anime, Music Albums.
* [ ] "✨ 2026 Wrapped" button opens the multi-slide interactive story modal.
* [ ] `git push origin main` succeeded and GitHub Pages build is green.
