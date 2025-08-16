from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, date
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import PortfolioSummaryModel
from database import (
    get_trades_collection,
    get_portfolios_collection,
    get_daily_snapshots_collection,
    get_market_data_collection
)
from services.market_data import market_data_service

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

def serialize_portfolio(portfolio) -> dict:
    """Convert MongoDB document to dict with string _id"""
    if portfolio:
        portfolio["_id"] = str(portfolio["_id"])
        if "created_at" in portfolio:
            portfolio["created_at"] = portfolio["created_at"].isoformat()
        if "updated_at" in portfolio:
            portfolio["updated_at"] = portfolio["updated_at"].isoformat()
    return portfolio

@router.get("/", response_model=List[dict])
async def get_portfolios():
    """Get all portfolios"""
    portfolios_collection = get_portfolios_collection()
    
    cursor = portfolios_collection.find({}).sort("portfolio_name", 1)
    portfolios = await cursor.to_list(length=None)
    
    return [serialize_portfolio(portfolio) for portfolio in portfolios]

@router.get("/{portfolio_name}/positions")
async def get_portfolio_positions(portfolio_name: str):
    """Get current positions for a portfolio with mark-to-market values"""
    trades_collection = get_trades_collection()
    market_data_collection = get_market_data_collection()
    
    # Aggregate trades to get current positions
    pipeline = [
        {"$match": {"portfolio_name": portfolio_name}},
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
                "position_quantity": {"$ne": 0}  # Only positions with non-zero quantity
            }
        }
    ]
    
    cursor = trades_collection.aggregate(pipeline)
    positions = await cursor.to_list(length=None)
    
    # Get current market prices and calculate mark-to-market
    result = []
    for position in positions:
        symbol = position["symbol"]
        
        # Get current market price from real-time market data service
        try:
            price_data = await market_data_service.get_stock_price(symbol)
            current_price = price_data["price"] if price_data else position["average_cost"]
        except Exception as e:
            print(f"Error fetching market price for {symbol}: {e}")
            current_price = position["average_cost"]  # Fallback to cost price
        
        # Calculate mark-to-market values
        market_value = position["position_quantity"] * current_price
        unrealized_pl = market_value - position["net_cost"]
        unrealized_pl_percent = (unrealized_pl / position["net_cost"] * 100) if position["net_cost"] != 0 else 0
        
        # Calculate inception P&L (current value + net proceeds from sales - total cost)
        inception_pl = market_value + position["total_proceeds"] - position["total_cost"]
        
        position_summary = {
            "portfolio_name": portfolio_name,
            "symbol": symbol,
            "instrument_type": position["instrument_type"],
            "position_quantity": position["position_quantity"],
            "average_cost": round(position["average_cost"], 2),
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "total_cost": round(position["total_cost"], 2),
            "net_cost": round(position["net_cost"], 2),
            "unrealized_pl": round(unrealized_pl, 2),
            "unrealized_pl_percent": round(unrealized_pl_percent, 2),
            "inception_pl": round(inception_pl, 2),
            "dtd_pl": 0.0,  # Will be calculated later
            "mtd_pl": 0.0,  # Will be calculated later
            "ytd_pl": 0.0   # Will be calculated later
        }
        
        result.append(position_summary)
    
    return result

@router.get("/{portfolio_name}/performance")
async def get_portfolio_performance(portfolio_name: str):
    """Get portfolio performance metrics including DTD, MTD, YTD P&L"""
    daily_snapshots_collection = get_daily_snapshots_collection()
    
    today = date.today()
    
    # Get latest snapshots for comparison
    pipeline = [
        {"$match": {"portfolio_name": portfolio_name}},
        {"$sort": {"snapshot_date": -1}},
        {
            "$group": {
                "_id": "$symbol",
                "latest_snapshot": {"$first": "$$ROOT"}
            }
        }
    ]
    
    cursor = daily_snapshots_collection.aggregate(pipeline)
    latest_snapshots = await cursor.to_list(length=None)
    
    # For now, return current positions (daily snapshots will be implemented with cron job)
    current_positions = await get_portfolio_positions(portfolio_name)
    
    performance_summary = {
        "portfolio_name": portfolio_name,
        "total_market_value": sum(pos["market_value"] for pos in current_positions),
        "total_cost": sum(pos["total_cost"] for pos in current_positions),
        "total_unrealized_pl": sum(pos["unrealized_pl"] for pos in current_positions),
        "total_inception_pl": sum(pos["inception_pl"] for pos in current_positions),
        "positions": current_positions,
        "as_of_date": today.isoformat()
    }
    
    return performance_summary

