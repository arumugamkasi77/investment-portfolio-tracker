from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import pymongo

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import TradeModel, TradeCreateRequest, TradeUpdateRequest
from database import get_trades_collection, get_portfolios_collection

router = APIRouter(prefix="/trades", tags=["trades"])

def serialize_trade(trade) -> dict:
    """Convert MongoDB document to dict with string _id"""
    if trade:
        trade["_id"] = str(trade["_id"])
        # Convert datetime objects to ISO strings for JSON serialization
        if "trade_date" in trade:
            trade["trade_date"] = trade["trade_date"].isoformat()
        if "created_at" in trade:
            trade["created_at"] = trade["created_at"].isoformat()
        if "updated_at" in trade:
            trade["updated_at"] = trade["updated_at"].isoformat()
    return trade

@router.post("/", response_model=dict)
async def create_trade(trade_request: TradeCreateRequest):
    """Create a new trade"""
    trades_collection = get_trades_collection()
    portfolios_collection = get_portfolios_collection()
    
    # Create or update portfolio
    portfolio_filter = {"portfolio_name": trade_request.portfolio_name}
    portfolio_update = {
        "$setOnInsert": {
            "portfolio_name": trade_request.portfolio_name,
            "created_at": datetime.now()
        },
        "$set": {"updated_at": datetime.now()}
    }
    await portfolios_collection.update_one(
        portfolio_filter, portfolio_update, upsert=True
    )
    
    # Create trade document
    trade_data = trade_request.dict()
    if trade_data.get("trade_date") is None:
        trade_data["trade_date"] = datetime.now()
    trade_data["created_at"] = datetime.now()
    trade_data["updated_at"] = datetime.now()
    
    # Insert trade
    result = await trades_collection.insert_one(trade_data)
    
    if result.inserted_id:
        # Retrieve and return the created trade
        created_trade = await trades_collection.find_one({"_id": result.inserted_id})
        return {
            "message": "Trade created successfully",
            "trade_id": str(result.inserted_id),
            "trade": serialize_trade(created_trade)
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create trade")

@router.get("/", response_model=List[dict])
async def get_trades(
    portfolio_name: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get trades with optional filtering"""
    trades_collection = get_trades_collection()
    
    # Build filter
    filter_dict = {}
    if portfolio_name:
        filter_dict["portfolio_name"] = portfolio_name
    if symbol:
        filter_dict["symbol"] = symbol
    
    # Execute query
    cursor = trades_collection.find(filter_dict).sort("trade_date", -1).skip(offset).limit(limit)
    trades = await cursor.to_list(length=limit)
    
    return [serialize_trade(trade) for trade in trades]

@router.get("/{trade_id}", response_model=dict)
async def get_trade(trade_id: str):
    """Get a specific trade by ID"""
    trades_collection = get_trades_collection()
    
    try:
        object_id = ObjectId(trade_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid trade ID format")
    
    trade = await trades_collection.find_one({"_id": object_id})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return serialize_trade(trade)

@router.put("/{trade_id}", response_model=dict)
async def update_trade(trade_id: str, trade_update: TradeUpdateRequest):
    """Update a specific trade"""
    trades_collection = get_trades_collection()
    
    try:
        object_id = ObjectId(trade_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid trade ID format")
    
    # Build update document
    update_data = {k: v for k, v in trade_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now()
    
    # Update trade
    result = await trades_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Return updated trade
    updated_trade = await trades_collection.find_one({"_id": object_id})
    return {
        "message": "Trade updated successfully",
        "trade": serialize_trade(updated_trade)
    }

@router.delete("/{trade_id}")
async def delete_trade(trade_id: str):
    """Delete a specific trade"""
    trades_collection = get_trades_collection()
    
    try:
        object_id = ObjectId(trade_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid trade ID format")
    
    result = await trades_collection.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return {"message": "Trade deleted successfully"}

@router.get("/portfolio/{portfolio_name}/summary")
async def get_portfolio_summary(portfolio_name: str):
    """Get summary of trades for a specific portfolio"""
    trades_collection = get_trades_collection()
    
    pipeline = [
        {"$match": {"portfolio_name": portfolio_name}},
        {
            "$group": {
                "_id": {
                    "symbol": "$symbol",
                    "instrument_type": "$instrument_type"
                },
                "total_trades": {"$sum": 1},
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
                "total_amount_bought": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "BUY"]},
                            {"$multiply": ["$quantity", "$executed_price"]},
                            0
                        ]
                    }
                },
                "total_amount_sold": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$trade_type", "SELL"]},
                            {"$multiply": ["$quantity", "$executed_price"]},
                            0
                        ]
                    }
                },
                "total_brokerage": {"$sum": "$brokerage"}
            }
        },
        {
            "$project": {
                "symbol": "$_id.symbol",
                "instrument_type": "$_id.instrument_type",
                "total_trades": 1,
                "net_quantity": {"$subtract": ["$total_quantity_bought", "$total_quantity_sold"]},
                "total_quantity_bought": 1,
                "total_quantity_sold": 1,
                "total_amount_bought": 1,
                "total_amount_sold": 1,
                "net_amount": {"$subtract": ["$total_amount_sold", "$total_amount_bought"]},
                "total_brokerage": 1,
                "average_buy_price": {
                    "$cond": [
                        {"$gt": ["$total_quantity_bought", 0]},
                        {"$divide": ["$total_amount_bought", "$total_quantity_bought"]},
                        0
                    ]
                }
            }
        }
    ]
    
    cursor = trades_collection.aggregate(pipeline)
    summary = await cursor.to_list(length=None)
    
    return summary
