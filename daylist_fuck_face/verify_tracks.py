
# verify_tracks.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path="/Users/stuartholmberg/servers/code/spotify-soul/.env")

# The same hardcoded list from update_daylist.py
TRACK_URIS = [
"spotify:track:4Bgh6Uv9851EcAMH8IRirR",
"spotify:track:5h40rH72rWC28mPT8tFn31",
"spotify:track:72vmEODDrpQ5wEUhLbiYgI",
"spotify:track:5hvqUsj6aRCNuQdABRbdLi",
"spotify:track:5NSdMmd2LnvgDcpLiKeKeD",
"spotify:track:1TWNKyNQOBfNUkWWs7FooF",
"spotify:track:7dUrhEQguPAglRgnACCzYw",
"spotify:track:7sKbyYeJnITO1Eh9xd0lKd",
"spotify:track:1lgIlt243DVXg597hMx3Uf",
"spotify:track:5alFLxnNmBmTdNM6Oq0nqD",
"spotify:track:5Zk0IqQrbxjFQyxKHaAcqO",
"spotify:track:1Nehx06u9ypVSu5NJOev4H",
"spotify:track:4fIhcJ0bXPwN6G0RejFtYj",
"spotify:track:781V2Y5LPtcpgONEOadadE",
"spotify:track:1M3XB6EUPUZy58Aqt6zbKr",
"spotify:track:3r0gvoaAkWmLdJO4UUv94v",
"spotify:track:7nu0Lc0jJltztDxsGeoPiG",
"spotify:track:6wbAFSrmC2rEQY3OSrj4eH",
"spotify:track:3z1liIZgam8CRi8CaNKyrJ",
"spotify:track:4H9637mkUDyk9Rq0WgDEwc",
"spotify:track:2MpZratWHtEtJB0qVdJSPN",
"spotify:track:2EkOwCBWjcFfhychOKcY7j",
"spotify:track:3NuN59jpH3B5cNa2M4r7XG",
"spotify:track:4lbiIzTsYUT1Kz3KOtQn1b",
"spotify:track:2gmwvGC1yOw8NdMcZE8nfo",
]

try:
    # Initialize Spotipy with OAuth
    auth_manager = SpotifyOAuth(scope=["playlist-read-private"], cache_path=".spotify_cache")
    sp = spotipy.Spotify(auth_manager=auth_manager)

    print("🔍 Verifying the hardcoded track list...")
    
    # Fetch track details from Spotify
    results = sp.tracks(TRACK_URIS)
    
    print("--------------------------------------------------")
    print("GARBAGE LIST CONFIRMED - THESE ARE THE SONGS IN THE SCRIPT:")
    print("--------------------------------------------------")
    for track in results['tracks']:
        artist_name = track['artists'][0]['name']
        track_name = track['name']
        print(f"- {artist_name} - {track_name}")
    print("--------------------------------------------------")

except Exception as e:
    print(f"❌ An error occurred: {e}")
    print("   Please ensure your .env file is set up correctly and you have authenticated.")

