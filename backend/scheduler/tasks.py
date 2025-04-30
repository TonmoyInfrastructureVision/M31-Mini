import logging
import traceback
from typing import Dict, Any, Optional, List, Union
import asyncio
import json
from datetime import datetime, timedelta
import time
import os
import sys
import psutil

from celery import Task, group, chain, chord
from celery.exceptions import MaxRetriesExceededError, Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .celery_app import app
from config.settings import settings
from agent_core import db, agent as agent_module
from memory import memory_manager
from config.logging_config import get_logger
from tools import initialize_tools

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._async_call(*args, **kwargs))
        
    async def _async_call(self, *args, **kwargs):
        # Call the task's run method with the args/kwargs
        return await self.run(*args, **kwargs)


@app.task(name="initialize_system")
def initialize_system():
    logger.info("Initializing system")
    
    async def _init():
        try:
            # Initialize memory stores
            await memory_manager.initialize()
            
            # Initialize tools
            initialize_tools()
            
            logger.info("System initialization complete")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error initializing system: {str(e)}")
            return {"success": False, "error": str(e)}
    
    return asyncio.run(_init())


@app.task(name="run_agent_task")
def run_agent_task(agent_data: Dict[str, Any], goal: str):
    logger.info(f"Running task for agent {agent_data.get('id', 'unknown')}: {goal}")
    
    async def _run():
        try:
            # Create or load agent
            agent = await agent_module.Agent.from_dict(agent_data)
            
            # Run the task
            result = await agent.run_task(goal)
            
            return result
        except Exception as e:
            logger.error(f"Error running agent task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_data.get("id"),
                "goal": goal
            }
    
    return asyncio.run(_run())


