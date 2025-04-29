import logging
from typing import List, Dict, Optional, Any
import os
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from config.settings import settings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_function = None
        self.initialized = False
        
    async def initialize(self) -> None:
        logger.info(f"Initializing ChromaDB with settings: {settings.chroma}")
        
        # Ensure persist directory exists
        os.makedirs(settings.chroma.persist_directory, exist_ok=True)
        
        # Set up embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.chroma.embedding_model
        )
        
        # Initialize client
        self.client = chromadb.PersistentClient(
            path=settings.chroma.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="agent_memories",
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collection 'agent_memories' initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection: {str(e)}")
            raise
            
        self.initialized = True
        
    async def close(self) -> None:
        logger.info("Closing ChromaDB connection")
        self.initialized = False
        self.client = None
        self.collection = None
        
    def _check_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")
            
    async def add_memory(
        self, 
        agent_id: str, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> str:
        self._check_initialized()
        
        memory_id = str(uuid.uuid4())
        embedding_id = memory_id
        
        try:
            # Prepare metadata (ensure all values are strings for ChromaDB)
            safe_metadata = {}
            if metadata:
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        safe_metadata[k] = str(v)
                    elif v is None:
                        safe_metadata[k] = "null"
                    else:
                        # Skip complex objects
                        continue
                        
            # Always add agent_id and memory_id
            safe_metadata["agent_id"] = agent_id
            safe_metadata["memory_id"] = memory_id
            
            # Add to ChromaDB
            self.collection.add(
                ids=[embedding_id],
                documents=[text],
                metadatas=[safe_metadata]
            )
            
            logger.debug(f"Added memory {memory_id} for agent {agent_id}")
            return embedding_id
            
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise
            
    async def search_memories(
        self, 
        agent_id: str, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        self._check_initialized()
        
        try:
            # Build filter to include agent_id
            where_filter = {"agent_id": agent_id}
            
            # Add additional filters if provided
            if filters:
                for k, v in filters.items():
                    if k != "agent_id":  # Skip if trying to override agent_id
                        where_filter[k] = v
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            # Process results
            memories = []
            if results and results["ids"] and results["documents"]:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0] * len(ids)
                
                for i in range(len(ids)):
                    # Calculate relevance score (invert distance)
                    relevance = 1.0 - (distances[i] / 2.0) if distances[i] <= 2.0 else 0.0
                    
                    # Extract memory_id from metadata or use embedding_id
                    memory_id = metadatas[i].get("memory_id", ids[i])
                    
                    memories.append({
                        "id": memory_id,
                        "embedding_id": ids[i],
                        "agent_id": agent_id,
                        "text": documents[i],
                        "metadata": metadatas[i],
                        "relevance_score": relevance
                    })
            
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise
            
    async def delete_memory(self, embedding_id: str) -> bool:
        self._check_initialized()
        
        try:
            self.collection.delete(ids=[embedding_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return False
            
    async def delete_agent_memories(self, agent_id: str) -> bool:
        self._check_initialized()
        
        try:
            self.collection.delete(where={"agent_id": agent_id})
            return True
        except Exception as e:
            logger.error(f"Error deleting agent memories: {str(e)}")
            return False


# Create singleton instance
vector_store = VectorStore() 