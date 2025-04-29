from typing import Dict, List, Any, Optional, Tuple, Union
import json
from datetime import datetime

from .chroma_store import ChromaMemoryStore
from .redis_store import RedisMemoryStore
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class MemoryManager:
    def __init__(self) -> None:
        self.long_term = ChromaMemoryStore()
        self.short_term = RedisMemoryStore()
    
    async def initialize(self) -> None:
        try:
            await self.long_term.connect()
            await self.short_term.connect()
            logger.info("Memory stores initialized")
        except Exception as e:
            logger.error(f"Error initializing memory stores: {str(e)}")
            raise
    
    async def close(self) -> None:
        await self.short_term.close()
        logger.debug("Memory stores closed")
    
    async def add_memory(
        self,
        agent_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
        memory_type: str = "short_term",
    ) -> str:
        metadata = metadata or {}
        
        try:
            if memory_type == "long_term":
                memory_id = await self.long_term.add_memory(
                    agent_id=agent_id,
                    text=text,
                    metadata=metadata,
                    memory_id=memory_id
                )
                logger.debug(f"Added long-term memory for agent {agent_id}: {memory_id}")
            else:
                memory_id = await self.short_term.add_memory(
                    agent_id=agent_id,
                    text=text,
                    metadata=metadata,
                    memory_id=memory_id
                )
                logger.debug(f"Added short-term memory for agent {agent_id}: {memory_id}")
            
            return memory_id
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise
    
    async def search_memory(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
        search_type: str = "long_term",
    ) -> List[Dict[str, Any]]:
        try:
            if search_type == "long_term":
                memories = await self.long_term.search_memory(
                    agent_id=agent_id,
                    query=query,
                    limit=limit
                )
                logger.debug(f"Found {len(memories)} long-term memories for query: {query}")
                return memories
            else:
                # For short-term, we just get the recent memories
                memories = await self.short_term.get_agent_memories(
                    agent_id=agent_id,
                    limit=limit
                )
                logger.debug(f"Retrieved {len(memories)} short-term memories")
                return memories
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}")
            return []
    
    async def get_memory(
        self,
        memory_id: str,
        memory_type: str = "auto",
    ) -> Optional[Dict[str, Any]]:
        try:
            # Try short-term first if auto
            if memory_type in ["auto", "short_term"]:
                memory = await self.short_term.get_memory(memory_id)
                if memory:
                    return memory
            
            # If not found or explicitly long-term
            if memory_type in ["auto", "long_term"]:
                memory = await self.long_term.get_memory(memory_id)
                if memory:
                    return memory
            
            return None
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {str(e)}")
            return None
    
    async def delete_memory(
        self,
        memory_id: str,
        memory_type: str = "auto",
    ) -> bool:
        try:
            success = False
            
            if memory_type in ["auto", "short_term"]:
                success = await self.short_term.delete_memory(memory_id)
            
            if not success and memory_type in ["auto", "long_term"]:
                success = await self.long_term.delete_memory(memory_id)
            
            return success
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            return False
    
    async def delete_agent_memories(
        self,
        agent_id: str,
        memory_type: str = "all",
    ) -> bool:
        try:
            success = True
            
            if memory_type in ["all", "short_term"]:
                st_success = await self.short_term.delete_agent_memories(agent_id)
                success = success and st_success
            
            if memory_type in ["all", "long_term"]:
                lt_success = await self.long_term.delete_agent_memories(agent_id)
                success = success and lt_success
            
            return success
        except Exception as e:
            logger.error(f"Error deleting agent memories: {str(e)}")
            return False
    
    async def promote_to_long_term(
        self,
        memory_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            # Get from short-term
            memory = await self.short_term.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory not found for promotion: {memory_id}")
                return None
            
            # Add metadata
            metadata = memory["metadata"].copy()
            metadata["promoted_from"] = memory_id
            metadata["promoted_at"] = datetime.now().isoformat()
            
            if additional_metadata:
                metadata.update(additional_metadata)
            
            # Add to long-term
            agent_id = metadata["agent_id"]
            new_id = await self.long_term.add_memory(
                agent_id=agent_id,
                text=memory["text"],
                metadata=metadata
            )
            
            logger.info(f"Promoted memory {memory_id} to long-term: {new_id}")
            return new_id
        except Exception as e:
            logger.error(f"Error promoting memory to long-term: {str(e)}")
            return None
    
    async def get_agent_context(
        self,
        agent_id: str,
        query: Optional[str] = None,
        max_short_term: int = 5,
        max_long_term: int = 3,
    ) -> Dict[str, Any]:
        try:
            result = {
                "short_term": [],
                "long_term": [],
                "state": None,
            }
            
            # Get state
            state = await self.short_term.get_agent_state(agent_id)
            if state:
                result["state"] = state
            
            # Get short-term memories
            st_memories = await self.short_term.get_agent_memories(
                agent_id=agent_id,
                limit=max_short_term
            )
            result["short_term"] = st_memories
            
            # Get long-term memories if query is provided
            if query:
                lt_memories = await self.long_term.search_memory(
                    agent_id=agent_id,
                    query=query,
                    limit=max_long_term
                )
                result["long_term"] = lt_memories
            
            return result
        except Exception as e:
            logger.error(f"Error getting agent context: {str(e)}")
            return {"short_term": [], "long_term": [], "state": None}
    
    async def store_agent_state(
        self,
        agent_id: str,
        state: Dict[str, Any],
    ) -> bool:
        try:
            return await self.short_term.store_agent_state(agent_id, state)
        except Exception as e:
            logger.error(f"Error storing agent state: {str(e)}")
            return False


memory_manager = MemoryManager() 