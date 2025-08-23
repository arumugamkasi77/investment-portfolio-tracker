from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date, timedelta
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

async def calculate_dtd_mtd_ytd_pl_for_symbol(portfolio_name: str, symbol: str, current_inception_pl: float) -> tuple[float, float, float]:
    """
    Calculate DTD, MTD, YTD P&L for a specific symbol using enhanced snapshots logic.
    Returns (dtd_pl, mtd_pl, ytd_pl) tuple.
    Uses NYSE calendar-aware logic for month-end and year-end calculations.
    """
    daily_snapshots_collection = get_daily_snapshots_collection()
    
    today = date.today()
    
    # Get previous trading day (yesterday or last working day)
    from services.enhanced_snapshots import EnhancedSnapshotsService
    enhanced_service = EnhancedSnapshotsService()
    previous_trading_day = enhanced_service._get_previous_trading_day(today)
    last_month_end = enhanced_service._get_last_trading_day_of_previous_month(today)
    last_year_end = enhanced_service._get_last_trading_day_of_previous_year(today)
    
    # Convert to datetime for MongoDB queries
    previous_trading_day_datetime = datetime.combine(previous_trading_day, datetime.min.time())
    last_month_end_datetime = datetime.combine(last_month_end, datetime.min.time())
    last_year_end_datetime = datetime.combine(last_year_end, datetime.min.time())
    
    print(f"🔍 DEBUG: Calculating P&L for {symbol} in {portfolio_name}")
    print(f"  Today: {today}")
    print(f"  Previous trading day: {previous_trading_day}")
    print(f"  Last month end: {last_month_end}")
    print(f"  Last year end: {last_year_end}")
    
    # Get stored snapshots for comparison
    previous_trading_day_snapshot = await daily_snapshots_collection.find_one({
        "portfolio_name": portfolio_name,
        "symbol": symbol,
        "snapshot_date": previous_trading_day_datetime
    })
    
    last_month_end_snapshot = await daily_snapshots_collection.find_one({
        "portfolio_name": portfolio_name,
        "symbol": symbol,
        "snapshot_date": last_month_end_datetime
    })
    
    last_year_end_snapshot = await daily_snapshots_collection.find_one({
        "portfolio_name": portfolio_name,
        "symbol": symbol,
        "snapshot_date": last_year_end_datetime
    })
    
    # Fallback: if no snapshot for exact dates, find most recent from previous periods
    if not last_month_end_snapshot:
        last_month_end_snapshot = await daily_snapshots_collection.find_one(
            {
                "portfolio_name": portfolio_name,
                "symbol": symbol,
                "snapshot_date": {"$lte": last_month_end_datetime}
            },
            sort=[("snapshot_date", -1)]  # Get most recent in previous month
        )
    
    if not last_year_end_snapshot:
        last_year_end_snapshot = await daily_snapshots_collection.find_one(
            {
                "portfolio_name": portfolio_name,
                "symbol": symbol,
                "snapshot_date": {"$lte": last_year_end_datetime}
            },
            sort=[("snapshot_date", -1)]  # Get most recent in previous year
        )
    
    # Calculate DTD, MTD, YTD P&L
    # DTD = Today's P&L - Previous trading day's P&L
    dtd_pl = current_inception_pl - (previous_trading_day_snapshot["inception_pl"] if previous_trading_day_snapshot else 0.0)
    
    # MTD = Today's P&L - Last month-end P&L
    mtd_pl = current_inception_pl - (last_month_end_snapshot["inception_pl"] if last_month_end_snapshot else 0.0)
    
    # YTD = Today's P&L - Last year-end P&L
    ytd_pl = current_inception_pl - (last_year_end_snapshot["inception_pl"] if last_year_end_snapshot else 0.0)
    
    print(f"  Previous trading day snapshot: {'Found' if previous_trading_day_snapshot else 'Not found'}")
    print(f"  Last month-end snapshot: {'Found' if last_month_end_snapshot else 'Not found'}")
    print(f"  Last year-end snapshot: {'Found' if last_year_end_snapshot else 'Not found'}")
    print(f"  DTD PL: ${dtd_pl:,.2f}, MTD PL: ${mtd_pl:,.2f}, YTD PL: ${ytd_pl:,.2f}")
    
    return dtd_pl, mtd_pl, ytd_pl

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
async def get_portfolio_positions(portfolio_name: str, force_fresh: bool = Query(False, description="Force fresh market data")):
    """Get current positions for a portfolio with mark-to-market values"""
    trades_collection = get_trades_collection()
    market_data_collection = get_market_data_collection()
    
    # Python-based FIFO calculation for portfolio positions
    async def calculate_fifo_position(symbol: str, instrument_type: str):
        """Calculate position using FIFO method for accurate average cost"""
        
        # Get all trades for this symbol, sorted by trade_date
        trades = await trades_collection.find({
            "portfolio_name": portfolio_name,
            "symbol": symbol
        }).sort("trade_date", 1).to_list(length=None)
        
        if not trades:
            return None
        
        # Debug: Show all trades for NVDA
        if symbol == "NVDA":
            print(f"🔍 DEBUG: Found {len(trades)} trades for NVDA:")
            for i, trade in enumerate(trades):
                print(f"  Trade {i+1}: {trade['trade_type']} {trade['quantity']} shares at ${trade['executed_price']} on {trade['trade_date']}")
            print()
        
        # FIFO tracking
        buy_lots = []  # List of (quantity, price_per_share, brokerage_per_share)
        total_quantity_bought = 0
        total_quantity_sold = 0
        total_cost_bought = 0
        total_proceeds_sold = 0
        realized_pl = 0
        
        # Process trades chronologically
        for trade in trades:
            if trade["trade_type"] == "BUY":
                # Add to buy lots
                quantity = trade["quantity"]
                price_per_share = trade["executed_price"]
                brokerage_per_share = trade.get("brokerage", 0) / quantity if quantity > 0 else 0
                
                buy_lots.append((quantity, price_per_share, brokerage_per_share))
                total_quantity_bought += quantity
                total_cost_bought += (quantity * price_per_share) + trade.get("brokerage", 0)
                
                # Debug for NVDA
                if symbol == "NVDA":
                    print(f"  🔍 BUY: {quantity} shares at ${price_per_share} + ${trade.get('brokerage', 0)} brokerage")
                    print(f"     Total cost for this trade: ${(quantity * price_per_share) + trade.get('brokerage', 0):,.2f}")
                
            elif trade["trade_type"] == "SELL":
                # Apply FIFO to sell
                remaining_to_sell = trade["quantity"]
                sell_proceeds = (trade["quantity"] * trade["executed_price"]) - trade.get("brokerage", 0)
                total_proceeds_sold += sell_proceeds
                total_quantity_sold += trade["quantity"]
                
                # Debug for NVDA
                if symbol == "NVDA":
                    print(f"  🔍 SELL: {trade['quantity']} shares at ${trade['executed_price']} - ${trade.get('brokerage', 0)} brokerage")
                    print(f"     Total proceeds for this trade: ${sell_proceeds:,.2f}")
                
                # Calculate realized P&L using FIFO
                while remaining_to_sell > 0 and buy_lots:
                    lot_quantity, lot_price, lot_brokerage = buy_lots[0]
                    
                    if lot_quantity <= remaining_to_sell:
                        # Sell entire lot
                        shares_sold_from_lot = lot_quantity
                        cost_basis = lot_quantity * (lot_price + lot_brokerage)
                        realized_pl += (shares_sold_from_lot * trade["executed_price"]) - cost_basis
                        
                        remaining_to_sell -= lot_quantity
                        buy_lots.pop(0)  # Remove consumed lot
                        
                    else:
                        # Sell partial lot
                        shares_sold_from_lot = remaining_to_sell
                        cost_basis = shares_sold_from_lot * (lot_price + lot_brokerage)
                        realized_pl += (shares_sold_from_lot * trade["executed_price"]) - cost_basis
                        
                        # Update remaining lot
                        remaining_quantity = lot_quantity - shares_sold_from_lot
                        buy_lots[0] = (remaining_quantity, lot_price, lot_brokerage)
                        remaining_to_sell = 0
        
        # Calculate remaining position
        position_quantity = total_quantity_bought - total_quantity_sold
        
        if position_quantity <= 0:
            return None
        
        # Calculate remaining cost basis using FIFO
        remaining_cost_basis = sum(quantity * (price + brokerage) for quantity, price, brokerage in buy_lots)
        
        # Calculate weighted average cost
        average_cost = remaining_cost_basis / position_quantity if position_quantity > 0 else 0
        
        # Debug logging for NVDA
        if symbol == "NVDA":
            print(f"🔍 DEBUG: NVDA FIFO Calculation:")
            print(f"  - Total bought: {total_quantity_bought} shares, ${total_cost_bought:,.2f}")
            print(f"  - Total sold: {total_quantity_sold} shares, ${total_proceeds_sold:,.2f}")
            print(f"  - Remaining position: {position_quantity} shares")
            print(f"  - Buy lots: {buy_lots}")
            print(f"  - Remaining cost basis: ${remaining_cost_basis:,.2f}")
            print(f"  - Average cost: ${average_cost:,.2f}")
        
        return {
            "symbol": symbol,
            "instrument_type": instrument_type,
            "position_quantity": position_quantity,
            "total_cost": remaining_cost_basis,
            "total_proceeds": total_proceeds_sold,
            "net_cost": remaining_cost_basis,
            "total_quantity_bought": total_quantity_bought,
            "total_quantity_sold": total_quantity_sold,
            "total_cost_bought": total_cost_bought,
            "total_proceeds_sold": total_proceeds_sold,
            "average_cost": average_cost,
            "realized_pl": realized_pl
        }
    
    # Get unique symbols from trades
    symbols = await trades_collection.distinct("symbol", {"portfolio_name": portfolio_name})
    
    # Calculate FIFO positions for each symbol
    positions = []
    for symbol in symbols:
        # Get instrument type from first trade
        first_trade = await trades_collection.find_one({"portfolio_name": portfolio_name, "symbol": symbol})
        if first_trade:
            instrument_type = first_trade.get("instrument_type", "STOCK")
            position = await calculate_fifo_position(symbol, instrument_type)
            if position:
                positions.append(position)
    
    # Get current market prices and calculate mark-to-market
    result = []
    
    # CRITICAL FIX: Single batch fetch for all symbols to eliminate race conditions
    if force_fresh:
        print(f"🔧 DEBUG: Starting single batch fetch for all {len(positions)} symbols")
        symbols_to_fetch = [pos["symbol"] for pos in positions]
        print(f"🔧 DEBUG: Symbols to fetch: {symbols_to_fetch}")
        
        # Single batch call - no individual symbol calls
        all_prices = await market_data_service.get_multiple_prices(symbols_to_fetch)
        print(f"🔧 DEBUG: Batch fetch completed. Prices received: {list(all_prices.keys())}")
        
        # Verify all prices were fetched
        for symbol in symbols_to_fetch:
            if symbol in all_prices and all_prices[symbol]:
                print(f"✅ DEBUG: {symbol} = ${all_prices[symbol]['price']} ({all_prices[symbol].get('price_type', 'unknown')})")
            else:
                print(f"❌ DEBUG: {symbol} = NO PRICE DATA")
    
    for position in positions:
        symbol = position["symbol"]
        
        # Get current market price with extended hours priority
        try:
            print(f"🔍 DEBUG: Processing position {symbol} (row {len(result)})")
            
            if force_fresh:
                # Use the pre-fetched price data from single batch call
                price_data = all_prices.get(symbol)
                if price_data:
                    print(f"🔍 DEBUG: Using batch-fetched price for {symbol}: ${price_data['price']}")
                else:
                    print(f"⚠️ DEBUG: No batch price for {symbol}, using fallback")
                    price_data = None
            else:
                # Use cached data for normal requests
                print(f"🔍 DEBUG: Using cached data for {symbol}")
                price_data = await market_data_service.get_stock_price(symbol)
            
            current_price = price_data["price"] if price_data else position["average_cost"]
            price_type = price_data.get("price_type", "unknown") if price_data else "unknown"
            print(f"🔍 DEBUG: Final price for {symbol}: ${current_price} ({price_type})")
            
        except Exception as e:
            print(f"Error fetching market price for {symbol}: {e}")
            current_price = position["average_cost"]  # Fallback to cost price
        
        # Calculate mark-to-market values
        market_value = position["position_quantity"] * current_price
        unrealized_pl = market_value - position["net_cost"]
        unrealized_pl_percent = (unrealized_pl / position["net_cost"] * 100) if position["net_cost"] != 0 else 0
        
        # Calculate inception P&L (current value + net proceeds from sales - total cost)
        inception_pl = market_value + position["total_proceeds"] - position["total_cost"]
        
        # Calculate DTD, MTD, YTD P&L using enhanced snapshots logic
        dtd_pl, mtd_pl, ytd_pl = await calculate_dtd_mtd_ytd_pl_for_symbol(
            portfolio_name, symbol, inception_pl
        )
        
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
            "dtd_pl": round(dtd_pl, 2),
            "mtd_pl": round(mtd_pl, 2),
            "ytd_pl": round(ytd_pl, 2)
        }
        
        # CRITICAL: Log the result object before adding to array
        print(f"🔍 DEBUG: Adding to result array: {symbol} = {position_summary['current_price']}")
        
        result.append(position_summary)
    
    # CRITICAL: Log the final result array to verify data integrity
    print(f"🔍 DEBUG: Final result array:")
    for i, pos in enumerate(result):
        print(f"  [{i}] {pos['symbol']}: price=${pos['current_price']}, market_value=${pos['market_value']}")
    
    return result

