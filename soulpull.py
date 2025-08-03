#!/usr/bin/env python3

import json
import os
import shutil
import sys
import datetime
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
from dotenv import load_dotenv
from flask import Flask, request, redirect
# Load environment variables from .env file
load_dotenv()

from pathlib import Path

# Paths
raw_path = Path('path/raw_soul_data.json')
landing_folder = Path('final_landing')

# Spotify auth
# Spotify auth
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

tokens_dir = Path("tokens")
if not tokens_dir.exists() or not any(tokens_dir.iterdir()):
    print(f"No token files found in '{tokens_dir}' directory.")
    print("Please run the authentication flow first (e.g., by running server.py).")
    sys.exit(1)
token_files = list(tokens_dir.glob('*.json'))
if not token_files:
    print(f"No token files found in '{tokens_dir}' directory.")
    print("Please run the authentication flow first (e.g., by running server.py).")
    sys.exit(1)
# Define the scopes used for Spotify authentication
SPOTIFY_SCOPE = "user-top-read user-read-recently-played"

# Find the latest token file for cache_path
latest_file = max(token_files, key=os.path.getctime)

sp = Spotify(auth_manager=SpotifyOAuth(
    scope=SPOTIFY_SCOPE,
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    cache_path=str(latest_file)
))

# Initialize the OAuth instance (if needed for callback flows)
sp_oauth_instance_for_callback = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE
)

cache_path = ".cache"

if "--backup" in sys.argv:
    os.makedirs("backups", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    source_file = "path/raw_soul_data.json"
    if os.path.exists(source_file):
        shutil.copy(source_file, f"backups/soul_{timestamp}.json")
    else:
        print(f"Backup failed: '{source_file}' does not exist.")
def process_track(track_item):
    track = track_item.get('track', track_item) # For recent tracks, 'track' is nested
    if not track:
        return None
    artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
    return {
        "name": track.get('name'),
        "artist": artists,
        "album": track.get('album', {}).get('name')
    }

def process_artist(artist_item):
    if not artist_item:
        return None
    return {
        "name": artist_item.get('name'),
        "genres": ", ".join(artist_item.get('genres', []))
    }

def process_soul_data(raw_data):
    processed = {}

    # Process User Profile
    user_profile = raw_data.get('user_profile', {})
    processed['user_profile'] = {
        "display_name": user_profile.get('display_name'),
        "email": user_profile.get('email'),
        "spotify_uri": user_profile.get('uri'),
        "profile_url": user_profile.get('external_urls', {}).get('spotify')
    }

    # Process Top Tracks
    processed_tracks = {}
    for term, tracks_data in raw_data.get('top_tracks', {}).items():
        processed_tracks[term] = [process_track(item) for item in tracks_data.get('items', []) if process_track(item) is not None]
    processed['top_tracks'] = processed_tracks

    # Process Top Artists
    processed_artists = {}
    for term, artists_data in raw_data.get('top_artists', {}).items():
        process_top_artists(term, processed_artists, artists_data)
    processed['top_artists'] = processed_artists

    # Process Recent Tracks
    process_recent_tracks(raw_data, processed)

    return processed

def process_top_artists(term, processed_artists, artists_data):
    processed_artists[term] = [process_artist(item) for item in artists_data.get('items', []) if process_artist(item) is not None]

def process_recent_tracks(raw_data, processed):
    processed['recent_tracks'] = [process_track(item) for item in raw_data.get('recent_tracks', {}).get('items', []) if process_track(item) is not None]

def ritual():
    extract()
    read()
    write()
    print("Full soul ritual complete.")

def extract():
    print("Extracting your soul from Spotify...")
    try:
        # Validate Spotify credentials
        if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET or not SPOTIPY_REDIRECT_URI:
            raise ValueError("Missing Spotify API credentials. Please check your environment variables.")
        
        # Ensure Spotify instance is initialized
        if not sp or not isinstance(sp, Spotify):
            raise RuntimeError("Spotify instance is not properly initialized. Check your authentication flow.")
        
        data = {
            "user_profile": sp.current_user(),
            "top_tracks": {
                "short_term": sp.current_user_top_tracks(time_range='short_term', limit=50),
                "medium_term": sp.current_user_top_tracks(time_range='medium_term', limit=50),
                "long_term": sp.current_user_top_tracks(time_range='long_term', limit=50)
            },
            "top_artists": {
                "short_term": sp.current_user_top_artists(time_range='short_term', limit=50),
                "medium_term": sp.current_user_top_artists(time_range='medium_term', limit=50),
                "long_term": sp.current_user_top_artists(time_range='long_term', limit=50)
            },
            "recent_tracks": sp.current_user_recently_played(limit=10)
        }
        raw_path.parent.mkdir(exist_ok=True)
        with open(raw_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Soul extracted and saved to {raw_path}")
    except ValueError as ve:
        print(f"Validation error: {ve}")
    except RuntimeError as re:
        print(f"Runtime error: {re}")
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}")

def write():
    landing_folder.mkdir(exist_ok=True)
    i = 1
    while (landing_folder / f'the_end_{i}.json').exists():
        i += 1
    dest_path = landing_folder / f'the_end_{i}.json'
    if not raw_path.exists():
        print("No extracted soul found. Run with --extract first.")
        return
    with open(raw_path, 'r') as f:
        raw_data = json.load(f)
    processed_data = process_soul_data(raw_data)
    with open(dest_path, 'w') as f:
        json.dump(processed_data, f, indent=2)
    print(f"Copied processed soul data to {dest_path}")

def read():
    if not raw_path.exists():
        print("No extracted soul found. Run with --extract first.")
        return
    with open(raw_path, 'r') as f:
        data = json.load(f)
    # Display user profile information
    user_profile = data.get('user_profile', {})
    print("\n--- User Profile ---")
    print(f"Display Name: {user_profile.get('display_name', 'N/A')}")
    print(f"Email: {user_profile.get('email', 'N/A')}")
    print(f"Spotify URI: {user_profile.get('uri', 'N/A')}")
    print(f"Profile URL: {user_profile.get('external_urls', {}).get('spotify', 'N/A')}")
    print("--------------------\n")
    display_raw_data(data)

def display_raw_data(data):
    pprint(data)

import argparse

# CLI interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and process Spotify soul data.")
    parser.add_argument("--extract", action="store_true", help="Extract soul data from Spotify")
    parser.add_argument("--read", action="store_true", help="Print soul data to terminal")
    parser.add_argument("--write", action="store_true", help="Save numbered copy to final_landing")
    parser.add_argument("--ritual", action="store_true", help="Do all 3 steps automatically")

    args = parser.parse_args()

    if args.extract:
        extract()
    if args.read:
        read()
    if args.write:
        write()
    if args.ritual:
        ritual()