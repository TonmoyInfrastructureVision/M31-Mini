import logging
from typing import List, Dict, Any, Optional, Tuple, Set, Union, Callable
import uuid
import json
import time
import asyncio
from datetime import datetime, timedelta
import hashlib
import os
from abc import ABC, abstractmethod

from config.settings import settings
from .vector_store import VectorStore, ChromaVectorStore
from .redis_store import RedisStore, MemoryEntry

logger = logging.getLogger(__name__)


class MemoryInterface(ABC):
    @abstractmethod
    async def add(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, namespace: str = "default") -> str:
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5, namespace: str = "default", 
                    filters: Optional[Dict[str, Any]] = None, min_score: float = 0.0) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def add_conversation(self, agent_id: str, task_id: str, role: str, content: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        pass

    @abstractmethod
    async def get_conversation_history(self, agent_id: str, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def clear(self, namespace: str = "default") -> bool:
        pass


class MemoryManager(MemoryInterface):
    def __init__(self):
        self.initialized = False
        self.vector_store: Optional[VectorStore] = None
        self.redis_store: Optional[RedisStore] = None
        self.available_namespaces: Set[str] = set()
        self._batch_queue: Dict[str, List[Tuple[Dict[str, Any], Dict[str, Any]]]] = {}
        self._task_memory_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._memory_locks: Dict[str, asyncio.Lock] = {}
        
    async def initialize(self) -> None:
        if self.initialized:
            return
        
        logger.info("Initializing memory manager")
        
        try:
            # Initialize vector database
            if settings.memory.vector_db_type == "chroma":
                logger.info(f"Initializing ChromaDB vector store with persistence at {settings.memory.chroma_persist_directory}")
                os.makedirs(settings.memory.chroma_persist_directory, exist_ok=True)
                self.vector_store = ChromaVectorStore(
                    persist_directory=settings.memory.chroma_persist_directory,
                    embedding_model=settings.memory.embedding_model
                )
                await self.vector_store.initialize()
            else:
                raise ValueError(f"Unsupported vector database type: {settings.memory.vector_db_type}")
            
            # Initialize Redis
            logger.info(f"Initializing Redis store at {settings.redis.host}:{settings.redis.port}")
            self.redis_store = RedisStore(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                db=settings.redis.db,
                ssl=settings.redis.ssl,
                default_ttl=settings.memory.redis_ttl_seconds
            )
            await self.redis_store.initialize()
            
            # Set up batch processing if enabled
            if settings.memory.structured_storage_enabled:
                logger.info("Starting background batch processing task")
                asyncio.create_task(self._batch_processing_loop())
            
            self.initialized = True
            logger.info("Memory manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing memory manager: {str(e)}")
            raise
    
    async def close(self) -> None:
        logger.info("Closing memory manager connections")
        
        if self.vector_store:
            await self.vector_store.close()
            
        if self.redis_store:
            await self.redis_store.close()
            
        self.initialized = False
        logger.info("Memory manager closed")
    
    async def add(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, namespace: str = "default") -> str:
        if not self.initialized:
            await self.initialize()
            
        if not metadata:
            metadata = {}
            
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.utcnow().isoformat()
            
        # Generate a unique ID if not provided
        entry_id = metadata.get("id", str(uuid.uuid4()))
        metadata["id"] = entry_id
        
        # Convert data to text if it's not already
        if isinstance(data, dict):
            text = json.dumps(data)
        else:
            text = str(data)
            
        # Store in vector database for semantic search
        await self.vector_store.add(
            id=entry_id,
            text=text,
            metadata=metadata,
            namespace=namespace
        )
        
        # Ensure namespace is tracked
        self.available_namespaces.add(namespace)
        
        # Store in redis for fast lookup
        if settings.memory.structured_storage_enabled:
            entry = MemoryEntry(
                id=entry_id,
                data=data,
                metadata=metadata,
                namespace=namespace,
                text=text,
                created_at=datetime.utcnow()
            )
            await self.redis_store.set(f"memory:{namespace}:{entry_id}", entry.model_dump())
        
        logger.debug(f"Added memory entry {entry_id} to namespace {namespace}")
        return entry_id
    
    async def add_batch(self, items: List[Tuple[Dict[str, Any], Dict[str, Any]]], namespace: str = "default") -> List[str]:
        if not self.initialized:
            await self.initialize()
            
        if not items:
            return []
            
        # Get lock for this namespace to prevent concurrent batch operations
        if namespace not in self._memory_locks:
            self._memory_locks[namespace] = asyncio.Lock()
            
        async with self._memory_locks[namespace]:
            # Add each item to vector store
            entries = []
            ids = []
            
            for data, metadata in items:
                # Add timestamp if not present
                if "timestamp" not in metadata:
                    metadata["timestamp"] = datetime.utcnow().isoformat()
                    
                # Generate a unique ID if not provided
                entry_id = metadata.get("id", str(uuid.uuid4()))
                metadata["id"] = entry_id
                ids.append(entry_id)
                
                # Convert data to text if it's not already
                if isinstance(data, dict):
                    text = json.dumps(data)
                else:
                    text = str(data)
                    
                entries.append((entry_id, text, metadata))
                
                # Store in redis for fast lookup if enabled
                if settings.memory.structured_storage_enabled:
                    entry = MemoryEntry(
                        id=entry_id,
                        data=data,
                        metadata=metadata,
                        namespace=namespace,
                        text=text,
                        created_at=datetime.utcnow()
                    )
                    await self.redis_store.set(f"memory:{namespace}:{entry_id}", entry.model_dump())
            
            # Add all entries to vector store in one batch
            await self.vector_store.add_batch(entries, namespace)
            
            # Ensure namespace is tracked
            self.available_namespaces.add(namespace)
            
            logger.debug(f"Added batch of {len(entries)} memory entries to namespace {namespace}")
            return ids
    
    async def queue_for_batch(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, 
                             namespace: str = "default") -> str:
        if not metadata:
            metadata = {}
            
        # Generate a unique ID if not provided
        entry_id = metadata.get("id", str(uuid.uuid4()))
        metadata["id"] = entry_id
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.utcnow().isoformat()
            
        # Add to batch queue
        if namespace not in self._batch_queue:
            self._batch_queue[namespace] = []
            
        self._batch_queue[namespace].append((data, metadata))
        
        return entry_id
    
    async def _batch_processing_loop(self) -> None:
        while True:
            await asyncio.sleep(5)  # Process batches every 5 seconds
            
            try:
                for namespace, items in list(self._batch_queue.items()):
                    if items:
                        batch = items.copy()
                        self._batch_queue[namespace] = []
                        await self.add_batch(batch, namespace)
                        logger.debug(f"Processed batch of {len(batch)} items for namespace {namespace}")
            except Exception as e:
                logger.error(f"Error in batch processing loop: {str(e)}")
    
    async def search(self, query: str, limit: int = 5, namespace: str = "default", 
                    filters: Optional[Dict[str, Any]] = None, min_score: float = 0.0) -> List[Dict[str, Any]]:
        if not self.initialized:
            await self.initialize()
            
        start_time = time.time()
        
        # First check cache if caching is enabled
        if settings.memory.caching_enabled:
            cache_key = hashlib.md5(f"{query}:{namespace}:{limit}:{json.dumps(filters or {})}".encode()).hexdigest()
            cached_results = await self.redis_store.get(f"search_cache:{cache_key}")
            
            if cached_results:
                logger.debug(f"Cache hit for query '{query}' in namespace {namespace}")
                return json.loads(cached_results)
        
        # Perform search in vector store
        results = await self.vector_store.search(
            query=query,
            limit=limit,
            namespace=namespace,
            filters=filters,
            min_score=min_score
        )
        
        # Process and enhance results
        enhanced_results = []
        for result in results:
            # Try to get full data from Redis if available
            if settings.memory.structured_storage_enabled:
                entry_data = await self.redis_store.get(f"memory:{namespace}:{result['id']}")
                if entry_data:
                    # Merge with vector search result to include score
                    entry = json.loads(entry_data)
                    entry["score"] = result["score"]
                    enhanced_results.append(entry)
                else:
                    enhanced_results.append(result)
            else:
                enhanced_results.append(result)
        
        # Cache results if caching is enabled
        if settings.memory.caching_enabled:
            await self.redis_store.set(
                f"search_cache:{cache_key}", 
                json.dumps(enhanced_results),
                ex=settings.memory.cache_ttl_seconds
            )
        
        search_time = time.time() - start_time
        logger.debug(f"Search for '{query}' in namespace {namespace} returned {len(enhanced_results)} results in {search_time:.2f}s")
        
        return enhanced_results
    
    async def get(self, entry_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        if not self.initialized:
            await self.initialize()
            
        # Try to get from Redis first
        if settings.memory.structured_storage_enabled:
            entry_data = await self.redis_store.get(f"memory:{namespace}:{entry_id}")
            if entry_data:
                return json.loads(entry_data)
        
        # Fall back to vector store
        result = await self.vector_store.get(entry_id, namespace)
        if not result:
            return None
            
        return result
    
    async def add_conversation(self, agent_id: str, task_id: str, role: str, content: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        if not self.initialized:
            await self.initialize()
            
        if not metadata:
            metadata = {}
            
        namespace = f"conversation:{agent_id}"
        
        # Prepare message data
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        message_data = {
            "agent_id": agent_id,
            "task_id": task_id,
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        
        # Update metadata
        metadata.update({
            "id": message_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "role": role,
            "message_type": "conversation",
            "timestamp": timestamp
        })
        
        # Add to memory
        await self.add(message_data, metadata, namespace)
        
        # Update in-memory cache for this task
        task_cache_key = f"{agent_id}:{task_id}"
        if task_cache_key not in self._task_memory_cache:
            self._task_memory_cache[task_cache_key] = []
            
        self._task_memory_cache[task_cache_key].append({
            "id": message_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
            **metadata
        })
        
        # Trim cache if it exceeds the maximum size
        if len(self._task_memory_cache[task_cache_key]) > settings.memory.max_short_term_history:
            self._task_memory_cache[task_cache_key] = self._task_memory_cache[task_cache_key][-settings.memory.max_short_term_history:]
        
        return message_id
    
    async def get_conversation_history(self, agent_id: str, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.initialized:
            await self.initialize()
            
        # Check in-memory cache first
        task_cache_key = f"{agent_id}:{task_id}"
        if task_cache_key in self._task_memory_cache:
            history = self._task_memory_cache[task_cache_key]
            return history[-limit:] if limit > 0 else history
        
        # Otherwise, search in vector store
        namespace = f"conversation:{agent_id}"
        
        filters = {
            "task_id": task_id,
            "message_type": "conversation"
        }
        
        # Use vector search sorted by timestamp
        results = await self.vector_store.search_by_metadata(
            filters=filters,
            namespace=namespace,
            sort_field="timestamp",
            sort_order="asc"
        )
        
        # Update cache
        self._task_memory_cache[task_cache_key] = results
        
        return results[-limit:] if limit > 0 else results
    
    async def add_task_memory(self, agent_id: str, task_id: str, memory_type: str, 
                             data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        if not self.initialized:
            await self.initialize()
            
        if not metadata:
            metadata = {}
            
        namespace = f"task_memory:{agent_id}"
        
        # Prepare memory data
        memory_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Update metadata
        metadata.update({
            "id": memory_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "memory_type": memory_type,
            "timestamp": timestamp
        })
        
        # Add to memory
        await self.add(data, metadata, namespace)
        
        return memory_id
    
    async def get_task_memory(self, agent_id: str, task_id: str, memory_type: Optional[str] = None, 
                             limit: int = 10) -> List[Dict[str, Any]]:
        if not self.initialized:
            await self.initialize()
            
        namespace = f"task_memory:{agent_id}"
        
        filters = {
            "agent_id": agent_id,
            "task_id": task_id
        }
        
        if memory_type:
            filters["memory_type"] = memory_type
        
        # Use vector store search by metadata
        results = await self.vector_store.search_by_metadata(
            filters=filters,
            namespace=namespace,
            sort_field="timestamp",
            sort_order="desc"
        )
        
        return results[:limit] if limit > 0 else results
    
    async def delete_conversation(self, agent_id: str, task_id: str) -> bool:
        if not self.initialized:
            await self.initialize()
            
        namespace = f"conversation:{agent_id}"
        
        filters = {
            "agent_id": agent_id,
            "task_id": task_id,
            "message_type": "conversation"
        }
        
        # Delete from vector store
        deleted = await self.vector_store.delete_by_metadata(filters, namespace)
        
        # Clear cache
        task_cache_key = f"{agent_id}:{task_id}"
        if task_cache_key in self._task_memory_cache:
            del self._task_memory_cache[task_cache_key]
            
        return deleted
    
    async def delete_task_memory(self, agent_id: str, task_id: str, memory_type: Optional[str] = None) -> bool:
        if not self.initialized:
            await self.initialize()
            
        namespace = f"task_memory:{agent_id}"
        
        filters = {
            "agent_id": agent_id,
            "task_id": task_id
        }
        
        if memory_type:
            filters["memory_type"] = memory_type
        
        # Delete from vector store
        return await self.vector_store.delete_by_metadata(filters, namespace)
    
    async def clear(self, namespace: str = "default") -> bool:
        if not self.initialized:
            await self.initialize()
            
        # Clear from vector store
        result = await self.vector_store.clear(namespace)
        
        # Clear from redis if structured storage is enabled
        if settings.memory.structured_storage_enabled:
            await self.redis_store.delete_by_prefix(f"memory:{namespace}:")
            
        # Clear relevant caches
        if namespace.startswith("conversation:"):
            agent_id = namespace.split(":", 1)[1]
            for key in list(self._task_memory_cache.keys()):
                if key.startswith(f"{agent_id}:"):
                    del self._task_memory_cache[key]
                    
        return result
    
    async def clear_all(self) -> bool:
        if not self.initialized:
            await self.initialize()
            
        # Clear all namespaces in vector store
        result = True
        for namespace in self.available_namespaces:
            ns_result = await self.vector_store.clear(namespace)
            result = result and ns_result
            
        # Clear redis if structured storage is enabled
        if settings.memory.structured_storage_enabled:
            await self.redis_store.delete_by_prefix("memory:")
            
        # Clear caches
        self._task_memory_cache.clear()
        self.available_namespaces.clear()
        
        return result
    
    async def get_relevant_memories(self, agent_id: str, query: str, limit: int = 5, 
                                   include_tasks: bool = True, include_conversations: bool = True,
                                   min_score: float = 0.0) -> List[Dict[str, Any]]:
        if not self.initialized:
            await self.initialize()
            
        results = []
        
        # Search conversations
        if include_conversations:
            conversations = await self.search(
                query=query,
                limit=limit,
                namespace=f"conversation:{agent_id}",
                min_score=min_score
            )
            for convo in conversations:
                convo["source"] = "conversation"
                results.append(convo)
                
        # Search task memories
        if include_tasks:
            task_memories = await self.search(
                query=query,
                limit=limit,
                namespace=f"task_memory:{agent_id}",
                min_score=min_score
            )
            for mem in task_memories:
                mem["source"] = "task_memory"
                results.append(mem)
                
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return results[:limit]
    
    async def get_namespaces(self) -> List[str]:
        if not self.initialized:
            await self.initialize()
            
        # Get all namespaces from vector store
        vector_namespaces = await self.vector_store.get_namespaces()
        
        # Update our tracking set
        self.available_namespaces.update(vector_namespaces)
        
        return list(self.available_namespaces)


# Create singleton instance
memory_manager = MemoryManager() 