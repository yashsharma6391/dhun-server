# Create fix_urls.py in dhun-server folder
import sqlite3

conn = sqlite3.connect('dhun.db')
cursor = conn.cursor()

BASE_URL = "http://192.168.29.252:8000"

# Get all songs with relative URLs
cursor.execute("SELECT id, audio_url, cover_url FROM songs")
songs = cursor.fetchall()

for song in songs:
    song_id, audio_url, cover_url = song
    
    # Fix audio_url if relative
    if audio_url and not audio_url.startswith('http'):
        new_audio_url = f"{BASE_URL}{audio_url}"
        cursor.execute(
            "UPDATE songs SET audio_url = ? WHERE id = ?",
            (new_audio_url, song_id)
        )
        print(f"Fixed audio: {audio_url} → {new_audio_url}")
    
    # Fix cover_url if relative
    if cover_url and not cover_url.startswith('http'):
        new_cover_url = f"{BASE_URL}{cover_url}"
        cursor.execute(
            "UPDATE songs SET cover_url = ? WHERE id = ?",
            (new_cover_url, song_id)
        )
        print(f"Fixed cover: {cover_url} → {new_cover_url}")

conn.commit()
conn.close()
print("Done! All URLs fixed.")