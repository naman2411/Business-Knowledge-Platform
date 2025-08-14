﻿from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
_client = None
def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client
def get_db():
    return get_client()[settings.mongo_db]
