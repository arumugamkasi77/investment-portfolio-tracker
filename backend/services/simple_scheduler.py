"""
Simple Scheduler Service
Provides manual scheduling capabilities for daily snapshots without auto-running.
This ensures your existing working system remains untouched.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
import logging
from dataclasses import dataclass

# Import the enhanced service (don't modify existing code)
from services.enhanced_snapshots import enhanced_snapshots_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    task_id: str
    task_type: str
    portfolio_name: Optional[str]
    scheduled_time: datetime
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SimpleScheduler:
    """
    Simple scheduler that can be triggered manually.
    No automatic execution to avoid breaking your working system.
    """
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_counter = 0
        self.is_running = False
        logger.info("Simple Scheduler initialized - manual mode only")
    
    def generate_task_id(self) -> str:
        """Generate unique task ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def schedule_daily_snapshots(
        self, 
        portfolio_name: Optional[str] = None,
        delay_minutes: int = 0
    ) -> str:
        """
        Schedule daily snapshots to run after a specified delay.
        This is manual scheduling - no automatic execution.
        """
        task_id = self.generate_task_id()
        
        # Calculate scheduled time
        if delay_minutes > 0:
            scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        else:
            scheduled_time = datetime.now()
        
        # Create scheduled task
        task = ScheduledTask(
            task_id=task_id,
            task_type="daily_snapshots",
            portfolio_name=portfolio_name,
            scheduled_time=scheduled_time,
            status="pending",
            created_at=datetime.now()
        )
        
        self.scheduled_tasks[task_id] = task
        logger.info(f"Scheduled daily snapshots task {task_id} for {scheduled_time}")
        
        return task_id
    
    async def run_scheduled_task(self, task_id: str) -> Dict:
        """
        Manually run a scheduled task.
        This gives you control over when tasks execute.
        """
        if task_id not in self.scheduled_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.scheduled_tasks[task_id]
        
        if task.status == "completed":
            return {
                "task_id": task_id,
                "status": "already_completed",
                "message": "Task was already completed"
            }
        
        if task.status == "running":
            return {
                "task_id": task_id,
                "status": "already_running",
                "message": "Task is already running"
            }
        
        try:
            # Mark task as running
            task.status = "running"
            logger.info(f"Starting task {task_id}")
            
            # Execute the task
            if task.task_type == "daily_snapshots":
                snapshots_created = await enhanced_snapshots_service.create_simple_daily_snapshot(
                    task.portfolio_name
                )
                
                # Mark task as completed
                task.status = "completed"
                task.completed_at = datetime.now()
                
                logger.info(f"Task {task_id} completed successfully: {snapshots_created} snapshots created")
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "snapshots_created": snapshots_created,
                    "message": f"Successfully created {snapshots_created} snapshots"
                }
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            # Mark task as failed
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"Task {task_id} failed: {e}")
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "message": "Task execution failed"
            }
    
    async def run_all_pending_tasks(self) -> List[Dict]:
        """
        Manually run all pending tasks.
        This gives you control over batch execution.
        """
        pending_tasks = [
            task_id for task_id, task in self.scheduled_tasks.items()
            if task.status == "pending"
        ]
        
        results = []
        for task_id in pending_tasks:
            result = await self.run_scheduled_task(task_id)
            results.append(result)
        
        logger.info(f"Executed {len(pending_tasks)} pending tasks")
        return results
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        if task_id not in self.scheduled_tasks:
            return None
        
        task = self.scheduled_tasks[task_id]
        
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "portfolio_name": task.portfolio_name,
            "scheduled_time": task.scheduled_time.isoformat(),
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
    
    def get_all_tasks(self) -> List[Dict]:
        """Get status of all tasks"""
        return [
            self.get_task_status(task_id)
            for task_id in self.scheduled_tasks.keys()
        ]
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get list of pending tasks"""
        return [
            self.get_task_status(task_id)
            for task_id, task in self.scheduled_tasks.items()
            if task.status == "pending"
        ]
    
    def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Clear completed tasks older than specified hours.
        This helps manage memory usage.
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        tasks_to_remove = []
        for task_id, task in self.scheduled_tasks.items():
            if (task.status in ["completed", "failed"] and 
                task.completed_at and 
                task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.scheduled_tasks[task_id]
        
        logger.info(f"Cleared {len(tasks_to_remove)} old completed tasks")
        return len(tasks_to_remove)
    
    async def simulate_daily_schedule(self, portfolio_name: Optional[str] = None) -> str:
        """
        Simulate what would happen in a daily schedule.
        This helps you understand the scheduling without auto-execution.
        """
        task_id = self.generate_task_id()
        
        # Create a simulation task
        task = ScheduledTask(
            task_id=task_id,
            task_type="daily_snapshots_simulation",
            portfolio_name=portfolio_name,
            scheduled_time=datetime.now(),
            status="pending",
            created_at=datetime.now()
        )
        
        self.scheduled_tasks[task_id] = task
        
        logger.info(f"Created simulation task {task_id} for daily snapshots")
        
        return task_id
    
    def get_scheduler_status(self) -> Dict:
        """Get overall scheduler status"""
        total_tasks = len(self.scheduled_tasks)
        pending_tasks = len([t for t in self.scheduled_tasks.values() if t.status == "pending"])
        running_tasks = len([t for t in self.scheduled_tasks.values() if t.status == "running"])
        completed_tasks = len([t for t in self.scheduled_tasks.values() if t.status == "completed"])
        failed_tasks = len([t for t in self.scheduled_tasks.values() if t.status == "failed"])
        
        return {
            "scheduler_status": "manual_mode",
            "auto_execution": False,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "last_updated": datetime.now().isoformat()
        }

# Global instance
simple_scheduler = SimpleScheduler()
