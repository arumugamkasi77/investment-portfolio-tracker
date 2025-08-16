"""
Scheduler Router
Provides manual scheduling capabilities for daily snapshots.
This router works alongside existing functionality without modifying it.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.simple_scheduler import simple_scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.post("/schedule-daily-snapshots")
async def schedule_daily_snapshots(
    portfolio_name: Optional[str] = None,
    delay_minutes: int = 0
):
    """
    Schedule daily snapshots to run after a specified delay.
    This is manual scheduling - no automatic execution.
    """
    try:
        task_id = await simple_scheduler.schedule_daily_snapshots(
            portfolio_name, delay_minutes
        )
        
        return {
            "message": "Daily snapshots scheduled successfully",
            "task_id": task_id,
            "portfolio_name": portfolio_name or "all portfolios",
            "delay_minutes": delay_minutes,
            "scheduled_time": (datetime.now() + timedelta(minutes=delay_minutes)).isoformat(),
            "status": "scheduled"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling snapshots: {str(e)}")

@router.post("/run-task/{task_id}")
async def run_scheduled_task(task_id: str):
    """
    Manually run a scheduled task.
    This gives you control over when tasks execute.
    """
    try:
        result = await simple_scheduler.run_scheduled_task(task_id)
        
        return {
            "message": "Task executed successfully",
            "task_id": task_id,
            "result": result,
            "status": "executed"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing task: {str(e)}")

@router.post("/run-all-pending")
async def run_all_pending_tasks(background_tasks: BackgroundTasks):
    """
    Manually run all pending tasks.
    This gives you control over batch execution.
    """
    try:
        # Run in background to avoid timeout
        background_tasks.add_task(simple_scheduler.run_all_pending_tasks)
        
        return {
            "message": "All pending tasks started in background",
            "status": "started",
            "note": "Check task status for progress updates"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting tasks: {str(e)}")

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    try:
        status = simple_scheduler.get_task_status(task_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {
            "data": status,
            "message": f"Task status for {task_id}",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving task status: {str(e)}")

@router.get("/all-tasks")
async def get_all_tasks():
    """Get status of all tasks"""
    try:
        tasks = simple_scheduler.get_all_tasks()
        
        return {
            "data": tasks,
            "message": "All scheduled tasks",
            "status": "success",
            "task_count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tasks: {str(e)}")

@router.get("/pending-tasks")
async def get_pending_tasks():
    """Get list of pending tasks"""
    try:
        tasks = simple_scheduler.get_pending_tasks()
        
        return {
            "data": tasks,
            "message": "Pending tasks",
            "status": "success",
            "pending_count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving pending tasks: {str(e)}")

@router.post("/clear-completed-tasks")
async def clear_completed_tasks(older_than_hours: int = 24):
    """
    Clear completed tasks older than specified hours.
    This helps manage memory usage.
    """
    try:
        if older_than_hours < 1:
            older_than_hours = 1  # Minimum 1 hour
        
        deleted_count = simple_scheduler.clear_completed_tasks(older_than_hours)
        
        return {
            "message": f"Cleared {deleted_count} old completed tasks",
            "status": "success",
            "older_than_hours": older_than_hours,
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing tasks: {str(e)}")

@router.get("/status")
async def get_scheduler_status():
    """Get overall scheduler status"""
    try:
        status = simple_scheduler.get_scheduler_status()
        
        return {
            "data": status,
            "message": "Scheduler system status",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scheduler status: {str(e)}")

@router.post("/simulate-daily-schedule")
async def simulate_daily_schedule(portfolio_name: Optional[str] = None):
    """
    Simulate what would happen in a daily schedule.
    This helps you understand the scheduling without auto-execution.
    """
    try:
        task_id = simple_scheduler.simulate_daily_schedule(portfolio_name)
        
        return {
            "message": "Daily schedule simulation created",
            "task_id": task_id,
            "portfolio_name": portfolio_name or "all portfolios",
            "simulation_type": "daily_snapshots",
            "status": "simulated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating simulation: {str(e)}")

@router.post("/quick-daily-snapshots")
async def quick_daily_snapshots(portfolio_name: Optional[str] = None):
    """
    Quick way to create daily snapshots for today.
    This bypasses scheduling for immediate execution.
    """
    try:
        # Import the enhanced service directly
        from services.enhanced_snapshots import enhanced_snapshots_service
        
        snapshots_created = await enhanced_snapshots_service.create_simple_daily_snapshot(
            portfolio_name, date.today()
        )
        
        return {
            "message": f"Quick daily snapshots created successfully",
            "snapshots_created": snapshots_created,
            "portfolio_name": portfolio_name or "all portfolios",
            "snapshot_date": date.today().isoformat(),
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating quick snapshots: {str(e)}")

@router.get("/help")
async def get_scheduler_help():
    """
    Get help information about the scheduler system.
    This explains how to use the manual scheduling features.
    """
    help_info = {
        "scheduler_type": "Manual Scheduler",
        "auto_execution": False,
        "description": "This scheduler requires manual triggering - no automatic execution",
        "usage_steps": [
            "1. Schedule daily snapshots using POST /scheduler/schedule-daily-snapshots",
            "2. Check task status using GET /scheduler/task-status/{task_id}",
            "3. Manually run tasks using POST /scheduler/run-task/{task_id}",
            "4. Run all pending tasks using POST /scheduler/run-all-pending",
            "5. Monitor system status using GET /scheduler/status"
        ],
        "endpoints": {
            "schedule": "POST /scheduler/schedule-daily-snapshots",
            "run_task": "POST /scheduler/run-task/{task_id}",
            "run_all": "POST /scheduler/run-all-pending",
            "task_status": "GET /scheduler/task-status/{task_id}",
            "all_tasks": "GET /scheduler/all-tasks",
            "pending_tasks": "GET /scheduler/pending-tasks",
            "scheduler_status": "GET /scheduler/status",
            "quick_snapshots": "POST /scheduler/quick-daily-snapshots"
        },
        "notes": [
            "No automatic execution to preserve system stability",
            "All tasks must be manually triggered",
            "Background execution available for long-running tasks",
            "Task cleanup available to manage memory usage"
        ]
    }
    
    return {
        "data": help_info,
        "message": "Scheduler system help information",
        "status": "success"
    }
