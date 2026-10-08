"""CLI script to test MongoDB connectivity."""

import asyncio
from app.database.mongodb import MongoDBManager


async def main():
    manager = MongoDBManager()
    url = manager.get_connection_url()
    db_name = manager.get_database_name()

    print("=" * 50)
    print("DNS Health Analyzer - MongoDB Connectivity Test")
    print("=" * 50)
    print(f"Target Database: {db_name}")
    print(f"MongoDB URL Configured: {'YES' if url else 'NO (Set MONGODB_URL in backend/.env)'}")

    if not url:
        print("\n[!] Please create backend/.env with your MONGODB_URL to connect to live MongoDB.")
        print("    Example: MONGODB_URL=mongodb://localhost:27017")
        print("    Example (Atlas): MONGODB_URL=mongodb+srv://<user>:<password>@cluster.mongodb.net")
        return

    print("\nAttempting connection to MongoDB...")
    connected = await manager.connect()

    if connected:
        print("[✓] Successfully connected to MongoDB!")
        print("[✓] Ping check: PASSED")
        collection = manager.get_analysis_collection()
        print(f"[✓] Analysis Collection '{collection.name}' is ready.")
    else:
        print("[✗] Failed to connect to MongoDB.")
        print("    Please verify that your MongoDB service is running and the connection string is valid.")

    await manager.close()
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
