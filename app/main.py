from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from app.mongodb import mongodb
from app.config import settings
from app.routers import auth, songs, channels, search, upload

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Dhun Server v2...")

    # MongoDB - ALL data
    try:
        mongodb.connect()
        await mongodb.client.admin.command("ping")
        logger.info("MongoDB ready ✅")

        # Create indexes for performance
        await create_indexes()
        logger.info("MongoDB indexes created ✅")
    except Exception as e:
        logger.error(f"MongoDB error: {e}")

    # Storage provider
    try:
        from app.storage.factory import get_storage
        storage = get_storage()
        logger.info(f"Storage ready: {storage.get_provider_name()} ✅")
    except Exception as e:
        logger.error(f"Storage error: {e}")

    # Local dev only
    if settings.DEBUG:
        os.makedirs("uploads/audio", exist_ok=True)
        os.makedirs("uploads/covers", exist_ok=True)
        os.makedirs("uploads/lyrics", exist_ok=True)

    print("✅ Dhun Server v2 Started!")
    print(f"📦 Storage: {settings.STORAGE_PROVIDER}")
    print(f"🗄️  Database: MongoDB (all data)")
    yield

    mongodb.disconnect()
    print("Server stopped")

async def create_indexes():
    """Create MongoDB indexes for better performance"""
    db = mongodb.db

    # Users indexes
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("username", unique=True)
    await db["users"].create_index("id", unique=True)

    # Channels indexes
    await db["channels"].create_index("id", unique=True)
    await db["channels"].create_index("owner_id")
    await db["channels"].create_index("is_public")

    # Songs indexes
    await db["songs"].create_index("id", unique=True)
    await db["songs"].create_index("channel_id")
    await db["songs"].create_index("is_active")
    await db["songs"].create_index([
        ("title", "text"),
        ("artist", "text"),
        ("album", "text")
    ])

app = FastAPI(
    title="Dhun Music API",
    description="Backend for Dhun Music App",
    version="2.0.0",
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"ERROR: {request.method} {request.url}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.DEBUG:
    try:
        from fastapi.staticfiles import StaticFiles
        if os.path.exists("uploads"):
            app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    except Exception as e:
        logger.warning(f"Static files: {e}")

app.include_router(auth.router, prefix="/v1")
app.include_router(songs.router, prefix="/v1")
app.include_router(channels.router, prefix="/v1")
app.include_router(search.router, prefix="/v1")
app.include_router(upload.router, prefix="/v1")

@app.get("/")
def root():
    return {
        "app": "Dhun Music Server",
        "version": "2.0.0",
        "storage": settings.STORAGE_PROVIDER,
        "database": "MongoDB",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    mongo_ok = "error"
    try:
        await mongodb.client.admin.command("ping")
        mongo_ok = "connected"
    except Exception as e:
        mongo_ok = f"error: {str(e)}"

    storage_ok = "error"
    try:
        from app.storage.factory import get_storage
        storage = get_storage()
        storage_ok = storage.get_provider_name()
    except Exception as e:
        storage_ok = f"error: {str(e)}"

    return {
        "status": "ok" if mongo_ok == "connected" else "degraded",
        "mongodb": mongo_ok,
        "storage": storage_ok
    }