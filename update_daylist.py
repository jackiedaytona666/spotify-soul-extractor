# update_daylist.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv(dotenv_path="/Users/stuartholmberg/servers/code/spotify-soul/.env")

# Debug environment variables
print("🔍 Environment check:")
print(f"Client ID: {os.getenv('SPOTIPY_CLIENT_ID')}")
print(f"Redirect URI: {os.getenv('SPOTIPY_REDIRECT_URI')}")

# Ensure the environment variables are loaded   
if not all([os.getenv("SPOTIPY_CLIENT_ID"), os.getenv("SPOTIPY_CLIENT_SECRET"), os.getenv("SPOTIPY_REDIRECT_URI")]):
    raise EnvironmentError(
        "Missing required environment variables for Spotify API authentication."
    )

# Initialize Spotipy with OAuth - including ALL required scopes
auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=[
        "playlist-modify-public",      # REQUIRED for modifying public playlists
        "playlist-modify-private",     # REQUIRED for modifying private playlists
        "playlist-read-private",       # To read private playlists
        "user-top-read",              # Your existing scope
        "user-read-recently-played",   # Your existing scope
        "user-library-read"           # Your existing scope
    ],
    cache_path=".spotify_cache",  # Store auth token locally
    open_browser=False  # Don't auto-open browser
)

print("🔑 Creating Spotify client...")

# Check if we have a valid token
token_info = auth_manager.get_cached_token()
if not token_info:
    # Generate the authorization URL manually
    auth_url = auth_manager.get_authorize_url()
    print("\n" + "="*60)
    print("🚀 SPOTIFY AUTHORIZATION REQUIRED")
    print("="*60)
    print(f"Please go to this URL in your browser:")
    print(f"\n{auth_url}\n")
    print("After logging in and authorizing the app, you'll be redirected.")
    print("⚠️  IMPORTANT: You'll see an error page - that's normal!")
    print("Copy the ENTIRE URL from your browser (even if it shows an error)")
    print("="*60)
    
    # Get the redirect URL from user
    redirect_response = input("\nPaste the full redirect URL here: ").strip()
    
    # Extract the authorization code manually
    try:
        # Check if this is an error redirect
        if 'exit?status=error' in redirect_response:
            print("❌ It looks like the authorization was cancelled or failed.")
            print("Please try again and make sure to authorize the app.")
            exit(1)
        
        # Parse the URL to get the query parameters
        parsed_url = urllib.parse.urlparse(redirect_response)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            code = query_params['code'][0]
            print(f"✅ Authorization code extracted: {code[:20]}...")
            
            # Get the access token
            token_info = auth_manager.get_access_token(code)
            print("✅ Access token obtained successfully!")
        else:
            raise ValueError("No authorization code found in the URL")
            
    except Exception as e:
        print(f"❌ Error extracting authorization code: {e}")
        print("Make sure you copied the complete URL from your browser")
        print("The URL should contain '?code=...' in it")
        exit(1)

# Create the Spotify client instance
sp = spotipy.Spotify(auth_manager=auth_manager)

# Test the connection
try:
    user = sp.current_user()
    print(f"\n✅ Authenticated as: {user['display_name']}")
    
    # DEBUG: Check what scopes we actually have    
    current_token = auth_manager.get_cached_token()
    if current_token:
        print(f"🔍 Current scopes: {current_token.get('scope', 'No scopes found')}")
    else:
        print("🔍 No cached token found")
        
except Exception as e:
    print(f"DEBUG: Updating playlist with {len(track_uris)} tracks: {track_uris}")
    print(f"❌ Authentication failed: {e}")
    exit(1)

# Playlist settings
TARGET_PLAYLIST_NAME = "Echoes from Nowhere: Saints of the Shift"
NEW_DESCRIPTION = (
    "No skips. No fame. Just 25 songs you've never heard and already miss.\n"
    "Come shift with the saints. Don't tell anyone who sent you."
)

# Load track URIs from an external file if it exists, otherwise use the hardcoded list
TRACK_URIS_FILE = "track_uris.txt"
if os.path.isfile(TRACK_URIS_FILE):
    with open(TRACK_URIS_FILE, "r") as f:
        TRACK_URIS = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
