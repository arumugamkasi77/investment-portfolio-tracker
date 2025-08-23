"""
Enhanced Daily Snapshots Service - Simplified Version
Uses existing working portfolio logic to store daily inception P&L values.
No complex MongoDB aggregation - just simple daily storage.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import logging
import pandas as pd

# Import existing working code (don't modify)
from database import (
    get_trades_collection,
    get_portfolios_collection,
    get_market_data_collection,
    get_daily_snapshots_collection
)

# Import existing models (don't modify)
from models import DailySnapshotModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSnapshotsService:
    """
    Simplified enhanced service that uses existing working logic.
    Just stores daily inception P&L values for DTD/MTD/YTD tracking.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def get_portfolio_positions_simple(self, portfolio_name: str) -> List[Dict]:
        """
        Get portfolio positions using existing working logic.
        This is a simplified version that just gets the data we need.
        """
        try:
            # Import the existing working portfolios router logic
            from routers.portfolios import get_portfolio_positions
            
            # Use the existing working function
            positions = await get_portfolio_positions(portfolio_name)
            return positions
            
        except Exception as e:
            logger.error(f"Error getting portfolio positions: {e}")
            return []

    async def get_portfolio_positions_for_date(self, portfolio_name: str, snapshot_date: date) -> List[Dict]:
        """
        Get portfolio positions and calculate P&L for a specific historical date.
        Uses market data from that date, not today's data.
        """
        try:
            trades_collection = get_trades_collection()
            market_data_collection = get_market_data_collection()
            
            # Aggregate trades to get positions as of the snapshot date
            pipeline = [
                {"$match": {"portfolio_name": portfolio_name}},
                {"$match": {"trade_date": {"$lte": datetime.combine(snapshot_date, datetime.max.time())}}},
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
                }
            ]
            
            cursor = trades_collection.aggregate(pipeline)
            positions = await cursor.to_list(length=None)
            
            logger.info(f"Found {len(positions)} raw positions from database for {portfolio_name}")
            
            result = []
            
            for position in positions:
                symbol = position["_id"]["symbol"]
                instrument_type = position["_id"]["instrument_type"]
                
                # Calculate net position
                net_quantity = position["total_quantity_bought"] - position["total_quantity_sold"]
                
                logger.info(f"Processing {symbol}: bought={position['total_quantity_bought']}, sold={position['total_quantity_sold']}, net={net_quantity}")
                
                if net_quantity <= 0:
                    logger.info(f"Skipping {symbol} - net quantity <= 0")
                    continue  # Skip closed positions
                
                # Calculate average cost
                average_cost = position["total_cost_bought"] / position["total_quantity_bought"] if position["total_quantity_bought"] > 0 else 0
                
                # Get historical market price for the snapshot date
                logger.info(f"Fetching historical price for {symbol} on {snapshot_date}")
                try:
                    # Try to fetch historical market data using yfinance
                    historical_price = await self.fetch_historical_market_data(symbol, snapshot_date)
                    logger.info(f"Historical price result for {symbol}: {historical_price}")
                    
                    if historical_price > 0:
                        current_price = historical_price
                        logger.info(f"Using yfinance historical price for {symbol} on {snapshot_date}: ${historical_price}")
                    else:
                        # Fallback: use average cost (this means P&L will be 0 for that date)
                        current_price = average_cost
                        logger.warning(f"No historical market data for {symbol} on {snapshot_date}, using average cost")
                except Exception as e:
                    logger.error(f"Error fetching historical market data for {symbol}: {e}")
                    current_price = average_cost
                
                # Calculate values
                market_value = net_quantity * current_price
                net_cost = position["total_cost_bought"] - position["total_proceeds_sold"]
                
                # Calculate P&L using the simple formula: quantity × (current_price - average_cost)
                # This gives us the unrealized P&L as of the snapshot date
                unrealized_pl = net_quantity * (current_price - average_cost)
                total_pl = position["realized_pl"] + unrealized_pl
                
                position_summary = {
                    "symbol": symbol,
                    "instrument_type": instrument_type,
                    "position_quantity": net_quantity,
                    "average_cost": round(average_cost, 2),
                    "current_price": round(current_price, 2),
                    "market_value": round(market_value, 2),
                    "total_cost": round(position["total_cost_bought"], 2),
                    "net_cost": round(net_cost, 2),
                    "unrealized_pl": round(unrealized_pl, 2),
                    "realized_pl": round(position["realized_pl"], 2),
                    "inception_pl": round(total_pl, 2)
                }
                
                result.append(position_summary)
            
            logger.info(f"Returning {len(result)} processed positions for {portfolio_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting portfolio positions for date {snapshot_date}: {e}")
            return []

    def _get_previous_trading_day(self, target_date: date) -> date:
        """
        Get the previous trading day (NYSE calendar-aware).
        Skips weekends and major US market holidays.
        """
        from datetime import timedelta
        
        print(f"🔧 DEBUG: _get_previous_trading_day called with target_date: {target_date}")
        
        # Start with the day BEFORE the target date
        current_date = target_date - timedelta(days=1)
        print(f"🔧 DEBUG: After subtracting 1 day: {current_date}")
        
        # Simple weekend skipping (Saturday=5, Sunday=6)
        while current_date.weekday() >= 5:  # Saturday or Sunday
            current_date -= timedelta(days=1)
            print(f"🔧 DEBUG: Skipped weekend, now: {current_date}")
        
        # Skip major US market holidays (simplified list)
        # In production, you'd want to use a proper holiday calendar library
        holidays_2025 = [
            date(2025, 1, 1),   # New Year's Day
            date(2025, 1, 20),  # Martin Luther King Jr. Day
            date(2025, 2, 17),  # Presidents' Day
            date(2025, 4, 18),  # Good Friday
            date(2025, 5, 26),  # Memorial Day
            date(2025, 6, 19),  # Juneteenth
            date(2025, 7, 4),   # Independence Day
            date(2025, 9, 1),   # Labor Day
            date(2025, 11, 27), # Thanksgiving Day
            date(2025, 12, 25), # Christmas Day
        ]
        
        while current_date in holidays_2025:
            current_date -= timedelta(days=1)
            print(f"🔧 DEBUG: Skipped holiday, now: {current_date}")
            # Also skip weekends when going back
            while current_date.weekday() >= 5:
                current_date -= timedelta(days=1)
                print(f"🔧 DEBUG: Skipped weekend after holiday, now: {current_date}")
        
        print(f"🔧 DEBUG: Final result: {current_date}")
        return current_date

    def _get_last_trading_day_of_previous_month(self, target_date: date) -> date:
        """
        Get the last trading day of the previous month (NYSE calendar-aware).
        Skips weekends and major US market holidays.
        """
        from datetime import timedelta
        
        # Go to first day of current month, then subtract 1 day to get last day of previous month
        first_day_current_month = target_date.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        current_date = last_day_previous_month
        
        # Find the last trading day (skip weekends and holidays)
        while current_date.weekday() >= 5:  # Saturday or Sunday
            current_date -= timedelta(days=1)
        
        # Skip major US market holidays (simplified list)
        holidays_2025 = [
            date(2025, 1, 1),   # New Year's Day
            date(2025, 1, 20),  # Martin Luther King Jr. Day
            date(2025, 2, 17),  # Presidents' Day
            date(2025, 4, 18),  # Good Friday
            date(2025, 5, 26),  # Memorial Day
            date(2025, 6, 19),  # Juneteenth
            date(2025, 7, 4),   # Independence Day
            date(2025, 9, 1),   # Labor Day
            date(2025, 11, 27), # Thanksgiving Day
            date(2025, 12, 25), # Christmas Day
        ]
        
        while current_date in holidays_2025:
            current_date -= timedelta(days=1)
            # Also skip weekends when going back
            while current_date.weekday() >= 5:
                current_date -= timedelta(days=1)
        
        return current_date

    def _get_last_trading_day_of_previous_year(self, target_date: date) -> date:
        """
        Get the last trading day of the previous year (NYSE calendar-aware).
        Skips weekends and major US market holidays.
        """
        from datetime import timedelta
        
        # Go to December 31st of previous year
        last_day_previous_year = target_date.replace(year=target_date.year-1, month=12, day=31)
        current_date = last_day_previous_year
        
        # Find the last trading day (skip weekends and holidays)
        while current_date.weekday() >= 5:  # Saturday or Sunday
            current_date -= timedelta(days=1)
        
        # Skip major US market holidays (simplified list)
        holidays_2024 = [
            date(2024, 1, 1),   # New Year's Day
            date(2024, 1, 15),  # Martin Luther King Jr. Day
            date(2024, 2, 19),  # Presidents' Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 6, 19),  # Juneteenth
            date(2024, 7, 4),   # Independence Day
            date(2024, 9, 2),   # Labor Day
            date(2024, 11, 28), # Thanksgiving Day
            date(2024, 12, 25), # Christmas Day
        ]
        
        while current_date in holidays_2024:
            current_date -= timedelta(days=1)
            # Also skip weekends when going back
            while current_date.weekday() >= 5:
                current_date -= timedelta(days=1)
        
        return current_date

    def _get_closest_historical_price(self, historical_prices: List[Dict], target_date: date) -> float:
        """
        Get the closest historical price to the target date.
        This is a helper method for finding historical market data.
        """
        try:
            # Convert target_date to datetime for comparison
            target_datetime = datetime.combine(target_date, datetime.min.time())
            
            # Find the closest date in historical prices
            closest_price = None
            min_diff = float('inf')
            
            for price_data in historical_prices:
                if "date" in price_data and "price" in price_data:
                    try:
                        # Handle timezone-aware dates from yfinance by converting to timezone-naive
                        if isinstance(price_data["date"], str):
                            if price_data["date"].endswith('Z'):
                                # UTC timezone, remove Z and parse
                                price_date = datetime.fromisoformat(price_data["date"].replace('Z', ''))
                            elif '+' in price_data["date"] or price_data["date"].endswith('UTC'):
                                # Has timezone info, remove it and parse
                                price_date_str = price_data["date"].split('+')[0].split('UTC')[0].strip()
                                price_date = datetime.fromisoformat(price_date_str)
                            else:
                                # No timezone info, parse directly
                                price_date = datetime.fromisoformat(price_data["date"])
                        else:
                            # If it's already a datetime object, convert to timezone-naive
                            price_date = price_data["date"].replace(tzinfo=None) if hasattr(price_data["date"], 'replace') else price_data["date"]
                        
                        diff = abs((price_date - target_datetime).total_seconds())
                        
                        if diff < min_diff:
                            min_diff = diff
                            closest_price = price_data["price"]
                    except (ValueError, TypeError):
                        continue
            
            return closest_price if closest_price is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error getting closest historical price: {e}")
            return 0.0

    async def fetch_historical_market_data(self, symbol: str, target_date: date) -> float:
        """
        Fetch historical market data for a specific symbol and date using the same approach
        as the existing market data service, but for historical dates.
        """
        try:
            import yfinance as yf
            import asyncio
            
            # Handle CASH_USD specially - always return 1.0
            if symbol == "CASH_USD":
                return 1.0
            
            # Convert date to string format for yfinance
            date_str = target_date.strftime("%Y-%m-%d")
            
            # Use the same approach as market_data_service: run yfinance in thread pool
            loop = asyncio.get_event_loop()
            
            def get_historical_data():
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Get historical data for a small range around the target date
                    start_date = target_date - timedelta(days=5)
                    end_date = target_date + timedelta(days=5)
                    
                    hist_data = ticker.history(start=start_date, end=end_date)
                    
                    if hist_data.empty:
                        return None
                    
                    # Find the closest available date to the target date
                    # Convert target_date to timezone-naive datetime for comparison
                    target_datetime = pd.Timestamp(target_date).tz_localize(None)
                    closest_date = None
                    min_difference = float('inf')
                    
                    for date_idx in hist_data.index:
                        # Convert yfinance date to timezone-naive for comparison
                        date_idx_naive = date_idx.tz_localize(None) if date_idx.tz is not None else date_idx
                        difference = abs((date_idx_naive - target_datetime).days)
                        if difference < min_difference:
                            min_difference = difference
                            closest_date = date_idx
                    
                    if closest_date is not None:
                        closing_price = hist_data.loc[closest_date, 'Close']
                        print(f"🔍 DEBUG: Historical price for {symbol} on {target_date}: closest available date {closest_date.date()} = ${closing_price}")
                        return float(closing_price)
                    else:
                        return None
                    
                except Exception as e:
                    print(f"Error in historical data fetch for {symbol}: {e}")
                    return None
            
            # Run in thread pool to avoid blocking (same as market_data_service)
            historical_price = await loop.run_in_executor(None, get_historical_data)
            
            if historical_price:
                logger.info(f"Found historical price for {symbol} on {target_date}: ${historical_price}")
                return historical_price
            else:
                logger.warning(f"No historical data found for {symbol} around {date_str}")
                return 0.0
            
        except ImportError:
            logger.error("yfinance not available for historical data fetching")
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching historical market data for {symbol} on {target_date}: {e}")
            return 0.0
    
    async def create_simple_daily_snapshot(self, portfolio_name: str = None, snapshot_date: date = None) -> int:
        """
        Create simple daily snapshots by storing inception P&L values.
        Uses existing working logic, just stores the results.
        """
        if snapshot_date is None:
            snapshot_date = date.today()
        
        portfolios_collection = get_portfolios_collection()
        daily_snapshots_collection = get_daily_snapshots_collection()
        
        # Get portfolios to snapshot
        if portfolio_name:
            portfolios = [{"portfolio_name": portfolio_name}]
        else:
            cursor = portfolios_collection.find({}, {"portfolio_name": 1})
            portfolios = await cursor.to_list(length=None)
        
        snapshots_created = 0
        
        for portfolio in portfolios:
            portfolio_name = portfolio["portfolio_name"]
            logger.info(f"Creating snapshot for portfolio: {portfolio_name}")
            
            try:
                # Get positions for the specific date (historical or current)
                if snapshot_date == date.today():
                    # Use current positions for today
                    positions = await self.get_portfolio_positions_simple(portfolio_name)
                else:
                    # Use historical positions for past dates
                    positions = await self.get_portfolio_positions_for_date(portfolio_name, snapshot_date)
                
                for position in positions:
                    symbol = position["symbol"]
                    
                    # Check if snapshot already exists for this date
                    snapshot_datetime = datetime.combine(snapshot_date, datetime.min.time())
                    existing_snapshot = await daily_snapshots_collection.find_one({
                        "portfolio_name": portfolio_name,
                        "symbol": symbol,
                        "snapshot_date": snapshot_datetime
                    })
                    
                    if not existing_snapshot:
                        # Store snapshot with inception P&L for the specific date
                        snapshot_data = {
                            "portfolio_name": portfolio_name,
                            "symbol": symbol,
                            "snapshot_date": datetime.combine(snapshot_date, datetime.min.time()),
                            "position_quantity": position["position_quantity"],
                            "average_cost": position["average_cost"],
                            "current_price": position["current_price"],
                            "market_value": position["market_value"],
                            "inception_pl": position["inception_pl"],
                            "created_at": datetime.now()
                        }
                        
                        await daily_snapshots_collection.insert_one(snapshot_data)
                        snapshots_created += 1
                        logger.info(f"Created snapshot for {symbol} in {portfolio_name} on {snapshot_date}: P&L ${position['inception_pl']}")
                    else:
                        logger.info(f"Snapshot already exists for {symbol} in {portfolio_name} on {snapshot_date}")
                        
            except Exception as e:
                logger.error(f"Error creating snapshot for {portfolio_name}: {e}")
                continue
        
        logger.info(f"Created {snapshots_created} simple snapshots for {snapshot_date}")
        return snapshots_created
    
    async def delete_snapshots_by_date(self, snapshot_date: date) -> int:
        """
        Delete all snapshots for a specific date.
        Returns the number of snapshots deleted.
        """
        try:
            daily_snapshots_collection = get_daily_snapshots_collection()
            
            # Convert date to datetime for MongoDB query
            snapshot_datetime = datetime.combine(snapshot_date, datetime.min.time())
            
            # Delete all snapshots for this date
            result = await daily_snapshots_collection.delete_many({
                "snapshot_date": snapshot_datetime
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} snapshots for {snapshot_date}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting snapshots for {snapshot_date}: {e}")
            raise
    
    async def calculate_dtd_mtd_ytd_pl_simple(self, portfolio_name: str, symbol: Optional[str] = None) -> List[Dict]:
        """
        Calculate DTD, MTD, YTD P&L using stored snapshots.
        DTD = Today's P&L - Last working day's P&L
        MTD = Today's P&L - Month start P&L
        YTD = Today's P&L - Year start P&L
        """
        daily_snapshots_collection = get_daily_snapshots_collection()
        
        today = date.today()
        
        # Get NYSE calendar-aware dates
        previous_trading_day = self._get_previous_trading_day(today)
        last_trading_day_of_previous_month = self._get_last_trading_day_of_previous_month(today)
        last_trading_day_of_previous_year = self._get_last_trading_day_of_previous_year(today)
        
        # Convert to datetime for MongoDB queries (timezone-naive to match stored data)
        today_datetime = datetime.combine(today, datetime.min.time())
        previous_trading_day_datetime = datetime.combine(previous_trading_day, datetime.min.time())
        last_trading_day_of_previous_month_datetime = datetime.combine(last_trading_day_of_previous_month, datetime.min.time())
        last_trading_day_of_previous_year_datetime = datetime.combine(last_trading_day_of_previous_year, datetime.min.time())
        
        print(f"DEBUG: Today: {today} -> {today_datetime}")
        print(f"DEBUG: Previous trading day: {previous_trading_day} -> {previous_trading_day_datetime}")
        print(f"DEBUG: Last month end: {last_trading_day_of_previous_month} -> {last_trading_day_of_previous_month_datetime}")
        print(f"DEBUG: Last year end: {last_trading_day_of_previous_year} -> {last_trading_day_of_previous_year_datetime}")
        
        # Get current positions using existing logic (today's data)
        current_positions = await self.get_portfolio_positions_simple(portfolio_name)
        
        result = []
        portfolio_totals = {
            "dtd_pl": 0.0,
            "mtd_pl": 0.0,
            "ytd_pl": 0.0,
            "current_total_pl": 0.0,
            "previous_trading_day_total_pl": 0.0,
            "last_trading_day_of_previous_month_total_pl": 0.0,
            "last_trading_day_of_previous_year_total_pl": 0.0
        }
        
        for position in current_positions:
            if symbol and position["symbol"] != symbol:
                continue
                
            current_symbol = position["symbol"]
            current_inception_pl = position["inception_pl"]
            
            # Find the previous trading day snapshot (NYSE calendar-aware)
            previous_trading_day_snapshot = await daily_snapshots_collection.find_one(
                {
                    "portfolio_name": portfolio_name,
                    "symbol": current_symbol,
                    "snapshot_date": previous_trading_day_datetime
                }
            )
            
            # Fallback: if no snapshot for exact previous trading day, find most recent before today
            if not previous_trading_day_snapshot:
                print(f"DEBUG: No exact match for {current_symbol} on {previous_trading_day_datetime}, using fallback")
                last_working_day_snapshot = await daily_snapshots_collection.find_one(
                    {
                        "portfolio_name": portfolio_name,
                        "symbol": current_symbol,
                        "snapshot_date": {"$lt": today_datetime}
                    },
                    sort=[("snapshot_date", -1)]  # Get most recent
                )
                if last_working_day_snapshot:
                    print(f"DEBUG: Found fallback snapshot for {current_symbol} on {last_working_day_snapshot['snapshot_date']}")
                else:
                    print(f"DEBUG: No fallback snapshot found for {current_symbol}")
            else:
                print(f"DEBUG: Found exact snapshot for {current_symbol} on {previous_trading_day_datetime}")
                last_working_day_snapshot = previous_trading_day_snapshot
            
            # Find month-end snapshot (last trading day of previous month)
            month_end_snapshot = await daily_snapshots_collection.find_one({
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "snapshot_date": last_trading_day_of_previous_month_datetime
            })
            
            # Fallback: if no snapshot for exact month-end, find most recent from previous month
            if not month_end_snapshot:
                month_end_snapshot = await daily_snapshots_collection.find_one(
                    {
                        "portfolio_name": portfolio_name,
                        "symbol": current_symbol,
                        "snapshot_date": {"$lte": last_trading_day_of_previous_month_datetime}
                    },
                    sort=[("snapshot_date", -1)]  # Get most recent in previous month
                )
            
            # Find year-end snapshot (last trading day of previous year)
            year_end_snapshot = await daily_snapshots_collection.find_one({
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "snapshot_date": last_trading_day_of_previous_year_datetime
            })
            
            # Fallback: if no snapshot for exact year-end, find most recent from previous year
            if not year_end_snapshot:
                year_end_snapshot = await daily_snapshots_collection.find_one(
                    {
                        "portfolio_name": portfolio_name,
                        "symbol": current_symbol,
                        "snapshot_date": {"$lte": last_trading_day_of_previous_year_datetime}
                    },
                    sort=[("snapshot_date", -1)]  # Get most recent in previous year
                )
            
            # Calculate DTD, MTD, YTD P&L
            # DTD = Today's P&L - Previous trading day's P&L
            dtd_pl = current_inception_pl - (last_working_day_snapshot["inception_pl"] if last_working_day_snapshot else 0.0)
            
            # MTD = Today's P&L - Last month-end P&L  
            mtd_pl = current_inception_pl - (month_end_snapshot["inception_pl"] if month_end_snapshot else 0.0)
            
            # YTD = Today's P&L - Last year-end P&L
            ytd_pl = current_inception_pl - (year_end_snapshot["inception_pl"] if year_end_snapshot else 0.0)
            
            # Accumulate portfolio totals
            portfolio_totals["dtd_pl"] += dtd_pl
            portfolio_totals["mtd_pl"] += mtd_pl
            portfolio_totals["ytd_pl"] += ytd_pl
            portfolio_totals["current_total_pl"] += current_inception_pl
            
            if last_working_day_snapshot:
                portfolio_totals["previous_trading_day_total_pl"] += last_working_day_snapshot["inception_pl"]
            if month_end_snapshot:
                portfolio_totals["last_trading_day_of_previous_month_total_pl"] += month_end_snapshot["inception_pl"]
            if year_end_snapshot:
                portfolio_totals["last_trading_day_of_previous_year_total_pl"] += year_end_snapshot["inception_pl"]
            
            position_analysis = {
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "current_inception_pl": round(current_inception_pl, 2),
                "dtd_pl": round(dtd_pl, 2),
                "mtd_pl": round(mtd_pl, 2),
                "ytd_pl": round(ytd_pl, 2),
                "analysis_date": today.isoformat(),
                "previous_trading_day": previous_trading_day.isoformat(),
                "last_trading_day_of_previous_month": last_trading_day_of_previous_month.isoformat(),
                "last_trading_day_of_previous_year": last_trading_day_of_previous_year.isoformat(),
                "has_previous_trading_day_snapshot": previous_trading_day_snapshot is not None,
                "has_last_working_day_snapshot": last_working_day_snapshot is not None,
                "last_working_day": last_working_day_snapshot["snapshot_date"].date().isoformat() if last_working_day_snapshot else None,
                "has_month_end_snapshot": month_end_snapshot is not None,
                "has_year_end_snapshot": year_end_snapshot is not None
            }
            
            result.append(position_analysis)
        
        # Add portfolio summary to the result
        portfolio_summary = {
            "portfolio_name": portfolio_name,
            "type": "portfolio_summary",
            "current_total_pl": round(portfolio_totals["current_total_pl"], 2),
            "dtd_pl": round(portfolio_totals["dtd_pl"], 2),
            "mtd_pl": round(portfolio_totals["mtd_pl"], 2),
            "ytd_pl": round(portfolio_totals["ytd_pl"], 2),
            "previous_trading_day_total_pl": round(portfolio_totals["previous_trading_day_total_pl"], 2),
            "last_trading_day_of_previous_month_total_pl": round(portfolio_totals["last_trading_day_of_previous_month_total_pl"], 2),
            "last_trading_day_of_previous_year_total_pl": round(portfolio_totals["last_trading_day_of_previous_year_total_pl"], 2),
            "analysis_date": today.isoformat()
        }
        
        result.append(portfolio_summary)
        return result
    
    async def get_snapshot_status(self, portfolio_name: str) -> Dict:
        """
        Get status of snapshots for a portfolio.
        Shows what dates have snapshots and what's missing.
        """
        daily_snapshots_collection = get_daily_snapshots_collection()
        
        # Get all snapshots for this portfolio
        cursor = daily_snapshots_collection.find(
            {"portfolio_name": portfolio_name}
        ).sort("snapshot_date", -1)
        
        snapshots = await cursor.to_list(length=None)
        
        if not snapshots:
            return {
                "portfolio_name": portfolio_name,
                "has_snapshots": False,
                "latest_snapshot": None,
                "snapshot_count": 0,
                "message": "No snapshots found for this portfolio"
            }
        
        # Get latest snapshot
        latest_snapshot = snapshots[0]
        latest_date = latest_snapshot["snapshot_date"]
        
        # Check if we have today's snapshot
        today = date.today()
        has_today_snapshot = any(
            s["snapshot_date"] == today for s in snapshots
        )
        
        # Check if we have yesterday's snapshot
        yesterday = today - timedelta(days=1)
        has_yesterday_snapshot = any(
            s["snapshot_date"] == yesterday for s in snapshots
        )
        
        return {
            "portfolio_name": portfolio_name,
            "has_snapshots": True,
            "latest_snapshot": latest_date.isoformat(),
            "snapshot_count": len(snapshots),
            "has_today_snapshot": has_today_snapshot,
            "has_yesterday_snapshot": has_yesterday_snapshot,
            "last_updated": datetime.now().isoformat()
        }
    
    async def cleanup_old_snapshots(self, days_to_keep: int = 365) -> int:
        """
        Clean up old snapshots to manage database size.
        Keeps snapshots for the specified number of days.
        """
        daily_snapshots_collection = get_daily_snapshots_collection()
        
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        result = await daily_snapshots_collection.delete_many({
            "snapshot_date": {"$lt": cutoff_date}
        })
        
        deleted_count = result.deleted_count
        logger.info(f"Cleaned up {deleted_count} old snapshots older than {cutoff_date}")
        
        return deleted_count

# Global instance
enhanced_snapshots_service = EnhancedSnapshotsService()
