# check_songs.py in dhun-server folder
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb+srv://YashCommTech:%24%40nCtiNn50wEvvH8U8@myprojectsdb.sfmzu9n.mongodb.net/DhunMusic?retryWrites=true&w=majority&appName=MyProjectsDB")
    db = client["dhun_music"]
    songs = db["songs"]
    
    async for song in songs.find({"is_active": True}).limit(3):
        print("Song:", song.get("title"))
        print("audio_file_id:", song.get("audio_file_id"))
        print("cover_file_id:", song.get("cover_file_id"))
        print("lyrics_file_id:", song.get("lyrics_file_id"))
        print("storage_provider:", song.get("storage_provider"))
        print("---")
    
    client.close()

asyncio.run(check())