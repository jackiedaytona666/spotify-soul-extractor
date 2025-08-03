# AI-Powered Spotify Playlist Generator

This project uses a Python script to automatically populate a Spotify playlist from a simple list of songs.

## How It Works

The system is split into two main scripts:

1.  **`find_songs.py`**: You provide a simple list of songs in the format `"Artist - Song Title"`. This script searches Spotify for each song, finds its unique ID (URI), and saves these URIs into a file named `track_uris.txt`.
2.  **`update_daylist.py`**: This script reads the song URIs from `track_uris.txt` and populates a target playlist on your Spotify account. If the playlist doesn't exist, it will be created automatically.

---

## How to Create a New Populated Playlist

Follow these four steps to create a new playlist with your chosen songs.

### Step 1: Create Your Song List

Open the `find_songs.py` file and edit the `song_list` variable. Add the songs you want, making sure each entry is a string in the format `"Artist - Song Title"`.

```python

### Step 2: Find the Spotify IDs

Run the `find_songs.py` script from your terminal. This will search for your songs and create the `track_uris.txt` file.

```bash
python3 find_songs.py
```

The script will print the songs it finds. Review the output to make sure it found the correct tracks.

### Step 3: Define Your Target Playlist

Open the `update_daylist.py` file and change the `TARGET_PLAYLIST_NAME` and `TARGET_PLAYLIST_DESCRIPTION` variables to whatever you want your new playlist to be called and described.

```python
# update_daylist.py

# ... (other code)

# Playlist settings
TARGET_PLAYLIST_NAME = "My New Awesome Playlist"
TARGET_PLAYLIST_DESCRIPTION = "The best songs ever, curated by my AI."

# ... (other code)
```

### Step 4: Populate the Playlist

Run the main `update_daylist.py` script from your terminal.

```bash
python3 update_daylist.py
```

The script will now connect to your Spotify, create the new playlist (or find it if it already exists), and fill it with the songs you chose in Step 1.

That's it! You can repeat this process to create as many AI-populated playlists as you want.
