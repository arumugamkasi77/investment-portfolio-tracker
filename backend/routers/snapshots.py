from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, date, timedelta
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DailySnapshotModel
from database import (
    get_trades_collection,
    get_portfolios_collection, 
    get_market_data_collection,
    get_daily_snapshots_collection
)

router = APIRouter(prefix="/snapshots", tags=["snapshots"])

def serialize_snapshot(snapshot) -> dict:
    """Convert MongoDB document to dict with string _id"""
    if snapshot:
        snapshot["_id"] = str(snapshot["_id"])
        if "snapshot_date" in snapshot:
            snapshot["snapshot_date"] = snapshot["snapshot_date"].isoformat()
        if "created_at" in snapshot:
            snapshot["created_at"] = snapshot["created_at"].isoformat()
    return snapshot

async def calculate_portfolio_positions(portfolio_name: str, as_of_date: date = None):
    """Calculate portfolio positions as of a specific date"""
    if as_of_date is None:
        as_of_date = date.today()
    
    trades_collection = get_trades_collection()
    market_data_collection = get_market_data_collection()
    
    # Get trades up to the specified date
    pipeline = [
        {
            "$match": {
                "portfolio_name": portfolio_name,
                "trade_date": {"$lte": datetime.combine(as_of_date, datetime.min.time())}
            }
        },
        {
            "$group": {
                "_id": {
                    "symbol": "$symbol",
                    "instrument_type": "$instrument_type"
                },
                "total_quantity_bought": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "BUY"]},
                            "$quantity",
                            0
                        ]
                    }
                },
                "total_quantity_sold": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "SELL"]},
                            "$quantity",
                            0
                        ]
                    }
                },
                "total_cost_bought": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "BUY"]},
                            {"$add": [
                                {"$multiply": ["$quantity", "$executed_price"]},
                                "$brokerage"
                            ]},
                            0
                        ]
                    }
                },
                "total_proceeds_sold": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "SELL"]},
                            {"$subtract": [
                                {"$multiply": ["$quantity", "$executed_price"]},
                                "$brokerage"
                            ]},
                            0
                        ]
                    }
                },
                "realized_pl": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "SELL"]},
                            {"$subtract": [
                                {"$multiply": ["$quantity", "$executed_price"]},
                                "$brokerage"
                            ]},
                            0
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "symbol": "$_id.symbol",
                "instrument_type": "$_id.instrument_type",
                "position_quantity": {"$subtract": ["$total_quantity_bought", "$total_quantity_sold"]},
                "total_cost": "$total_cost_bought",
                "total_proceeds": "$total_proceeds_sold",
                "net_cost": {"$subtract": ["$total_cost_bought", "$total_proceeds_sold"]},
                "realized_pl": "$realized_pl",
                "average_cost": {
                    "$cond": [
                        {"$gt": [{"$subtract": ["$total_quantity_bought", "$total_quantity_sold"]}, 0]},
                        {"$divide": [
                            {"$subtract": ["$total_cost_bought", "$total_proceeds_sold"]},
                            {"$subtract": ["$total_quantity_bought", "$total_quantity_sold"]}
                        ]},
                        0
                    ]
                }
            }
        },
        {
            "$match": {
                "position_quantity": {"$ne": 0}
            }
        }
    ]
    
    cursor = trades_collection.aggregate(pipeline)
    positions = await cursor.to_list(length=None)
    
    return positions

async def create_daily_snapshot(portfolio_name: str = None, snapshot_date: date = None):
    """Create daily snapshots for all portfolios or a specific portfolio"""
    if snapshot_date is None:
        snapshot_date = date.today()
    
    portfolios_collection = get_portfolios_collection()
    daily_snapshots_collection = get_daily_snapshots_collection()
    market_data_collection = get_market_data_collection()
    
    # Get portfolios to snapshot
    if portfolio_name:
        portfolios = [{"portfolio_name": portfolio_name}]
    else:
        cursor = portfolios_collection.find({}, {"portfolio_name": 1})
        portfolios = await cursor.to_list(length=None)
    
    snapshots_created = 0
    
    for portfolio in portfolios:
        portfolio_name = portfolio["portfolio_name"]
        
        # Calculate positions for this portfolio
        positions = await calculate_portfolio_positions(portfolio_name, snapshot_date)
        
        for position in positions:
            symbol = position["symbol"]
            
            # Get market price for the date (fallback to average cost if not available)
            market_data = await market_data_collection.find_one({"symbol": symbol})
            market_price = market_data["current_price"] if market_data else position["average_cost"]
            
            # Calculate values
            market_value = position["position_quantity"] * market_price
            unrealized_pl = market_value - position["net_cost"]
            total_pl = position["realized_pl"] + unrealized_pl
            
            # Check if snapshot already exists
            existing_snapshot = await daily_snapshots_collection.find_one({
                "portfolio_name": portfolio_name,
                "symbol": symbol,
                "snapshot_date": snapshot_date
            })
            
            if not existing_snapshot:
                # Create snapshot document
                snapshot_data = {
                    "portfolio_name": portfolio_name,
                    "symbol": symbol,
                    "snapshot_date": snapshot_date,
                    "position_quantity": position["position_quantity"],
                    "average_cost": position["average_cost"],
                    "market_price": market_price,
                    "market_value": market_value,
                    "unrealized_pl": unrealized_pl,
                    "realized_pl": position["realized_pl"],
                    "total_pl": total_pl,
                    "created_at": datetime.now()
                }
                
                await daily_snapshots_collection.insert_one(snapshot_data)
                snapshots_created += 1
    
    return snapshots_created

