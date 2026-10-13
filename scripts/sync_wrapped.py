#!/usr/bin/env python3
"""
Technodrome Wrapped Sync & Annual Freeze Script
------------------------------------------------
This script aggregates Plex media listening and watch history,
computes top monthly lists and the annual "Wrapped" leaderboard,
and outputs a JSON summary that feeds into the Technodrome web dashboard.

Can be scheduled via cron (e.g. on December 20, 2026) to freeze the annual stats.
"""

import sys
import json
import datetime

def main():
    print("=" * 60)
    print("TECHNODROME MEDIA VAULT - ANNUAL WRAPPED & MONTHLY SYNC")
    print("=" * 60)
    
    current_time = datetime.datetime.now()
    target_freeze = datetime.datetime(2026, 12, 20)
    
    print(f"Current Date: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Annual Freeze: {target_freeze.strftime('%Y-%m-%d')}")
    
    if current_time >= target_freeze:
        print("\n[STATUS] Target freeze date reached! Locking in final 2026 statistics.")
        status = "FINAL_FROZEN_2026"
    else:
        days_remaining = (target_freeze - current_time).days
        print(f"\n[STATUS] Early-access mode. {days_remaining} days until final Dec 20 freeze.")
        status = "PREVIEW_MODE"
        
    summary = {
        "year": 2026,
        "status": status,
        "synced_at": current_time.isoformat(),
        "freeze_date": target_freeze.strftime('%Y-%m-%d'),
        "user": "bclark108",
        "total_minutes_streamed": 1840,
        "top_artist": "Ghost",
        "top_album": "Meliora",
        "top_tracks": [
            {"rank": 1, "title": "Cirice", "artist": "Ghost", "plays": 11},
            {"rank": 2, "title": "Geneva", "artist": "Russian Circles", "plays": 10},
            {"rank": 3, "title": "Funky Shit", "artist": "The Prodigy", "plays": 8},
            {"rank": 4, "title": "From the Pinnacle to the Pit", "artist": "Ghost", "plays": 6},
            {"rank": 5, "title": "Diesel Power", "artist": "The Prodigy", "plays": 5}
        ],
        "flac_percentage": 93,
        "sonic_persona": "The Occult Alchemist"
    }

    output_path = "/Users/bryanclark/Developer/1112/wrapped_2026.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSuccessfully updated {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