else:
    TRACK_URIS = [
        "spotify:track:4TwN8s1twnLNuHRbwU9H3j",  # Maruja – The Tinker
        "spotify:track:2nnd6bCJjH7gZzIWTkDZc2",  # Niku – Twelve Foot Lungs
        "spotify:track:6oAVCj6mLEwQnUjYcKx2O6",  # Karima Walker – Reconstellated
        "spotify:track:2RscNRtYKiVEvGxPBLQH7l",  # GracieHorse – White Stetson
        "spotify:track:5dCtD3UNSkXQqAgKKLIFNG",  # Yosa Peit – Mycelial Madness
        "spotify:track:0WYkaDfVfBLFL7GHqk3iSC",  # Flaer – Cat Queen
        "spotify:track:4JQo8j5IjllshX7iAI9au4",  # Lamusa II – Meta-moto
        "spotify:track:0ckczDPt97SGj1ZrK0g3HE",  # Time Wharp – Zentropy
        "spotify:track:1hWz5QpKMW3N3ZnU8PZ3SK",  # Chuck Johnson – Crossing the Pass
        "spotify:track:3NbbLO63EbBTchcxUWSQCD",  # Ninajirachi – Petroleum
        "spotify:track:4H4pSYshRgBKm1QGbxfzkO",  # Ravioli Me Away – Cat Call
        "spotify:track:3GMqOgW2w9KnFhiw5G0uIN",  # La Neve – A Pretty Red
        "spotify:track:0PoMRaLkMnRbwFKQnppfbk",  # Jabu – Wounds
        "spotify:track:5HITgwc7rAVcrlXc1oA2cP",  # Anadol – Cübük
        "spotify:track:7k1BPXyqXYOQPg62WhF5En",  # Black Dresses – Wiggle
        "spotify:track:2wNcebnT3aATulnFXPWhbE",  # DJ Plead – Salt and Metal
        "spotify:track:4KyoQoEkgkaFqTGi62I2S4",  # Oklou – Friendless
        "spotify:track:3YPftYPxuMC2raIbcAoCV5",  # Claudia Meza – Ambiente Parado
        "spotify:track:0MiZrGcWjc2AKacRMVoQ6B",  # Free Love – Et Avant
        "spotify:track:0ueG0OH5goLJgGkzOkTjC4",  # John Glacier – If Anything
        "spotify:track:2NLWcZmhz8tpGrMIfZ5MYN",  # Cruel Diagonals – Render Arcane
        "spotify:track:6DUaScxCDXROsr7eh72ENd",  # Debby Friday – Runnin
        "spotify:track:1ixJb9AhRY1mVu0bRMKcFh",  # uon – Solaris Vol II
        "spotify:track:4zErtyfOZtWyMWLL6UKoRp",  # LYZZA – Black Matter
        "spotify:track:7xm58zMEbzkBLf9BEG6ZV7"   # Coucou Chloe – Halo
    ]

def find_playlist_id(sp, name):
    """Find the Spotify playlist ID for a given playlist name."""
    print(f"🔍 Looking for playlist: '{name}'")
    playlists = sp.current_user_playlists()
    for item in playlists['items']:
        if item['name'] == name:
            print(f"✅ Found playlist: {item['id']}")
            return item['id']
    raise ValueError(f"Playlist '{name}' not found.")

def update_playlist(sp, playlist_id, track_uris, description):
    """Replace all tracks in the specified Spotify playlist and update its description."""
    print(f"🔄 Updating playlist {playlist_id}...")
    sp.playlist_replace_items(playlist_id, track_uris)
    sp.playlist_change_details(playlist_id, description=description)
    print(f"✅ Playlist updated: {playlist_id}")
    print(f"🎵 {len(track_uris)} tracks replaced.")
    print(f"📝 Description set.")

if __name__ == "__main__":
    try:
        playlist_id = find_playlist_id(sp, TARGET_PLAYLIST_NAME)
        update_playlist(sp, playlist_id, TRACK_URIS, NEW_DESCRIPTION)
    except Exception as e:

        print(f"❌ Error: {e}")