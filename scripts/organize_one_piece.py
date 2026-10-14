#!/usr/bin/env python3
import os
import re
import sys
import shutil
import subprocess
import json

BASE_DIR = '/volume2/media/tv/One Piece'

ARC_MAP = {
    'water-seven': (8, 'Water Seven'),
    'water-7': (8, 'Water Seven'),
    'water seven': (8, 'Water Seven'),
    'enies-lobby': (9, 'Enies Lobby'),
    'enies lobby': (9, 'Enies Lobby'),
    'post-enies-lobby': (9, 'Post-Enies Lobby'),
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

def organize():
    if not os.path.exists(BASE_DIR):
        print(f"Error: {BASE_DIR} does not exist")
        return

    # 1. Handle existing loose Water Seven episodes (E229 - E248)
    s8_dir = os.path.join(BASE_DIR, 'Season 08 - Water Seven')
    os.makedirs(s8_dir, exist_ok=True)
    
    for f in sorted(os.listdir(BASE_DIR)):
        m = re.match(r'^One Piece - E(2[2-4][0-9])\.mp4$', f)
        if m:
            ep_num = int(m.group(1))
            # E229 is S08E01, E248 is S08E20
            s8_ep = ep_num - 228
            src = os.path.join(BASE_DIR, f)
            tag_title = get_video_title(src)
            sub_title = ''
            if '-' in tag_title:
                sub_title = tag_title.split('-', 1)[1].strip()
            
            if sub_title:
                clean_sub = re.sub(r'[/\\?%*:|"<>!]', '', sub_title).strip()
                dst_name = f'One Piece - S08E{s8_ep:02d} - {clean_sub}.mp4'
            else:
                dst_name = f'One Piece - S08E{s8_ep:02d}.mp4'
            
            dst = os.path.join(s8_dir, dst_name)
            print(f"Moving: {f} -> Season 08 - Water Seven/{dst_name}")
            shutil.move(src, dst)

    # 2. Handle arc folders like enies-lobby
    for entry in sorted(os.listdir(BASE_DIR)):
        arc_path = os.path.join(BASE_DIR, entry)
        if os.path.isdir(arc_path) and not entry.startswith('Season '):
            arc_key = entry.lower().strip()
            if arc_key in ARC_MAP:
                season_num, season_name = ARC_MAP[arc_key]
                target_season_dir = os.path.join(BASE_DIR, f"Season {season_num:02d} - {season_name}")
                os.makedirs(target_season_dir, exist_ok=True)
                
                print(f"Processing arc folder: {entry} -> Season {season_num:02d} - {season_name}")
                for video_file in sorted(os.listdir(arc_path)):
                    if video_file.endswith(('.mp4', '.mkv', '.avi')):
                        ep_match = re.search(r'[-_ ](\d{1,3})(?:[-_ ]|\.|$)', video_file)
                        if ep_match:
                            ep_num = int(ep_match.group(1))
                            video_src = os.path.join(arc_path, video_file)
                            tag_title = get_video_title(video_src)
                            
                            sub_title = ''
                            if '-' in tag_title:
                                sub_title = tag_title.split('-', 1)[1].strip()
                            elif tag_title:
                                sub_title = tag_title.strip()
                            
                            if sub_title:
                                clean_sub = re.sub(r'[/\\?%*:|"<>!]', '', sub_title).strip()
                                new_name = f"One Piece - S{season_num:02d}E{ep_num:02d} - {clean_sub}.mp4"
                            else:
                                new_name = f"One Piece - S{season_num:02d}E{ep_num:02d}.mp4"
                            
                            video_dst = os.path.join(target_season_dir, new_name)
                            print(f"Moving: {video_file} -> {os.path.basename(target_season_dir)}/{new_name}")
                            shutil.move(video_src, video_dst)
                
                remaining = os.listdir(arc_path)
                if not remaining:
                    os.rmdir(arc_path)
                    print(f"Cleaned up empty folder: {entry}")
                else:
                    print(f"Note: {entry} still contains files: {remaining}")

if __name__ == '__main__':
    organize()