@app.task(name="cancel_agent_task")
def cancel_agent_task(agent_id: str):
    logger.info(f"Cancelling task for agent {agent_id}")
    
    async def _cancel():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state or not agent_state.get("agent_info"):
                return {"success": False, "error": "Agent not found or no state available"}
            
            # Create agent from state
            agent = await agent_module.Agent.from_dict(agent_state["agent_info"])
            
            # Cancel the task
            cancelled = await agent.cancel_task()
            
            return {"success": cancelled, "agent_id": agent_id}
        except Exception as e:
            logger.error(f"Error cancelling agent task: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_cancel())


@app.task(name="get_agent_status")
def get_agent_status(agent_id: str):
    logger.info(f"Getting status for agent {agent_id}")
    
    async def _get_status():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state:
                return {"success": False, "error": "Agent not found or no state available"}
            
            return {
                "success": True,
                "agent_id": agent_id,
                "status": agent_state.get("status", "unknown"),
                "current_task": agent_state.get("current_task"),
                "updated_at": agent_state.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_get_status())


@app.task(name="get_agent_task_history")
def get_agent_task_history(agent_id: str, limit: int = 10):
    logger.info(f"Getting task history for agent {agent_id}")
    
    async def _get_history():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state or not agent_state.get("agent_info"):
                return {"success": False, "error": "Agent not found or no state available"}
            
            # Create agent from state
            agent = await agent_module.Agent.from_dict(agent_state["agent_info"])
            
            # Get task history
            history = await agent.get_task_history(limit=limit)
            
            return {"success": True, "agent_id": agent_id, "history": history}
        except Exception as e:
            logger.error(f"Error getting agent task history: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_get_history())


@app.task(name="delete_agent")
def delete_agent(agent_id: str):
    logger.info(f"Deleting agent {agent_id}")
    
    async def _delete():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state or not agent_state.get("agent_info"):
                return {"success": False, "error": "Agent not found or no state available"}
            
            # Create agent from state
            agent = await agent_module.Agent.from_dict(agent_state["agent_info"])
            
            # Delete the agent
            success = await agent.delete()
            
            return {"success": success, "agent_id": agent_id}
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_delete())


@app.task(name="scheduler.tasks.execute_agent_task", bind=True, base=AsyncTask)
async def execute_agent_task(self, agent_id: str, task_id: str) -> Dict[str, Any]:
    logger.info(f"Starting execution of task {task_id} for agent {agent_id}")
    
    try:
        # Initialize database if needed
        db.initialize()
        
        # Initialize memory manager
        await memory_manager.initialize()
        
        # Get task data
        task_data = db.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
            
        # Get agent data
        agent_data = db.get_agent(agent_id)
        if not agent_data:
            raise ValueError(f"Agent {agent_id} not found")
            
        if agent_data["status"] == "busy":
            logger.warning(f"Agent {agent_id} is busy, rescheduling task {task_id}")
            raise self.retry(countdown=60, max_retries=10)
            
        # Update agent status
        db.update_agent(agent_id, {"status": "busy"})
        
        # Update task status
        db.update_task(task_id, {
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        })
        
        # Create agent instance
        agent = agent_module.Agent(
            id=agent_id,
            name=agent_data["name"],
            model=agent_data["model"],
            workspace_dir=agent_data["workspace_dir"],
            config=agent_data.get("config", {}),
            max_iterations=agent_data.get("max_iterations", settings.agent.max_iterations),
            temperature=agent_data.get("temperature", settings.agent.default_temperature)
        )
        
        # Initialize agent
        await agent.initialize()
        
        # Execute the task
        goal = task_data["goal"]
        logger.info(f"Agent {agent_id} executing task: {goal}")
        
        # Initial planning
        plan = await agent.plan_task(goal)
        
        # Update task with plan
        db.update_task(task_id, {"plan": plan})
        
        # Execute plan
        max_iterations = agent_data.get("max_iterations", settings.agent.max_iterations)
        results = await agent.execute_plan(
            plan=plan,
            task_id=task_id,
            max_iterations=max_iterations
        )
        
        # Reflect on execution
        reflection = await agent.reflect_on_task(goal, plan, results)
        
        # Update task with results
        db.update_task(task_id, {
            "status": "completed",
            "results": results,
            "reflection": reflection,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Add task results to memory
        await memory_manager.add_task_memory(
            agent_id=agent_id,
            task_id=task_id,
            memory_type="task_results",
            data={
                "goal": goal,
                "plan": plan,
                "results": results,
                "reflection": reflection
            },
            metadata={
                "task_id": task_id,
                "success": True,
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        
        # Update agent status
        db.update_agent(agent_id, {"status": "idle"})
        
        logger.info(f"Completed task {task_id} for agent {agent_id}")
        
        return {
            "agent_id": agent_id,
            "task_id": task_id,
            "status": "completed",
            "results": results,
            "reflection": reflection
        }
        
    except (MaxRetriesExceededError, Retry) as e:
        # Let Celery handle the retry
        raise
        
    except Exception as e:
        logger.error(f"Error executing task {task_id} for agent {agent_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update task with error
        try:
            db.update_task(task_id, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })
            
            # Add error to memory
            await memory_manager.add_task_memory(
                agent_id=agent_id,
                task_id=task_id,
                memory_type="task_error",
                data={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                metadata={
                    "task_id": task_id,
                    "success": False,
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
            
            # Update agent status
            db.update_agent(agent_id, {"status": "idle"})
        except Exception as update_error:
            logger.error(f"Error updating task status: {str(update_error)}")
        
        return {
            "agent_id": agent_id,
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }
        
    finally:
        # Close resources
        await memory_manager.close()


@app.task(name="scheduler.tasks.schedule_task", bind=True, base=AsyncTask)
async def schedule_task(self, agent_id: str, goal: str, scheduled_for: Optional[str] = None, 
                       priority: int = 1, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    logger.info(f"Scheduling task for agent {agent_id}: {goal}")
    
    try:
        # Initialize database if needed
        db.initialize()
        
        # Create task
        task_data = {
            "agent_id": agent_id,
            "goal": goal,
            "status": "pending",
            "priority": priority,
            "meta_data": metadata or {}
        }
        
        if scheduled_for:
            task_data["scheduled_for"] = scheduled_for
            logger.info(f"Task scheduled for {scheduled_for}")
        
        task = db.create_task(task_data)
        
        # If not scheduled for later, execute immediately
        if not scheduled_for:
            execute_agent_task.delay(agent_id, task["id"])
            logger.info(f"Task {task['id']} queued for immediate execution")
        else:
            logger.info(f"Task {task['id']} scheduled for later execution")
        
        return {
            "agent_id": agent_id,
            "task_id": task["id"],
            "status": task["status"],
            "scheduled_for": scheduled_for
        }
        
    except Exception as e:
        logger.error(f"Error scheduling task for agent {agent_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e)
        }


@app.task(name="scheduler.tasks.cancel_task", bind=True, base=AsyncTask)
async def cancel_task(self, task_id: str) -> Dict[str, Any]:
    logger.info(f"Cancelling task {task_id}")
    
    try:
        # Initialize database if needed
        db.initialize()
        
        # Get task data
        task_data = db.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
            
        # Only cancel if not already completed or failed
        if task_data["status"] in ["completed", "failed"]:
            logger.warning(f"Task {task_id} already in state {task_data['status']}, cannot cancel")
            return {
                "task_id": task_id,
                "status": task_data["status"],
                "cancelled": False
            }
            
        # Update task status
        db.update_task(task_id, {
            "status": "cancelled",
            "completed_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Cancelled task {task_id}")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "cancelled": True
        }
        
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "cancelled": False
        }


@app.task(name="scheduler.tasks.process_scheduled_tasks", bind=True, base=AsyncTask)
async def process_scheduled_tasks(self) -> Dict[str, Any]:
    logger.debug("Processing scheduled tasks")
    
    try:
        # Initialize database if needed
        db.initialize()
        
        # Get current time
        now = datetime.utcnow().isoformat()
        
        # Get all pending tasks
        with db.get_db_session() as session:
            # Query all pending tasks with a scheduled_for time that has passed
            query = session.query(db.Task).filter(
                db.Task.status == "pending",
                db.Task.scheduled_for.isnot(None),
                db.Task.scheduled_for <= now
            )
            
            tasks = query.all()
            
        if not tasks:
            logger.debug("No scheduled tasks to process")
            return {"processed": 0}
            
        logger.info(f"Found {len(tasks)} scheduled tasks to process")
        
        # Process each task
        processed = 0
        for task in tasks:
            try:
                # Update task to remove scheduled_for
                db.update_task(task.id, {"scheduled_for": None})
                
                # Execute task
                execute_agent_task.delay(task.agent_id, task.id)
                
                processed += 1
            except Exception as e:
                logger.error(f"Error processing scheduled task {task.id}: {str(e)}")
                
        logger.info(f"Processed {processed} scheduled tasks")
        
        return {"processed": processed}
        
    except Exception as e:
        logger.error(f"Error processing scheduled tasks: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {"processed": 0, "error": str(e)}


@app.task(name="scheduler.tasks.retry_failed_tasks", bind=True, base=AsyncTask)
async def retry_failed_tasks(self) -> Dict[str, Any]:
    logger.debug("Retrying failed tasks")
    
    try:
        # Initialize database if needed
        db.initialize()
        
        # Get all failed tasks from the last 24 hours
        retry_since = datetime.utcnow() - timedelta(hours=24)
        
        with db.get_db_session() as session:
            # Query all failed tasks
            query = session.query(db.Task).filter(
                db.Task.status == "failed",
                db.Task.updated_at >= retry_since.isoformat()
            )
            
            tasks = query.all()
            
        if not tasks:
            logger.debug("No failed tasks to retry")
            return {"retried": 0}
            
        logger.info(f"Found {len(tasks)} failed tasks to retry")
        
        # Process each task
        retried = 0
        for task in tasks:
            try:
                # Check if task has already been retried too many times
                metadata = task.meta_data or {}
                retry_count = metadata.get("retry_count", 0)
                
                if retry_count >= settings.scheduler.max_retries:
                    logger.warning(f"Task {task.id} has reached max retries ({retry_count})")
                    continue
                
                # Update retry count in metadata
                metadata["retry_count"] = retry_count + 1
                metadata["last_retry"] = datetime.utcnow().isoformat()
                
                # Update task
                db.update_task(task.id, {
                    "status": "pending",
                    "error": None,
                    "meta_data": metadata
                })
                
                # Execute task
                execute_agent_task.delay(task.agent_id, task.id)
                
                retried += 1
            except Exception as e:
                logger.error(f"Error retrying failed task {task.id}: {str(e)}")
                
        logger.info(f"Retried {retried} failed tasks")
        
        return {"retried": retried}
        
    except Exception as e:
        logger.error(f"Error retrying failed tasks: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {"retried": 0, "error": str(e)}


@app.task(name="scheduler.tasks.cleanup_old_completed_tasks", bind=True, base=AsyncTask)
async def cleanup_old_completed_tasks(self, days: int = 7) -> Dict[str, Any]:
    logger.debug(f"Cleaning up completed tasks older than {days} days")
    
    try:
        # Initialize database if needed
        db.initialize()
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with db.get_db_session() as session:
            # Query completed and cancelled tasks older than cutoff date
            query = session.query(db.Task).filter(
                db.Task.status.in_(["completed", "cancelled"]),
                db.Task.completed_at.isnot(None),
                db.Task.completed_at <= cutoff_date.isoformat()
            )
            
            # Archive tasks before deletion if needed
            tasks = query.all()
            
            if not tasks:
                logger.debug("No old tasks to clean up")
                return {"deleted": 0}
                
            logger.info(f"Found {len(tasks)} old tasks to clean up")
            
            # Archive tasks if configured
            if settings.db.auto_backup:
                try:
                    backup_dir = os.path.join(settings.db.backup_dir, "task_archives")
                    os.makedirs(backup_dir, exist_ok=True)
                    
                    backup_file = os.path.join(backup_dir, f"tasks_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
                    
                    # Create archive data
                    archive_data = {
                        "tasks": [
                            {
                                "id": task.id,
                                "agent_id": task.agent_id,
                                "goal": task.goal,
                                "status": task.status,
                                "created_at": task.created_at.isoformat() if task.created_at else None,
                                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                                "plan": task.plan,
                                "results": task.results,
                                "reflection": task.reflection,
                                "error": task.error
                            }
                            for task in tasks
                        ]
                    }
                    
                    # Save archive
                    with open(backup_file, "w") as f:
                        json.dump(archive_data, f, indent=2)
                        
                    logger.info(f"Archived {len(tasks)} tasks to {backup_file}")
                except Exception as e:
                    logger.error(f"Error archiving tasks: {str(e)}")
            
            # Delete tasks
            deleted = 0
            for task in tasks:
                try:
                    session.delete(task)
                    deleted += 1
                except Exception as e:
                    logger.error(f"Error deleting task {task.id}: {str(e)}")
                    
            session.commit()
            
            logger.info(f"Deleted {deleted} old tasks")
            
            return {"deleted": deleted}
        
    except Exception as e:
        logger.error(f"Error cleaning up old tasks: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {"deleted": 0, "error": str(e)}


@app.task(name="scheduler.tasks.health_check", bind=True)
def health_check(self) -> Dict[str, Any]:
    logger.debug("Performing health check")
    
    try:
        # Check system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check database connection
        db_status = "ok"
        try:
            db.initialize()
        except Exception as e:
            db_status = f"error: {str(e)}"
            
        # Check Redis connection
        redis_status = "ok"
        try:
            redis_conn = app.backend.client
            redis_conn.ping()
        except Exception as e:
            redis_status = f"error: {str(e)}"
            
        # Prepare health data
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "cpu_percent": cpu_percent
            },
            "services": {
                "database": db_status,
                "redis": redis_status
            },
            "process": {
                "pid": os.getpid(),
                "python_version": sys.version,
                "uptime_seconds": time.time() - psutil.Process(os.getpid()).create_time()
            }
        }
        
        # Log warning if resources are running low
        if memory.percent > 90:
            logger.warning(f"Memory usage is high: {memory.percent}%")
            
        if disk.percent > 90:
            logger.warning(f"Disk usage is high: {disk.percent}%")
            
        if cpu_percent > 90:
            logger.warning(f"CPU usage is high: {cpu_percent}%")
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }


@app.task(name="scheduler.tasks.bulk_schedule_tasks", bind=True, base=AsyncTask)
async def bulk_schedule_tasks(self, agent_id: str, goals: List[str], 
                            priority: int = 1, sequential: bool = False) -> Dict[str, Any]:
    logger.info(f"Bulk scheduling {len(goals)} tasks for agent {agent_id}")
    
    results = []
    try:
        # Initialize database if needed
        db.initialize()
        
        # Get agent data
        agent_data = db.get_agent(agent_id)
        if not agent_data:
            raise ValueError(f"Agent {agent_id} not found")
            
        # Create all tasks
        task_ids = []
        for i, goal in enumerate(goals):
            task_data = {
                "agent_id": agent_id,
                "goal": goal,
                "status": "pending",
                "priority": priority
            }
            
            # If sequential, schedule with delay
            if sequential and i > 0:
                # Schedule 5 minutes after the previous task
                scheduled_time = datetime.utcnow() + timedelta(minutes=5 * i)
                task_data["scheduled_for"] = scheduled_time.isoformat()
                task_data["meta_data"] = {"bulk_index": i, "sequential": True}
            
            task = db.create_task(task_data)
            task_ids.append(task["id"])
            
            results.append({
                "task_id": task["id"],
                "goal": goal,
                "status": task["status"]
            })
            
            # If not sequential, execute immediately
            if not sequential:
                execute_agent_task.delay(agent_id, task["id"])
            elif i == 0:
                # Execute first task in sequential mode
                execute_agent_task.delay(agent_id, task["id"])
        
        logger.info(f"Scheduled {len(task_ids)} tasks for agent {agent_id}")
        
        return {
            "agent_id": agent_id,
            "tasks": results,
            "sequential": sequential
        }
        
    except Exception as e:
        logger.error(f"Error bulk scheduling tasks for agent {agent_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": str(e),
            "tasks": results
        } 