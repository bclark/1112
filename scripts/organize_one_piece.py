#!/usr/bin/env python3
import os
import re
import sys
import shutil
import subprocess
import json
import urllib.request

BASE_DIR = '/volume2/media/tv/One Piece'
PLEX_TOKEN = '1zBTm9AgtPFNNVeBzGtG'
PLEX_TV_SECTION_ID = '3'

# Season mapping: (Season Number, Canonical Season Folder Name)
ARC_MAP = {
    'romance-dawn': (1, 'Romance Dawn'),
    'orange-town': (2, 'Orange Town'),
    'syrup-village': (3, 'Syrup Village'),
    'baratie': (4, 'Baratie'),
    'arlong-park': (5, 'Arlong Park'),
    'loguetown': (6, 'Loguetown'),
    'reverse-mountain': (7, 'Reverse Mountain'),
    'whiskey-peak': (7, 'Whiskey Peak'),
    'little-garden': (7, 'Little Garden'),
    'drum-island': (7, 'Drum Island'),
    'arabasta': (4, 'Alabasta'),
    'alabasta': (4, 'Alabasta'),
    'jaya': (9, 'Jaya'),
    'skypiea': (10, 'Skypiea'),
    'long-ring-long-land': (7, 'Long Ring Long Land'),
    'water-seven': (8, 'Water Seven'),
    'water-7': (8, 'Water Seven'),
    'water seven': (8, 'Water Seven'),
    'enies-lobby': (9, 'Enies Lobby'),
    'enies lobby': (9, 'Enies Lobby'),
    'post-enies-lobby': (9, 'Enies Lobby'),
    'post enies lobby': (9, 'Enies Lobby'),
    'thriller-bark': (10, 'Thriller Bark'),
    'sabaody-archipelago': (11, 'Sabaody Archipelago'),
    'sabaody': (11, 'Sabaody Archipelago'),
    'amazon-lily': (12, 'Amazon Lily'),
    'impel-down': (13, 'Impel Down'),
    'marineford': (14, 'Marineford'),
    'post-war': (14, 'Post-War'),
    'return-to-sabaody': (15, 'Return to Sabaody'),
    'fishman-island': (15, 'Fishman Island'),
    'punk-hazard': (16, 'Punk Hazard'),
    'dressrosa': (17, 'Dressrosa'),
    'zou': (18, 'Zou'),
    'whole-cake-island': (19, 'Whole Cake Island'),
    'reverie': (19, 'Reverie'),
    'wano': (20, 'Wano Country'),
    'wano-country': (20, 'Wano Country'),
    'egghead': (21, 'Egghead'),
}

def get_video_title(file_path):
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        title = data.get('format', {}).get('tags', {}).get('title', '')
        return title
    except Exception:
        return ''

def get_max_existing_episode(season_dir, season_num):
    if not os.path.exists(season_dir):
        return 0
    max_ep = 0
    pattern = re.compile(rf'S{season_num:02d}E(\d{{1,3}})', re.IGNORECASE)
    for f in os.listdir(season_dir):
        m = pattern.search(f)
        if m:
            ep = int(m.group(1))
            if ep > max_ep:
                max_ep = ep
    return max_ep

def trigger_plex_scan():
    try:
        url = f'http://127.0.0.1:32400/library/sections/{PLEX_TV_SECTION_ID}/refresh?X-Plex-Token={PLEX_TOKEN}'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print('Plex TV Shows library scan triggered successfully.')
    except Exception as e:
        print(f'Failed to notify Plex: {e}')

def organize():
    if not os.path.exists(BASE_DIR):
        print(f"Error: {BASE_DIR} does not exist")
        return

    moved_count = 0

    # Handle arc folders (e.g. enies-lobby, post-enies-lobby, thriller-bark)
    for entry in sorted(os.listdir(BASE_DIR)):
        arc_path = os.path.join(BASE_DIR, entry)
        if os.path.isdir(arc_path) and not entry.startswith('Season '):
            arc_key = entry.lower().strip()
            if arc_key in ARC_MAP:
                season_num, season_name = ARC_MAP[arc_key]
                target_season_dir = os.path.join(BASE_DIR, f"Season {season_num:02d} - {season_name}")
                os.makedirs(target_season_dir, exist_ok=True)
                
                # Check for existing episodes to offset if this is a sub-arc
                existing_max = get_max_existing_episode(target_season_dir, season_num)
                is_sub_arc = 'post-' in arc_key or existing_max > 0
                
                print(f"Processing arc folder: '{entry}' -> Season {season_num:02d} - {season_name} (existing max ep: {existing_max})")
                
                for video_file in sorted(os.listdir(arc_path)):
                    # Ignore active downloads (.part, .crdownload, etc.)
                    if video_file.endswith(('.part', '.crdownload', '.tmp')):
                        continue
                    if video_file.endswith(('.mp4', '.mkv', '.avi')):
                        ep_match = re.search(r'[-_ ](\d{1,3})(?:[-_ ]|\.|$)', video_file)
                        if ep_match:
                            raw_ep_num = int(ep_match.group(1))
                            if is_sub_arc and raw_ep_num <= existing_max:
                                ep_num = existing_max + raw_ep_num
                            else:
                                ep_num = raw_ep_num

                            video_src = os.path.join(arc_path, video_file)
                            tag_title = get_video_title(video_src)
                            
                            sub_title = ''
                            if '-' in tag_title:
                                sub_title = tag_title.split('-', 1)[1].strip()
                            elif tag_title:
                                sub_title = tag_title.strip()
                            
                            # Clean up redundant prefix in title if present
                            if sub_title.lower().startswith('enies lobby ') or sub_title.lower().startswith('water seven '):
                                sub_title = re.sub(r'^(?:enies lobby|water seven)\s*\d+\s*-\s*', '', sub_title, flags=re.IGNORECASE)

                            if sub_title:
                                clean_sub = re.sub(r'[/\\?%*:|"<>!]', '', sub_title).strip()
                                new_name = f"One Piece - S{season_num:02d}E{ep_num:02d} - {clean_sub}.mp4"
                            else:
                                new_name = f"One Piece - S{season_num:02d}E{ep_num:02d}.mp4"
                            
                            video_dst = os.path.join(target_season_dir, new_name)
                            print(f"Moving: {video_file} -> {os.path.basename(target_season_dir)}/{new_name}")
                            shutil.move(video_src, video_dst)
                            moved_count += 1
                
                remaining = [f for f in os.listdir(arc_path) if not f.endswith(('.part', '.crdownload', '.tmp'))]
                if not remaining:
                    # If only partial downloads remain, keep directory; otherwise if totally empty, remove
                    all_remaining = os.listdir(arc_path)
                    if not all_remaining:
                        os.rmdir(arc_path)
                        print(f"Cleaned up empty folder: {entry}")
                else:
                    print(f"Note: {entry} still contains files: {remaining}")

    if moved_count > 0:
        print(f"Organized {moved_count} new episode(s). Notifying Plex...")
        trigger_plex_scan()
    else:
        print("No new completed arc episodes to organize.")

if __name__ == '__main__':
    organize()
