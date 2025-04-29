import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Union
import uuid
import json
from datetime import datetime

from ..config.settings import settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class ChromaMemoryStore:
    def __init__(
        self,
        collection_name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        self.collection_name = collection_name or settings.chroma.collection_name
        self.host = host or settings.chroma.host
        self.port = port or settings.chroma.port
        self.client = None
        self.collection = None
        
    async def connect(self) -> None:
        if self.client is not None:
            return
        
        try:
            logger.info(f"Connecting to ChromaDB at {self.host}:{self.port}")
            
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=ChromaSettings(
                    anonymized_telemetry=False
                )
            )
            
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            except Exception:
                logger.info(f"Creating new collection: {self.collection_name}")
                self.collection = self.client.create_collection(self.collection_name)
        
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {str(e)}")
            raise
    
    async def add_memory(
        self,
        agent_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        if self.collection is None:
            await self.connect()
        
        memory_id = memory_id or str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        full_metadata = {
            "agent_id": agent_id,
            "timestamp": timestamp,
            "type": "memory",
        }
        
        if metadata:
            full_metadata.update(metadata)
        
        try:
            self.collection.add(
                documents=[text],
                metadatas=[full_metadata],
                ids=[memory_id]
            )
            logger.debug(f"Added memory for agent {agent_id}: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise
    
    async def search_memory(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self.collection is None:
            await self.connect()
        
        filter_dict = {"agent_id": agent_id}
        if metadata_filter:
            filter_dict.update(metadata_filter)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_dict
            )
            
            memories = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    memory = {
                        "id": results["ids"][0][i],
                        "text": doc,
                        "metadata": results["metadatas"][0][i],
                    }
                    memories.append(memory)
            
            logger.debug(f"Found {len(memories)} memories for query: {query}")
            return memories
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        if self.collection is None:
            await self.connect()
        
        try:
            result = self.collection.get(ids=[memory_id])
            
            if not result["documents"]:
                return None
            
            memory = {
                "id": memory_id,
                "text": result["documents"][0],
                "metadata": result["metadatas"][0],
            }
            
            return memory
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {str(e)}")
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if self.collection is None:
            await self.connect()
        
        try:
            existing = await self.get_memory(memory_id)
            if not existing:
                logger.error(f"Memory not found for update: {memory_id}")
                return False
            
            update_dict = {}
            
            if text is not None:
                update_dict["documents"] = [text]
            
            if metadata is not None:
                new_metadata = existing["metadata"].copy()
                new_metadata.update(metadata)
                update_dict["metadatas"] = [new_metadata]
            
            if update_dict:
                update_dict["ids"] = [memory_id]
                self.collection.update(**update_dict)
                logger.debug(f"Updated memory: {memory_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {str(e)}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        if self.collection is None:
            await self.connect()
        
        try:
            self.collection.delete(ids=[memory_id])
            logger.debug(f"Deleted memory: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            return False
    
    async def delete_agent_memories(self, agent_id: str) -> bool:
        if self.collection is None:
            await self.connect()
        
        try:
            self.collection.delete(where={"agent_id": agent_id})
            logger.info(f"Deleted all memories for agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memories for agent {agent_id}: {str(e)}")
            return False 