#!/bin/bash
set -e

SHOWS=(
  "Aeon Flux"
  "X (2001)"
  "Drifting Dragons"
  "Master Keaton (1998)"
  "The Real Ghostbusters (1986)"
  "Escaflowne"
)

echo "=== Starting sync from Karai (192.168.68.86) to Technodrome (/volume2/media/tv/) ==="
date

for show in "${SHOWS[@]}"; do
  echo "--------------------------------------------------------"
  echo ">>> Starting transfer for: $show"
  date
  ssh Bryan@192.168.68.86 "tar -cf - -C D:/Shows \"$show\"" | ssh -o StrictHostKeyChecking=no bclark@technodrome.local "tar -xf - --skip-old-files -C /volume2/media/tv/"
  echo ">>> Completed transfer for: $show"
  date
done

echo "--------------------------------------------------------"
echo ">>> Normalizing filenames and folder permissions on Technodrome..."

ssh -o StrictHostKeyChecking=no bclark@technodrome.local python3 - << 'EOF'
import os
import re

# 1. Normalize X (2001)
x_dir = "/volume2/media/tv/X (2001)"
if os.path.exists(x_dir):
    for f in os.listdir(x_dir):
        m = re.match(r"^X Episode (\d+)(?:\s+(.*))?\.mp4$", f, re.IGNORECASE)
        if m:
            ep_num = int(m.group(1))
            title = m.group(2)
            if ep_num == 0:
                new_name = f"X (2001) - s00e01 - {title}.mp4" if title else "X (2001) - s00e01.mp4"
            else:
                new_name = f"X (2001) - s01e{ep_num:02d} - {title}.mp4" if title else f"X (2001) - s01e{ep_num:02d}.mp4"
            old_path = os.path.join(x_dir, f)
            new_path = os.path.join(x_dir, new_name)
            print(f"Renaming: {f} -> {new_name}")
            os.rename(old_path, new_path)

# 2. Fix Drifting Dragons typo in filenames if present
dd_dir = "/volume2/media/tv/Drifting Dragons"
if os.path.exists(dd_dir):
    for f in os.listdir(dd_dir):
        if "Drfting Dragons" in f:
            new_name = f.replace("Drfting Dragons", "Drifting Dragons")
            print(f"Renaming: {f} -> {new_name}")
            os.rename(os.path.join(dd_dir, f), os.path.join(dd_dir, new_name))

print("Normalization complete.")
EOF

# Ensure group read/write/execute permissions for Plex
ssh -o StrictHostKeyChecking=no bclark@technodrome.local "chmod -R 775 /volume2/media/tv/ && chown -R bclark:admin /volume2/media/tv/"

echo "--------------------------------------------------------"
PLEX_URL="${PLEX_URL:-http://192.168.68.79:32400}"
PLEX_TOKEN="${PLEX_TOKEN:-1zBTm9AgtPFNNVeBzGtG}"
curl -s "${PLEX_URL}/library/sections/3/refresh?X-Plex-Token=${PLEX_TOKEN}"

echo "=== All transfers and post-processing finished successfully! ==="
date
