from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import os
import asyncio
from dotenv import load_dotenv
import uvicorn

from database import connect_to_mongo, close_mongo_connection
from routers import trades, portfolios, snapshots, portfolio_static, stocks, options, market_data

load_dotenv()

app = FastAPI(title="Investment Portfolio Tracker", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trades.router)
app.include_router(portfolios.router)
app.include_router(snapshots.router)
app.include_router(portfolio_static.router)
app.include_router(stocks.router)
app.include_router(options.router)
app.include_router(market_data.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and start scheduler"""
    try:
        await connect_to_mongo()
        print("Database connection established successfully")
        
        print("Database ready - daily snapshots can be triggered manually")
            
    except Exception as e:
        print(f"Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    try:
        await close_mongo_connection()
        print("Database connection closed")
    except Exception as e:
        print(f"Error closing database connection: {e}")

@app.get("/")
async def root():
    return {"message": "Investment Portfolio Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    try:
        from database import db
        # Check database connection
        await db.client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
