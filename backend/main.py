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
from routers import trades, portfolios, snapshots, portfolio_static, stocks, options, market_data, enhanced_snapshots, scheduler, portfolio_analytics
# from routers import ai_predictions  # Temporarily disabled to fix main app

load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    try:
        await connect_to_mongo()
        print("Database connection established successfully")
        print("Database ready - daily snapshots can be triggered manually")
    except Exception as e:
        print(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
        print("Database connection closed")
    except Exception as e:
        print(f"Error closing database connection: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Investment Portfolio Tracker", 
    version="1.0.0",
    lifespan=lifespan
)

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

# Include enhanced functionality (separate layer)
app.include_router(enhanced_snapshots.router)
app.include_router(scheduler.router)

# Include portfolio analytics
app.include_router(portfolio_analytics.router)

# Include AI predictions
# app.include_router(ai_predictions.router) # Temporarily disabled to fix main app

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
