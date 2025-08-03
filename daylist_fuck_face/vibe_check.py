import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd

# Add your own Spotify credentials here
SPOTIPY_CLIENT_ID = 'your_client_id'
SPOTIPY_CLIENT_SECRET = 'your_client_secret'

# Authenticate
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# List of track URLs or URIs
track_urls = [
    "https://open.spotify.com/track/0ZNYGrmcehorhh9JOeg5Iv",
    "https://open.spotify.com/track/75IQVo8hqI1iwVZyvkN2VT",
    "https://open.spotify.com/track/4I59UjiR1vDGGdLmdvFoJO",
    "https://open.spotify.com/track/1el1feH98jWUrPpYmu5jN8",
    "https://open.spotify.com/track/7sqii6BhIDpJChYpU3WjwS",
    "https://open.spotify.com/track/0wPfUQUkWcguy2iUH0BWOT",
    "https://open.spotify.com/track/6Ao5d7TMQ92h87jQqSHGyw",
    "https://open.spotify.com/track/0YdFh2OHTAbNqfN1HCBRq1",
    "https://open.spotify.com/track/5MhMXTuVODDF234VDvSxQx",
    "https://open.spotify.com/track/0vtX8UMG38p7IXpP4lZJ2z",
    "https://open.spotify.com/track/3flWoQdYrWyqUsHbURIJby",
    "https://open.spotify.com/track/5oOIGick1Z3cJf60OZZusL",
    "https://open.spotify.com/track/7iKmj1a0DMZExoafuQ1Lmc",
    "https://open.spotify.com/track/2aJDlirz6v2a4HREki98cP",
    "https://open.spotify.com/track/5owacNcWuezb4JHoGdoQSj",
    "https://open.spotify.com/track/6nI1qWkwd3KF3q6RFbmL0B",
    "https://open.spotify.com/track/2X485T9Z5Ly0xyaghN73ed",
    "https://open.spotify.com/track/79Jl8KMvmnXedTjjW6pJan",
    "https://open.spotify.com/track/14gYIWhaZ3kKQiwr7kI4JQ",
    "https://open.spotify.com/track/233AL29SR6QWnD7hu7ylbf",
    "https://open.spotify.com/track/3d3MothkdkkSRU9OD9hZIO",
    "https://open.spotify.com/track/0OQehQY5sa24kxGOOB1Uuu",
    "https://open.spotify.com/track/13N1HPNBK0oU0FbAUZ3xYT",
    "https://open.spotify.com/track/3CFqsproirYuZ6ksCoCwfc",
    "https://open.spotify.com/track/30GGIrrJdSNtecPiFcVP5O",
    "https://open.spotify.com/track/69uPNh3b6VKdMZMbIKYQ1l",
    "https://open.spotify.com/track/023GoM1byudLGkMZDLweRJ",
    "https://open.spotify.com/track/2D4VTAyHTFegKvcw9oRZhX"
]

# Extract track IDs
track_ids = [url.split("/")[-1].split("?")[0] for url in track_urls]

# Get metadata
features = sp.audio_features(track_ids)
metadata = sp.tracks(track_ids)

# Build dataframe
records = []
for i, feat in enumerate(features):
    if feat is None:
        continue
    track_name = metadata['tracks'][i]['name']
    artist_name = metadata['tracks'][i]['artists'][0]['name']
    url = metadata['tracks'][i]['external_urls']['spotify']
    record = {
        'artist': artist_name,
        'track': track_name,
        'url': url,
        'energy': feat['energy'],
        'valence': feat['valence'],
        'tempo': feat['tempo'],
        'danceability': feat['danceability']
    }
    records.append(record)

df = pd.DataFrame(records)

# Sort with custom logic: slow > high energy rise > euphoric dance end
df_sorted = df.sort_values(by=['energy', 'valence', 'tempo', 'danceability'], ascending=[True, True, True, True])

# Output reordered list
print("\n--- REORDERED PLAYLIST ---\n")
for i, row in df_sorted.iterrows():
    print(f"{row['artist']} — {row['track']}\n{row['url']}\n")