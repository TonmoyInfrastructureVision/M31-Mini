import logging
from typing import Dict, List, Any, Optional, Set, Union, Tuple
import json
import asyncio
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

import redis.asyncio as redis
from redis.asyncio.client import Redis

from config.settings import settings

logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    id: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    namespace: str
    text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RedisStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        ssl: bool = False,
        default_ttl: int = 3600,
    ):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.ssl = ssl
        self.default_ttl = default_ttl
        
        self.redis: Optional[Redis] = None
        self.initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        if self.initialized:
            return
            
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                ssl=self.ssl,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            
            self.initialized = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            raise
            
    async def close(self) -> None:
        if self.redis:
            await self.redis.close()
            self.redis = None
            
        self.initialized = False
        logger.info("Closed Redis connection")
        
    async def _ensure_connected(self) -> None:
        if not self.initialized:
            await self.initialize()
            
        # Check if connection is alive
        try:
            if self.redis:
                await self.redis.ping()
        except:
            # Reconnect
            self.initialized = False
            await self.initialize()
            
    async def set(self, key: str, value: Union[str, Dict, bytes], ex: Optional[int] = None) -> bool:
        await self._ensure_connected()
        
        if ex is None:
            ex = self.default_ttl
            
        try:
            # Convert dict to JSON string
            if isinstance(value, dict):
                value = json.dumps(value)
                
            await self.redis.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Error setting key in Redis: {str(e)}")
            return False
            
    async def get(self, key: str) -> Optional[str]:
        await self._ensure_connected()
        
        try:
            value = await self.redis.get(key)
            
            if value is None:
                return None
                
            return value.decode("utf-8")
        except Exception as e:
            logger.error(f"Error getting key from Redis: {str(e)}")
            return None
            
    async def delete(self, key: str) -> bool:
        await self._ensure_connected()
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key from Redis: {str(e)}")
            return False
            
    async def exists(self, key: str) -> bool:
        await self._ensure_connected()
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence in Redis: {str(e)}")
            return False
            
    async def expire(self, key: str, seconds: int) -> bool:
        await self._ensure_connected()
        
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiry in Redis: {str(e)}")
            return False
            
    async def ttl(self, key: str) -> int:
        await self._ensure_connected()
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL from Redis: {str(e)}")
            return -2  # -2 means key doesn't exist
            
    async def keys(self, pattern: str) -> List[str]:
        await self._ensure_connected()
        
        try:
            keys = await self.redis.keys(pattern)
            return [key.decode("utf-8") for key in keys]
        except Exception as e:
            logger.error(f"Error getting keys from Redis: {str(e)}")
            return []
            
    async def delete_by_prefix(self, prefix: str) -> int:
        await self._ensure_connected()
        
        try:
            keys = await self.keys(f"{prefix}*")
            
            if not keys:
                return 0
                
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys by prefix from Redis: {str(e)}")
            return 0
            
    async def scan_iter(self, match: Optional[str] = None, count: int = 10) -> List[str]:
        await self._ensure_connected()
        
        result = []
        try:
            async for key in self.redis.scan_iter(match=match, count=count):
                result.append(key.decode("utf-8"))
            return result
        except Exception as e:
            logger.error(f"Error scanning keys from Redis: {str(e)}")
            return []
            
    async def hset(self, name: str, key: str, value: Union[str, Dict]) -> bool:
        await self._ensure_connected()
        
        try:
            # Convert dict to JSON string
            if isinstance(value, dict):
                value = json.dumps(value)
                
            await self.redis.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting hash key in Redis: {str(e)}")
            return False
            
    async def hget(self, name: str, key: str) -> Optional[str]:
        await self._ensure_connected()
        
        try:
            value = await self.redis.hget(name, key)
            
            if value is None:
                return None
                
            return value.decode("utf-8")
        except Exception as e:
            logger.error(f"Error getting hash key from Redis: {str(e)}")
            return None
            
    async def hgetall(self, name: str) -> Dict[str, str]:
        await self._ensure_connected()
        
        try:
            result = await self.redis.hgetall(name)
            
            if not result:
                return {}
                
            return {k.decode("utf-8"): v.decode("utf-8") for k, v in result.items()}
        except Exception as e:
            logger.error(f"Error getting all hash keys from Redis: {str(e)}")
            return {}
            
    async def hdel(self, name: str, *keys: str) -> int:
        await self._ensure_connected()
        
        try:
            return await self.redis.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Error deleting hash key from Redis: {str(e)}")
            return 0
            
    async def sadd(self, name: str, *values: str) -> int:
        await self._ensure_connected()
        
        try:
            return await self.redis.sadd(name, *values)
        except Exception as e:
            logger.error(f"Error adding to set in Redis: {str(e)}")
            return 0
            
    async def smembers(self, name: str) -> Set[str]:
        await self._ensure_connected()
        
        try:
            result = await self.redis.smembers(name)
            return {v.decode("utf-8") for v in result}
        except Exception as e:
            logger.error(f"Error getting set members from Redis: {str(e)}")
            return set()
            
    async def srem(self, name: str, *values: str) -> int:
        await self._ensure_connected()
        
        try:
            return await self.redis.srem(name, *values)
        except Exception as e:
            logger.error(f"Error removing from set in Redis: {str(e)}")
            return 0
            
    async def incr(self, name: str, amount: int = 1) -> int:
        await self._ensure_connected()
        
        try:
            return await self.redis.incrby(name, amount)
        except Exception as e:
            logger.error(f"Error incrementing key in Redis: {str(e)}")
            return 0
            
    async def pipeline_execute(self, commands: List[Tuple[str, List[Any]]]) -> List[Any]:
        await self._ensure_connected()
        
        try:
            pipeline = self.redis.pipeline()
            
            for cmd, args in commands:
                method = getattr(pipeline, cmd)
                method(*args)
                
            return await pipeline.execute()
        except Exception as e:
            logger.error(f"Error executing pipeline in Redis: {str(e)}")
            return []
            
    async def pubsub_subscribe(self, *channels: str) -> redis.client.PubSub:
        await self._ensure_connected()
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channels in Redis: {str(e)}")
            raise
            
    async def publish(self, channel: str, message: str) -> int:
        await self._ensure_connected()
        
        try:
            return await self.redis.publish(channel, message)
        except Exception as e:
            logger.error(f"Error publishing message in Redis: {str(e)}")
            return 0
            
    async def get_namespaces(self) -> Set[str]:
        await self._ensure_connected()
        
        try:
            keys = await self.redis.keys("memory:*")
            namespaces = set()
            
            for key in keys:
                key_str = key.decode("utf-8")
                parts = key_str.split(":")
                if len(parts) >= 2:
                    namespaces.add(parts[1])
                    
            return namespaces
        except Exception as e:
            logger.error(f"Error getting namespaces from Redis: {str(e)}")
            return set() 