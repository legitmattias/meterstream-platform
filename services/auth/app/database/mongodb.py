from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.config import get_settings

settings = get_settings()


class MongoDB:
    """MongoDB connection handler."""
    
    client: Optional[AsyncIOMotorClient] = None
    
    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        # Verify connection
        await self.client.admin.command("ping")
        print(f"✅ Connected to MongoDB: {settings.mongodb_url}")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("❌ Disconnected from MongoDB")
    
    def get_database(self):
        """Get the database instance."""
        return self.client[settings.database_name]
    
    def get_users_collection(self):
        """Get the users collection."""
        return self.get_database()["users"]


# Singleton instance
mongodb = MongoDB()


async def get_users_collection():
    """Dependency for FastAPI routes."""
    return mongodb.get_users_collection()