@router.get("/{portfolio_name}/performance")
async def get_portfolio_performance(portfolio_name: str, force_fresh: bool = False):
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
    current_positions = await get_portfolio_positions(portfolio_name, force_fresh)
    
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

@router.get("/{portfolio_name}/positions-with-analysis")
async def get_portfolio_positions_with_analysis(portfolio_name: str, force_fresh: bool = False):
    """
    Get portfolio positions AND DTD/MTD/YTD analysis in a single call.
    This eliminates the need for multiple individual market data fetches.
    """
    try:
        # Get positions with batch market data fetch
        positions = await get_portfolio_positions(portfolio_name, force_fresh)
        
        # Calculate overall portfolio DTD/MTD/YTD P&L
        total_dtd_pl = sum(pos.get("dtd_pl", 0) for pos in positions)
        total_mtd_pl = sum(pos.get("mtd_pl", 0) for pos in positions)
        total_ytd_pl = sum(pos.get("ytd_pl", 0) for pos in positions)
        
        # Calculate portfolio totals
        total_market_value = sum(pos["market_value"] for pos in positions)
        total_cost = sum(pos["total_cost"] for pos in positions)
        total_unrealized_pl = sum(pos["unrealized_pl"] for pos in positions)
        total_inception_pl = sum(pos["inception_pl"] for pos in positions)
        
        return {
            "portfolio_name": portfolio_name,
            "positions": positions,
            "portfolio_totals": {
                "total_market_value": round(total_market_value, 2),
                "total_cost": round(total_cost, 2),
                "total_unrealized_pl": round(total_unrealized_pl, 2),
                "total_inception_pl": round(total_inception_pl, 2),
                "total_dtd_pl": round(total_dtd_pl, 2),
                "total_mtd_pl": round(total_mtd_pl, 2),
                "total_ytd_pl": round(total_ytd_pl, 2)
            },
            "analysis_date": date.today().isoformat(),
            "message": "Single call returning both positions and analysis"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio with analysis: {str(e)}")

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


