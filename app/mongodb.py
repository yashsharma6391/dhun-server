from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[settings.MONGODB_DB_NAME]
            logger.info("MongoDB connected ✅")
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
            raise

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")

mongodb = MongoDB()

# ─── All Collections ──────────────────────────────────────
def get_users_collection():
    return mongodb.db["users"]

def get_channels_collection():
    return mongodb.db["channels"]

def get_songs_collection():
    return mongodb.db["songs"]

def get_likes_collection():
    return mongodb.db["song_likes"]

def get_follows_collection():
    return mongodb.db["channel_follows"]

def get_access_requests_collection():
    return mongodb.db["access_requests"]

def get_granted_access_collection():
    return mongodb.db["granted_access"]