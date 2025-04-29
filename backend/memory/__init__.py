import logging
from typing import Dict, Any, Optional, List

from memory.short_term import short_term_memory
from memory.vector_store import vector_store

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self):
        self.short_term = short_term_memory
        self.long_term = vector_store
        
    async def initialize(self) -> None:
        logger.info("Initializing memory subsystems")
        
        try:
            await self.short_term.initialize()
            await self.long_term.initialize()
            logger.info("Memory systems initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing memory systems: {str(e)}")
            raise
            
    async def close(self) -> None:
        logger.info("Closing memory connections")
        
        try:
            await self.short_term.close()
            await self.long_term.close()
            logger.info("Memory connections closed")
        except Exception as e:
            logger.error(f"Error closing memory connections: {str(e)}")
            
    async def add_long_term_memory(
        self, agent_id: str, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        return await self.long_term.add_memory(agent_id, text, metadata)
        
    async def search_long_term_memory(
        self, agent_id: str, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return await self.long_term.search_memories(agent_id, query, limit, filters)
        
    async def save_agent_state(
        self, agent_id: str, state: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        return await self.short_term.set_agent_state(agent_id, state, ttl)
        
    async def update_agent_state(
        self, agent_id: str, updates: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        return await self.short_term.update_agent_state(agent_id, updates, ttl)
        
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return await self.short_term.get_agent_state(agent_id)


# Create singleton instance
memory_manager = MemoryManager() 