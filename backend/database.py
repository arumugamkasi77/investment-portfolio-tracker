from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# Global database instance
db = Database()

async def get_database():
    """Get database instance"""
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "investment_tracker")
    
    db.client = AsyncIOMotorClient(MONGODB_URL)
    db.database = db.client[DATABASE_NAME]
    
    print(f"Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")

# Collection getters
def get_trades_collection():
    return db.database.trades

def get_portfolios_collection():
    return db.database.portfolios

def get_daily_snapshots_collection():
    return db.database.daily_snapshots

def get_market_data_collection():
    return db.database.market_data

def get_collection(collection_name: str):
    """Get any collection by name"""
    return db.database[collection_name]
