import logging
import json
from typing import Dict, List, Optional, Any, Union
import time

import redis
from redis.exceptions import RedisError

from config.settings import settings

logger = logging.getLogger(__name__)


class ShortTermMemory:
    def __init__(self):
        self.client = None
        self.initialized = False
        
    async def initialize(self) -> None:
        logger.info(f"Initializing Redis connection with settings: {settings.redis}")
        
        try:
            connection_kwargs = {
                "host": settings.redis.host,
                "port": settings.redis.port,
                "db": settings.redis.db,
                "decode_responses": True,
            }
            
            if settings.redis.password:
                connection_kwargs["password"] = settings.redis.password
                
            if settings.redis.use_ssl:
                connection_kwargs["ssl"] = True
                connection_kwargs["ssl_cert_reqs"] = None
                
            self.client = redis.Redis(**connection_kwargs)
            
            # Test connection
            self.client.ping()
            logger.info("Redis connection established successfully")
            self.initialized = True
            
        except RedisError as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            raise
        
    async def close(self) -> None:
        logger.info("Closing Redis connection")
        if self.client:
            self.client.close()
        self.initialized = False
        self.client = None
        
    def _check_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ShortTermMemory not initialized. Call initialize() first.")
            
    def _make_key(self, prefix: str, id: str) -> str:
        return f"{prefix}:{id}"
        
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        self._check_initialized()
        key = self._make_key("agent", agent_id)
        
        try:
            state_json = self.client.get(key)
            if state_json:
                return json.loads(state_json)
            return None
        except Exception as e:
            logger.error(f"Error getting agent state: {str(e)}")
            return None
            
    async def set_agent_state(
        self, agent_id: str, state: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        self._check_initialized()
        key = self._make_key("agent", agent_id)
        
        try:
            # Always add a timestamp
            state["updated_at"] = time.time()
            state_json = json.dumps(state)
            
            if ttl:
                return bool(self.client.setex(key, ttl, state_json))
            else:
                return bool(self.client.set(key, state_json))
        except Exception as e:
            logger.error(f"Error setting agent state: {str(e)}")
            return False
            
    async def update_agent_state(
        self, agent_id: str, updates: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        self._check_initialized()
        
        try:
            # Get existing state
            current_state = await self.get_agent_state(agent_id) or {}
            
            # Update state with new values
            current_state.update(updates)
            
            # Save updated state
            return await self.set_agent_state(agent_id, current_state, ttl)
        except Exception as e:
            logger.error(f"Error updating agent state: {str(e)}")
            return False
            
    async def delete_agent_state(self, agent_id: str) -> bool:
        self._check_initialized()
        key = self._make_key("agent", agent_id)
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting agent state: {str(e)}")
            return False
            
    async def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        self._check_initialized()
        key = self._make_key("task", task_id)
        
        try:
            state_json = self.client.get(key)
            if state_json:
                return json.loads(state_json)
            return None
        except Exception as e:
            logger.error(f"Error getting task state: {str(e)}")
            return None
            
    async def set_task_state(
        self, task_id: str, state: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        self._check_initialized()
        key = self._make_key("task", task_id)
        
        try:
            # Always add a timestamp
            state["updated_at"] = time.time()
            state_json = json.dumps(state)
            
            if ttl:
                return bool(self.client.setex(key, ttl, state_json))
            else:
                return bool(self.client.set(key, state_json))
        except Exception as e:
            logger.error(f"Error setting task state: {str(e)}")
            return False
            
    async def update_task_state(
        self, task_id: str, updates: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        self._check_initialized()
        
        try:
            # Get existing state
            current_state = await self.get_task_state(task_id) or {}
            
            # Update state with new values
            current_state.update(updates)
            
            # Save updated state
            return await self.set_task_state(task_id, current_state, ttl)
        except Exception as e:
            logger.error(f"Error updating task state: {str(e)}")
            return False
            
    async def delete_task_state(self, task_id: str) -> bool:
        self._check_initialized()
        key = self._make_key("task", task_id)
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting task state: {str(e)}")
            return False
            
    async def get_agent_tasks(self, agent_id: str) -> List[str]:
        self._check_initialized()
        key = self._make_key("agent_tasks", agent_id)
        
        try:
            tasks = self.client.smembers(key)
            return list(tasks) if tasks else []
        except Exception as e:
            logger.error(f"Error getting agent tasks: {str(e)}")
            return []
            
    async def add_agent_task(self, agent_id: str, task_id: str) -> bool:
        self._check_initialized()
        key = self._make_key("agent_tasks", agent_id)
        
        try:
            return bool(self.client.sadd(key, task_id))
        except Exception as e:
            logger.error(f"Error adding agent task: {str(e)}")
            return False
            
    async def remove_agent_task(self, agent_id: str, task_id: str) -> bool:
        self._check_initialized()
        key = self._make_key("agent_tasks", agent_id)
        
        try:
            return bool(self.client.srem(key, task_id))
        except Exception as e:
            logger.error(f"Error removing agent task: {str(e)}")
            return False


# Create singleton instance
short_term_memory = ShortTermMemory() 