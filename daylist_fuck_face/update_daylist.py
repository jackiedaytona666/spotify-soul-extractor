# update_daylist.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time
import random

# Load environment variables
load_dotenv(dotenv_path="/Users/stuartholmberg/servers/code/spotify-soul/.env")

# Ensure the environment variables are loaded
if not all([os.getenv("SPOTIPY_CLIENT_ID"), os.getenv("SPOTIPY_CLIENT_SECRET"), os.getenv("SPOTIPY_REDIRECT_URI")]):
    raise EnvironmentError(
        "Missing required environment variables for Spotify API authentication."
    )

# Initialize Spotipy with OAuth
auth_manager = SpotifyOAuth(
    scope=[
        "playlist-modify-public",
        "playlist-modify-private",
        "playlist-read-private",
    ],
    cache_path=".spotify_cache",
    open_browser=True  # This will try to open a browser for you
)

sp = spotipy.Spotify(auth_manager=auth_manager)

# Playlist settings
TARGET_PLAYLIST_NAME = "FINAL BOSS HP = 100"
TARGET_PLAYLIST_DESCRIPTION = "EAT ITS ASS"

def get_all_playlists():
    playlists = []
    results = sp.current_user_playlists(limit=50)
    playlists.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])
    return playlists

def find_or_create_playlist(user_id, name):
    """Find a playlist by name, or create it if it doesn't exist."""
    playlists = get_all_playlists()
    for item in playlists:
        if item['name'] == name:
            print(f"✅ Found playlist: {item['id']}")
            return item['id']

    # If not found, create it
    print(f"Playlist '{name}' not found. Creating it...")
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,  # Use the name as-is for public release
        public=True,  # Make playlist public
        description="soundtrack for when your reflection glitches and winks back at you synthetic mascara running you look hot as hell bleeding in the club"
    )
    print(f"🎯 Created playlist: {playlist['name']} → {playlist['id']}")
    return playlist['id']

def update_playlist_humanly(playlist_id, track_uris, description):
    """Update the playlist in a more 'human' way.
    This clears the playlist and adds tracks one by one with a random delay.
    """
    if not track_uris:
        print("⚠️ No tracks to add. Skipping update.")
        return

    print(f"Clearing all tracks from playlist '{TARGET_PLAYLIST_NAME}'...")
    sp.playlist_replace_items(playlist_id, [])
    print("Playlist cleared.")

    print(f"Adding {len(track_uris)} tracks one by one...")
    for i, track_uri in enumerate(track_uris):
        try:
            sp.playlist_add_items(playlist_id, [track_uri])
            # Simulate human typing speed with a random delay
            delay = random.uniform(0.7, 2.5)
            print(f"  {i+1}/{len(track_uris)}: Added track {track_uri} (waiting {delay:.2f}s)")
            time.sleep(delay)
        except Exception as e:
            print(f"  ❌ Failed to add track {track_uri}: {e}")

    # Update the playlist description at the end
    sp.playlist_change_details(playlist_id, description=description)
    print(f"\n✅ Playlist '{TARGET_PLAYLIST_NAME}' updated successfully.")

# Load track URIs from an external file or use a hardcoded list
TRACK_URIS_FILE = "track_uris.txt"
if os.path.isfile(TRACK_URIS_FILE):
    with open(TRACK_URIS_FILE, "r") as f:
        TRACK_URIS = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    print(f"Loaded {len(TRACK_URIS)} tracks from {TRACK_URIS_FILE}")
else:
    TRACK_URIS = [
    "spotify:track:4Bgh6Uv9851EcAMH8IRirR",
    "spotify:track:5h40rH72rWC28mPT8tFn31",
    "spotify:track:5NSdMmd2LnvgDcpLiKeKeD",
    "spotify:track:7dUrhEQguPAglRgnACCzYw",
    "spotify:track:7sKbyYeJnITO1Eh9xd0lKd",
    "spotify:track:1lgIlt243DVXg597hMx3Uf",
    "spotify:track:5alFLxnNmBmTdNM6Oq0nqD",
    "spotify:track:5Zk0IqQrbxjFQyxKHaAcqO",
    "spotify:track:1Nehx06u9ypVSu5NJOev4H",
    "spotify:track:3z1liIZgam8CRi8CaNKyrJ",
    "spotify:track:1Ra4XdTVkEG1PiK6cVX6K0",
    "spotify:track:1rpMOj4kKQbL1pU1t0ijgU",
    "spotify:track:3qJ6JZf3AXWngMFFNB2hH2",
    "spotify:track:3qW9Lmk9Z1DdWhYp2ql8YM",
    "spotify:track:3rKODaKovt5MNYsSRdCaGZ",
    "spotify:track:6fNQ1SIRnmU5vNLo1BdHq1",
    "spotify:track:5qEYCGavhE8tLQF31Edc0n",
    "spotify:track:4vTp1x69fCHyXtLKVuxZHR",
    "spotify:track:1oSIur44a9TYfHyJeCmn4H",
    "spotify:track:7DkTkr6An3zKtfQCPgmgAn",
    "spotify:track:4FRMpWUNnvQq54oEtp1O5I",
    "spotify:track:7vSzOYDQD4HX2tc77Doz7J",
    "spotify:track:3DOwaLAik9ZAdF6c17rKNP",
    "spotify:track:5K9sU7daQyIhtfw4rVCe6j",
    "spotify:track:6C8TVbcdHQ7yLsSCx1uU8f",
]
    
    print("Using hardcoded track list.")

if __name__ == "__main__":
    try:
        user = sp.current_user()
        user_id = user["id"]
        print(f"✅ Authenticated as: {user['display_name']} (id: {user_id})")

        playlist_id = find_or_create_playlist(user_id, TARGET_PLAYLIST_NAME)
        update_playlist_humanly(playlist_id, TRACK_URIS, TARGET_PLAYLIST_DESCRIPTION)

    except Exception as e:
        print(f"❌ Error: {e}")