@router.post("/create")
async def create_snapshot_manual(portfolio_name: Optional[str] = None, snapshot_date: Optional[str] = None):
    """Manually create daily snapshot(s)"""
    if snapshot_date:
        try:
            snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        snapshot_date = date.today()
    
    snapshots_created = await create_daily_snapshot(portfolio_name, snapshot_date)
    
    return {
        "message": f"Created {snapshots_created} snapshots",
        "portfolio_name": portfolio_name or "all portfolios",
        "snapshot_date": snapshot_date.isoformat()
    }

@router.get("/")
async def get_snapshots(
    portfolio_name: Optional[str] = None,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get daily snapshots with optional filtering"""
    daily_snapshots_collection = get_daily_snapshots_collection()
    
    # Build filter
    filter_dict = {}
    if portfolio_name:
        filter_dict["portfolio_name"] = portfolio_name
    if symbol:
        filter_dict["symbol"] = symbol
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            try:
                date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        if end_date:
            try:
                date_filter["$lte"] = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        filter_dict["snapshot_date"] = date_filter
    
    cursor = daily_snapshots_collection.find(filter_dict).sort("snapshot_date", -1).limit(limit)
    snapshots = await cursor.to_list(length=limit)
    
    return [serialize_snapshot(snapshot) for snapshot in snapshots]

@router.get("/pl-analysis/{portfolio_name}")
async def get_pl_analysis(portfolio_name: str, symbol: Optional[str] = None):
    """Get DTD, MTD, YTD P&L analysis for a portfolio"""
    daily_snapshots_collection = get_daily_snapshots_collection()
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    # Build filter
    filter_dict = {"portfolio_name": portfolio_name}
    if symbol:
        filter_dict["symbol"] = symbol
    
    # Get current positions (today's calculated values)
    current_positions = await calculate_portfolio_positions(portfolio_name, today)
    
    result = []
    
    for position in current_positions:
        symbol = position["symbol"]
        
        # Get snapshots for comparison
        yesterday_snapshot = await daily_snapshots_collection.find_one({
            "portfolio_name": portfolio_name,
            "symbol": symbol,
            "snapshot_date": yesterday
        })
        
        month_start_snapshot = await daily_snapshots_collection.find_one({
            "portfolio_name": portfolio_name,
            "symbol": symbol,
            "snapshot_date": month_start
        })
        
        year_start_snapshot = await daily_snapshots_collection.find_one({
            "portfolio_name": portfolio_name,
            "symbol": symbol,
            "snapshot_date": year_start
        })
        
        # Calculate current total P&L (realized + unrealized)
        current_total_pl = position["realized_pl"]  # This needs to be calculated properly
        
        # Calculate DTD, MTD, YTD P&L
        dtd_pl = 0.0
        mtd_pl = 0.0
        ytd_pl = 0.0
        
        if yesterday_snapshot:
            dtd_pl = current_total_pl - yesterday_snapshot["total_pl"]
        
        if month_start_snapshot:
            mtd_pl = current_total_pl - month_start_snapshot["total_pl"]
        
        if year_start_snapshot:
            ytd_pl = current_total_pl - year_start_snapshot["total_pl"]
        
        position_analysis = {
            "portfolio_name": portfolio_name,
            "symbol": symbol,
            "current_total_pl": current_total_pl,
            "dtd_pl": round(dtd_pl, 2),
            "mtd_pl": round(mtd_pl, 2),
            "ytd_pl": round(ytd_pl, 2),
            "analysis_date": today.isoformat()
        }
        
        result.append(position_analysis)
    
    return result

# Note: Scheduler functionality can be added later with proper configuration
# For now, snapshots can be created manually via the API endpoints
