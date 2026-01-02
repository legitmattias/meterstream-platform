import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection handler."""
    
    client: Optional[AsyncIOMotorClient] = None
    
    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        # Verify connection
        await self.client.admin.command("ping")
        logger.info("Connected to MongoDB database: %s", settings.database_name)
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def get_database(self):
        """Get the database instance."""
        return self.client[settings.database_name]
    
    def get_users_collection(self):
        """Get the users collection."""
        return self.get_database()["users"]

    def get_refresh_tokens_collection(self):
        """Get the refresh_tokens collection."""
        return self.get_database()["refresh_tokens"]


# Singleton instance
mongodb = MongoDB()


async def get_users_collection():
    """Dependency for FastAPI routes."""
    return mongodb.get_users_collection()


async def get_refresh_tokens_collection():
    """Dependency for FastAPI routes."""
    return mongodb.get_refresh_tokens_collection()
