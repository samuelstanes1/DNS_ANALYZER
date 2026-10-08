"""MongoDB connection management and collection access.

All connection parameters are dynamically loaded from environment variables
to prevent hardcoding of sensitive credentials.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo.errors

# Load environment variables from .env if present
load_dotenv()

# Configuration keys
ENV_MONGODB_URL = "MONGODB_URL"
ENV_DATABASE_NAME = "DATABASE_NAME"
DEFAULT_DATABASE_NAME = "dns_health"
ANALYSIS_COLLECTION_NAME = "analyses"


class MongoDBManager:
    """Manages asynchronous MongoDB client lifecycle and database collections."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.last_error: Optional[str] = None

    def get_connection_url(self) -> str:
        """Fetch MongoDB URL from environment variables."""
        return os.getenv(ENV_MONGODB_URL, "").strip()

    def get_database_name(self) -> str:
        """Fetch database name from environment variables with fallback."""
        return os.getenv(ENV_DATABASE_NAME, DEFAULT_DATABASE_NAME).strip() or DEFAULT_DATABASE_NAME

    async def connect(self, mongodb_url: Optional[str] = None, database_name: Optional[str] = None) -> bool:
        """Initialize the AsyncIOMotorClient connection."""
        url = mongodb_url if mongodb_url is not None else self.get_connection_url()
        db_name = database_name if database_name is not None else self.get_database_name()

        if not url or not url.strip():
            self.last_error = "MONGODB_URL is empty or not set"
            return False

        try:
            self.client = AsyncIOMotorClient(
                url,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
            )
            self.db = self.client[db_name]
            # Verify connectivity with a quick ping
            await self.client.admin.command("ping")
            self.last_error = None
            return True
        except pymongo.errors.PyMongoError as e:
            self.last_error = str(e)
            return False
        except Exception as e:
            self.last_error = str(e)
            return False

    async def close(self) -> None:
        """Close MongoDB connection gracefully."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    async def ping(self) -> bool:
        """Perform a ping command against MongoDB to check connection health."""
        if self.client is None:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_analysis_collection(self) -> Optional[AsyncIOMotorCollection]:
        """Expose the analyses collection."""
        if self.db is not None:
            return self.db[ANALYSIS_COLLECTION_NAME]
        return None


# Global singleton database manager instance
db_manager = MongoDBManager()


def get_db_manager() -> MongoDBManager:
    """Provide the global MongoDB manager instance."""
    return db_manager


def get_analysis_collection() -> Optional[AsyncIOMotorCollection]:
    """Helper function to directly access the analyses collection."""
    return db_manager.get_analysis_collection()
