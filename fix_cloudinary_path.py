# fix_cloudinary_paths.py
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("MONGODB_DB_NAME", "dhun_music")

async def fix():
    print("Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    songs = db["songs"]

    print("Fetching songs...")
    fixed = 0
    total = 0

    async for song in songs.find({}):
        total += 1
        updates = {}

        audio_id = song.get("audio_file_id", "") or ""
        if audio_id and audio_id.count("dhun/audio") > 1:
            fixed_id = "dhun/audio/" + audio_id.split("dhun/audio/")[-1]
            updates["audio_file_id"] = fixed_id
            print(f"Audio: {audio_id} → {fixed_id}")

        lyrics_id = song.get("lyrics_file_id", "") or ""
        if lyrics_id and lyrics_id.count("dhun/lyrics") > 1:
            fixed_id = "dhun/lyrics/" + lyrics_id.split("dhun/lyrics/")[-1]
            updates["lyrics_file_id"] = fixed_id
            print(f"Lyrics: {lyrics_id} → {fixed_id}")

        cover_id = song.get("cover_file_id", "") or ""
        if cover_id and cover_id.count("dhun/covers") > 1:
            fixed_id = "dhun/covers/" + cover_id.split("dhun/covers/")[-1]
            updates["cover_file_id"] = fixed_id
            print(f"Cover: {cover_id} → {fixed_id}")

        if updates:
            await songs.update_one(
                {"id": song["id"]},
                {"$set": updates}
            )
            fixed += 1

    print(f"\nTotal: {total} | Fixed: {fixed}")
    client.close()

asyncio.run(fix())