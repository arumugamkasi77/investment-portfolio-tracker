"""
Enhanced Daily Snapshots Service - Simplified Version
Uses existing working portfolio logic to store daily inception P&L values.
No complex MongoDB aggregation - just simple daily storage.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import logging

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
                # Get positions using existing working logic
                positions = await self.get_portfolio_positions_simple(portfolio_name)
                
                for position in positions:
                    symbol = position["symbol"]
                    
                    # Check if snapshot already exists for this date
                    existing_snapshot = await daily_snapshots_collection.find_one({
                        "portfolio_name": portfolio_name,
                        "symbol": symbol,
                        "snapshot_date": snapshot_date
                    })
                    
                    if not existing_snapshot:
                        # Store simple snapshot with inception P&L
                        snapshot_data = {
                            "portfolio_name": portfolio_name,
                            "symbol": symbol,
                            "snapshot_date": snapshot_date,
                            "position_quantity": position["position_quantity"],
                            "average_cost": position["average_cost"],
                            "current_price": position["current_price"],
                            "market_value": position["market_value"],
                            "inception_pl": position["inception_pl"],  # This is what we need!
                            "created_at": datetime.now()
                        }
                        
                        await daily_snapshots_collection.insert_one(snapshot_data)
                        snapshots_created += 1
                        logger.info(f"Created snapshot for {symbol} in {portfolio_name}: P&L ${position['inception_pl']}")
                    else:
                        logger.info(f"Snapshot already exists for {symbol} in {portfolio_name} on {snapshot_date}")
                        
            except Exception as e:
                logger.error(f"Error creating snapshot for {portfolio_name}: {e}")
                continue
        
        logger.info(f"Created {snapshots_created} simple snapshots for {snapshot_date}")
        return snapshots_created
    
    async def calculate_dtd_mtd_ytd_pl_simple(self, portfolio_name: str, symbol: Optional[str] = None) -> List[Dict]:
        """
        Calculate DTD, MTD, YTD P&L using stored snapshots.
        Simple calculation: current P&L - stored P&L (or 0 if no snapshot).
        """
        daily_snapshots_collection = get_daily_snapshots_collection()
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        
        # Get current positions using existing logic
        current_positions = await self.get_portfolio_positions_simple(portfolio_name)
        
        result = []
        
        for position in current_positions:
            if symbol and position["symbol"] != symbol:
                continue
                
            current_symbol = position["symbol"]
            current_inception_pl = position["inception_pl"]
            
            # Get stored snapshots for comparison
            yesterday_snapshot = await daily_snapshots_collection.find_one({
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "snapshot_date": yesterday
            })
            
            month_start_snapshot = await daily_snapshots_collection.find_one({
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "snapshot_date": month_start
            })
            
            year_start_snapshot = await daily_snapshots_collection.find_one({
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "snapshot_date": year_start
            })
            
            # Calculate DTD, MTD, YTD P&L
            # If no snapshot exists, use 0 (as per your requirement)
            dtd_pl = current_inception_pl - (yesterday_snapshot["inception_pl"] if yesterday_snapshot else 0.0)
            mtd_pl = current_inception_pl - (month_start_snapshot["inception_pl"] if month_start_snapshot else 0.0)
            ytd_pl = current_inception_pl - (year_start_snapshot["inception_pl"] if year_start_snapshot else 0.0)
            
            position_analysis = {
                "portfolio_name": portfolio_name,
                "symbol": current_symbol,
                "current_inception_pl": round(current_inception_pl, 2),
                "dtd_pl": round(dtd_pl, 2),
                "mtd_pl": round(mtd_pl, 2),
                "ytd_pl": round(ytd_pl, 2),
                "analysis_date": today.isoformat(),
                "has_yesterday_snapshot": yesterday_snapshot is not None,
                "has_month_start_snapshot": month_start_snapshot is not None,
                "has_year_start_snapshot": year_start_snapshot is not None
            }
            
            result.append(position_analysis)
        
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