@router.post("/{portfolio_name}/market-price/{symbol}")
async def update_market_price(portfolio_name: str, symbol: str, price: float):
    """Update market price for a symbol (manual entry for now)"""
    market_data_collection = get_market_data_collection()
    
    update_data = {
        "symbol": symbol,
        "current_price": price,
        "last_updated": datetime.now()
    }
    
    result = await market_data_collection.update_one(
        {"symbol": symbol},
        {"$set": update_data},
        upsert=True
    )
    
    return {
        "message": f"Market price updated for {symbol}",
        "symbol": symbol,
        "price": price,
        "updated_at": update_data["last_updated"].isoformat()
    }

@router.get("/{portfolio_name}/performance-realtime")
async def get_portfolio_performance_realtime(portfolio_name: str):
    """Get portfolio performance with real-time market data"""
    try:
        trades_collection = get_trades_collection()
        
        # Get all trades for this portfolio
        cursor = trades_collection.find({"portfolio_name": portfolio_name})
        trades = []
        async for trade in cursor:
            trades.append(trade)
        
        if not trades:
            return {
                "portfolio_name": portfolio_name,
                "positions": [],
                "total_value": 0,
                "total_cost": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        # Group trades by symbol
        positions = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in positions:
                positions[symbol] = {
                    'symbol': symbol,
                    'instrument_type': trade['instrument_type'],
                    'quantity': 0,
                    'total_cost': 0,
                    'trades': []
                }
            
            quantity = trade['quantity']
            cost = quantity * trade['executed_price'] + trade['brokerage']
            
            if trade['trade_type'] == 'BUY':
                positions[symbol]['quantity'] += quantity
                positions[symbol]['total_cost'] += cost
            else:  # SELL
                positions[symbol]['quantity'] -= quantity
                positions[symbol]['total_cost'] -= cost
            
            positions[symbol]['trades'].append(trade)
        
        # Get current market prices for all symbols
        symbols = [pos['symbol'] for pos in positions.values() if pos['quantity'] != 0]
        market_data = {}
        
        if symbols:
            price_data = await market_data_service.get_multiple_prices(symbols)
            market_data = {symbol: data for symbol, data in price_data.items() if data}
        
        # Calculate performance for each position
        portfolio_positions = []
        total_market_value = 0
        total_cost = 0
        
        for symbol, position in positions.items():
            if position['quantity'] == 0:
                continue  # Skip closed positions
            
            market_price = market_data.get(symbol, {}).get('price', 0)
            market_value = position['quantity'] * market_price
            pnl = market_value - position['total_cost']
            pnl_percent = (pnl / position['total_cost'] * 100) if position['total_cost'] != 0 else 0
            
            avg_cost = position['total_cost'] / position['quantity'] if position['quantity'] != 0 else 0
            
            portfolio_positions.append({
                'symbol': symbol,
                'instrument_type': position['instrument_type'],
                'quantity': position['quantity'],
                'average_cost': round(avg_cost, 2),
                'total_cost': round(position['total_cost'], 2),
                'market_price': market_price,
                'market_value': round(market_value, 2),
                'unrealized_pnl': round(pnl, 2),
                'unrealized_pnl_percent': round(pnl_percent, 2),
                'price_source': market_data.get(symbol, {}).get('source', 'N/A'),
                'price_change': market_data.get(symbol, {}).get('change', 0),
                'price_change_percent': market_data.get(symbol, {}).get('change_percent', '0.00')
            })
            
            total_market_value += market_value
            total_cost += position['total_cost']
        
        total_pnl = total_market_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost != 0 else 0
        
        return {
            "portfolio_name": portfolio_name,
            "positions": portfolio_positions,
            "total_market_value": round(total_market_value, 2),
            "total_cost": round(total_cost, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "total_unrealized_pnl_percent": round(total_pnl_percent, 2),
            "last_updated": datetime.now().isoformat(),
            "market_data_sources": list(set([pos.get('price_source', 'N/A') for pos in portfolio_positions]))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating performance: {str(e)}")


