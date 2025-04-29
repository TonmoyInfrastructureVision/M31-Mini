import redis.asyncio as redis
import json
from typing import Dict, List, Any, Optional, Union
import time
from datetime import datetime, timedelta
import uuid

from ..config.settings import settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class RedisMemoryStore:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        self.host = host or settings.redis.host
        self.port = port or settings.redis.port
        self.db = db if db is not None else settings.redis.db
        self.password = password or settings.redis.password
        self.ttl = ttl or settings.redis.ttl
        self.client = None
    
    async def connect(self) -> None:
        if self.client is not None:
            return
        
        try:
            logger.info(f"Connecting to Redis at {self.host}:{self.port}/{self.db}")
            
            self.client = await redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
            
            # Test connection
            await self.client.ping()
            logger.info("Connected to Redis successfully")
        
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            raise
    
    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None
            logger.debug("Redis connection closed")
    
    def _agent_key(self, agent_id: str) -> str:
        return f"agent:{agent_id}:cache"
    
    def _memory_key(self, memory_id: str) -> str:
        return f"memory:{memory_id}"
    
    def _index_key(self, agent_id: str) -> str:
        return f"agent:{agent_id}:memories"
    
    async def add_memory(
        self,
        agent_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> str:
        if self.client is None:
            await self.connect()
        
        memory_id = memory_id or str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        expiry = ttl or self.ttl
        
        full_metadata = {
            "agent_id": agent_id,
            "timestamp": timestamp,
            "type": "short_term",
        }
        
        if metadata:
            full_metadata.update(metadata)
        
        memory_data = {
            "id": memory_id,
            "text": text,
            "metadata": full_metadata,
        }
        
        memory_key = self._memory_key(memory_id)
        index_key = self._index_key(agent_id)
        
        try:
            # Store the memory
            await self.client.setex(
                memory_key,
                expiry,
                json.dumps(memory_data)
            )
            
            # Add to agent's memory index with score as timestamp
            score = time.time()
            await self.client.zadd(index_key, {memory_id: score})
            
            # Set TTL on the index if not already set
            if not await self.client.ttl(index_key) > 0:
                await self.client.expire(index_key, expiry)
            
            logger.debug(f"Added short-term memory for agent {agent_id}: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding memory to Redis: {str(e)}")
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        if self.client is None:
            await self.connect()
        
        memory_key = self._memory_key(memory_id)
        
        try:
            data = await self.client.get(memory_key)
            if not data:
                return None
            
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting memory from Redis: {str(e)}")
            return None
    
    async def get_agent_memories(
        self,
        agent_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str = "desc",
    ) -> List[Dict[str, Any]]:
        if self.client is None:
            await self.connect()
        
        index_key = self._index_key(agent_id)
        
        try:
            # Get memory IDs from sorted set, newest first or oldest first
            if sort.lower() == "desc":
                # Newest first (highest score to lowest)
                memory_ids = await self.client.zrevrange(index_key, offset, offset + limit - 1)
            else:
                # Oldest first (lowest score to highest)
                memory_ids = await self.client.zrange(index_key, offset, offset + limit - 1)
            
            if not memory_ids:
                return []
            
            # Get memories from their keys
            memory_keys = [self._memory_key(mid) for mid in memory_ids]
            memory_data = await self.client.mget(memory_keys)
            
            # Parse JSON
            memories = []
            for data in memory_data:
                if data:
                    try:
                        memory = json.loads(data)
                        memories.append(memory)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode memory data: {data}")
            
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving agent memories from Redis: {str(e)}")
            return []
    
    async def update_memory_ttl(self, memory_id: str, ttl: Optional[int] = None) -> bool:
        if self.client is None:
            await self.connect()
        
        expiry = ttl or self.ttl
        memory_key = self._memory_key(memory_id)
        
        try:
            # Check if memory exists
            exists = await self.client.exists(memory_key)
            if not exists:
                return False
            
            # Update TTL
            await self.client.expire(memory_key, expiry)
            logger.debug(f"Updated TTL for memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory TTL: {str(e)}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        if self.client is None:
            await self.connect()
        
        memory_key = self._memory_key(memory_id)
        
        try:
            # Get the memory to find the agent_id
            memory_data = await self.get_memory(memory_id)
            if not memory_data:
                return False
            
            agent_id = memory_data["metadata"]["agent_id"]
            index_key = self._index_key(agent_id)
            
            # Delete memory and remove from index
            await self.client.delete(memory_key)
            await self.client.zrem(index_key, memory_id)
            
            logger.debug(f"Deleted memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return False
    
    async def delete_agent_memories(self, agent_id: str) -> bool:
        if self.client is None:
            await self.connect()
        
        index_key = self._index_key(agent_id)
        
        try:
            # Get all memory IDs for the agent
            memory_ids = await self.client.zrange(index_key, 0, -1)
            
            if memory_ids:
                # Delete each memory
                memory_keys = [self._memory_key(mid) for mid in memory_ids]
                await self.client.delete(*memory_keys)
            
            # Delete the index
            await self.client.delete(index_key)
            
            logger.info(f"Deleted all short-term memories for agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting agent memories: {str(e)}")
            return False
    
    async def store_agent_state(
        self,
        agent_id: str,
        state: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        if self.client is None:
            await self.connect()
        
        key = self._agent_key(agent_id)
        expiry = ttl or self.ttl
        
        try:
            await self.client.setex(key, expiry, json.dumps(state))
            logger.debug(f"Stored state for agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing agent state: {str(e)}")
            return False
    
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if self.client is None:
            await self.connect()
        
        key = self._agent_key(agent_id)
        
        try:
            data = await self.client.get(key)
            if not data:
                return None
            
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error retrieving agent state: {str(e)}")
            return None 