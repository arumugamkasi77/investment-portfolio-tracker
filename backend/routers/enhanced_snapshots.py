"""
Enhanced Snapshots Router
Provides improved daily snapshot functionality and DTD/MTD/YTD P&L tracking.
This router works alongside existing functionality without modifying it.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, date, timedelta
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_snapshots import enhanced_snapshots_service
from models import DailySnapshotModel

router = APIRouter(prefix="/enhanced-snapshots", tags=["enhanced-snapshots"])

def serialize_snapshot(snapshot) -> dict:
    """Convert MongoDB document to dict with string _id"""
    if snapshot:
        snapshot["_id"] = str(snapshot["_id"])
        if "snapshot_date" in snapshot:
            snapshot["snapshot_date"] = snapshot["snapshot_date"].isoformat()
        if "created_at" in snapshot:
            snapshot["created_at"] = snapshot["created_at"].isoformat()
    return snapshot

@router.post("/create")
async def create_enhanced_snapshot(
    portfolio_name: Optional[str] = None, 
    snapshot_date: Optional[str] = None
):
    """
    Create enhanced daily snapshot(s) with proper P&L calculations.
    This fixes the existing snapshot creation logic.
    """
    if snapshot_date:
        try:
            snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        snapshot_date = date.today()
    
    try:
        snapshots_created = await enhanced_snapshots_service.create_simple_daily_snapshot(
            portfolio_name, snapshot_date
        )
        
        return {
            "message": f"Created {snapshots_created} enhanced snapshots",
            "portfolio_name": portfolio_name or "all portfolios",
            "snapshot_date": snapshot_date.isoformat(),
            "snapshots_created": snapshots_created,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating snapshots: {str(e)}")

@router.post("/create-all")
async def create_all_enhanced_snapshots(background_tasks: BackgroundTasks):
    """
    Create enhanced snapshots for all portfolios in the background.
    This is useful for daily batch processing.
    """
    try:
        # Run in background to avoid timeout
        background_tasks.add_task(
            enhanced_snapshots_service.create_enhanced_daily_snapshot
        )
        
        return {
            "message": "Enhanced snapshot creation started in background",
            "status": "success",
            "note": "Check logs for progress updates"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting snapshot creation: {str(e)}")

@router.get("/dtd-mtd-ytd/{portfolio_name}")
async def get_dtd_mtd_ytd_analysis(
    portfolio_name: str, 
    symbol: Optional[str] = None
):
    """
    Get DTD, MTD, YTD P&L analysis for a portfolio.
    This provides the meaningful P&L tracking you requested.
    """
    try:
        analysis = await enhanced_snapshots_service.calculate_dtd_mtd_ytd_pl_simple(
            portfolio_name, symbol
        )
        
        return {
            "data": analysis,
            "message": f"DTD/MTD/YTD analysis for {portfolio_name}",
            "status": "success",
            "portfolio_name": portfolio_name,
            "analysis_date": date.today().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating P&L analysis: {str(e)}")

@router.get("/pnl-history/{portfolio_name}")
async def get_portfolio_pnl_history(
    portfolio_name: str,
    symbol: Optional[str] = None,
    days: int = 30
):
    """
    Get P&L history for a portfolio over a specified number of days.
    This helps track performance trends.
    """
    try:
        if days > 365:
            days = 365  # Limit to 1 year to prevent performance issues
        
        history = await enhanced_snapshots_service.get_portfolio_pnl_history(
            portfolio_name, symbol, days
        )
        
        return {
            "data": history,
            "message": f"P&L history for {portfolio_name} over {days} days",
            "status": "success",
            "portfolio_name": portfolio_name,
            "days": days,
            "history_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving P&L history: {str(e)}")

@router.get("/positions/{portfolio_name}")
async def get_enhanced_portfolio_positions(portfolio_name: str):
    """
    Get enhanced portfolio positions with proper P&L calculations.
    This uses the same logic as the working portfolios router.
    """
    try:
        positions = await enhanced_snapshots_service.get_portfolio_positions_simple(
            portfolio_name
        )
        
        return {
            "data": positions,
            "message": f"Enhanced positions for {portfolio_name}",
            "status": "success",
            "portfolio_name": portfolio_name,
            "position_count": len(positions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving positions: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_snapshots(days_to_keep: int = 365):
    """
    Clean up old snapshots to manage database size.
    Keeps snapshots for the specified number of days.
    """
    try:
        if days_to_keep < 30:
            days_to_keep = 30  # Minimum 30 days
        
        deleted_count = await enhanced_snapshots_service.cleanup_old_snapshots(days_to_keep)
        
        return {
            "message": f"Cleaned up {deleted_count} old snapshots",
            "status": "success",
            "days_to_keep": days_to_keep,
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up snapshots: {str(e)}")

@router.get("/status")
async def get_snapshots_status():
    """
    Get status of daily snapshots system.
    Shows when last snapshots were created and system health.
    """
    try:
        from database import get_daily_snapshots_collection
        
        daily_snapshots_collection = get_daily_snapshots_collection()
        
        # Get latest snapshot date
        latest_snapshot = await daily_snapshots_collection.find_one(
            {}, 
            sort=[("snapshot_date", -1)]
        )
        
        # Get total snapshot count
        total_snapshots = await daily_snapshots_collection.count_documents({})
        
        # Get snapshots by date
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        today_count = await daily_snapshots_collection.count_documents({
            "snapshot_date": today
        })
        
        yesterday_count = await daily_snapshots_collection.count_documents({
            "snapshot_date": yesterday
        })
        
        status = {
            "system_status": "healthy",
            "total_snapshots": total_snapshots,
            "latest_snapshot_date": latest_snapshot["snapshot_date"].isoformat() if latest_snapshot else None,
            "today_snapshots": today_count,
            "yesterday_snapshots": yesterday_count,
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "data": status,
            "message": "Daily snapshots system status",
            "status": "success"
        }
    except Exception as e:
        return {
            "data": {
                "system_status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            },
            "message": "Error retrieving system status",
            "status": "error"
        }

@router.post("/test-calculation")
async def test_pnl_calculation(portfolio_name: str):
    """
    Test P&L calculation logic for a portfolio.
    This helps debug and verify calculations.
    """
    try:
        # Test position calculation
        positions = await enhanced_snapshots_service.get_portfolio_positions_simple(
            portfolio_name
        )
        
        # Test DTD/MTD/YTD calculation
        analysis = await enhanced_snapshots_service.calculate_dtd_mtd_ytd_pl_simple(portfolio_name)
        
        test_results = {
            "portfolio_name": portfolio_name,
            "test_date": date.today().isoformat(),
            "positions_calculated": len(positions),
            "analysis_calculated": len(analysis),
            "sample_position": positions[0] if positions else None,
            "sample_analysis": analysis[0] if analysis else None
        }
        
        return {
            "data": test_results,
            "message": f"P&L calculation test for {portfolio_name}",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing P&L calculation: {str(e)}")
