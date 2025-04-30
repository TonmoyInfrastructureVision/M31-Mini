import logging
import os
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
import asyncio
from abc import ABC, abstractmethod
import time
import json
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from config.settings import settings

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    @abstractmethod
    async def add(self, id: str, text: str, metadata: Dict[str, Any], namespace: str = "default") -> None:
        pass
    
    @abstractmethod
    async def add_batch(self, items: List[Tuple[str, str, Dict[str, Any]]], namespace: str = "default") -> None:
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 5, namespace: str = "default", 
                    filters: Optional[Dict[str, Any]] = None, min_score: float = 0.0) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get(self, id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def delete(self, id: str, namespace: str = "default") -> bool:
        pass
    
    @abstractmethod
    async def clear(self, namespace: str = "default") -> bool:
        pass
    
    @abstractmethod
    async def get_namespaces(self) -> List[str]:
        pass
    
    @abstractmethod
    async def search_by_metadata(self, filters: Dict[str, Any], namespace: str = "default",
                                sort_field: Optional[str] = None, sort_order: str = "desc") -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def delete_by_metadata(self, filters: Dict[str, Any], namespace: str = "default") -> bool:
        pass


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_directory: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.client = None
        self.embedding_function = None
        self.collections: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        try:
            # Set up embedding function
            if self.embedding_model == "all-MiniLM-L6-v2":
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            else:
                raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
            
            # Create client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"Initialized ChromaDB at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    async def close(self) -> None:
        # Nothing to close with ChromaDB
        self.client = None
        self.collections = {}
        logger.info("Closed ChromaDB client")
    
    async def _get_collection(self, namespace: str) -> Any:
        # Ensure we have a valid client
        if not self.client:
            await self.initialize()
        
        # Check if we already have this collection
        if namespace in self.collections:
            return self.collections[namespace]
        
        # Get or create collection
        async with self._lock:
            try:
                # Check again in case it was created while waiting for lock
                if namespace in self.collections:
                    return self.collections[namespace]
                
                # Create or get collection
                collection = self.client.get_or_create_collection(
                    name=namespace,
                    embedding_function=self.embedding_function,
                    metadata={"created_at": datetime.utcnow().isoformat()}
                )
                
                self.collections[namespace] = collection
                return collection
            except Exception as e:
                logger.error(f"Error getting collection {namespace}: {str(e)}")
                raise
    
    async def add(self, id: str, text: str, metadata: Dict[str, Any], namespace: str = "default") -> None:
        try:
            collection = await self._get_collection(namespace)
            
            # Add document to collection
            collection.add(
                ids=[id],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.debug(f"Added document {id} to collection {namespace}")
        except Exception as e:
            logger.error(f"Error adding document to ChromaDB: {str(e)}")
            raise
    
    async def add_batch(self, items: List[Tuple[str, str, Dict[str, Any]]], namespace: str = "default") -> None:
        if not items:
            return
            
        try:
            collection = await self._get_collection(namespace)
            
            # Separate into component lists
            ids = []
            documents = []
            metadatas = []
            
            for item_id, text, metadata in items:
                ids.append(item_id)
                documents.append(text)
                metadatas.append(metadata)
            
            # Add documents to collection
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.debug(f"Added batch of {len(items)} documents to collection {namespace}")
        except Exception as e:
            logger.error(f"Error adding batch to ChromaDB: {str(e)}")
            raise
    
    async def search(self, query: str, limit: int = 5, namespace: str = "default", 
                    filters: Optional[Dict[str, Any]] = None, min_score: float = 0.0) -> List[Dict[str, Any]]:
        try:
            collection = await self._get_collection(namespace)
            
            # Convert filters to Chroma format if provided
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = value
            
            # Perform search
            results = collection.query(
                query_texts=[query],
                n_results=limit * 2,  # Get more than needed to filter by score
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            processed_results = []
            
            if not results["ids"][0]:  # No results
                return []
                
            for i, result_id in enumerate(results["ids"][0]):
                # Calculate similarity score from distance (1.0 - distance)
                distance = results["distances"][0][i]
                score = 1.0 - distance
                
                # Skip results below minimum score
                if score < min_score:
                    continue
                
                # Create result object
                result = {
                    "id": result_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": score
                }
                
                processed_results.append(result)
            
            # Sort by score and limit results
            processed_results.sort(key=lambda x: x["score"], reverse=True)
            return processed_results[:limit]
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []
    
    async def get(self, id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        try:
            collection = await self._get_collection(namespace)
            
            result = collection.get(
                ids=[id],
                include=["documents", "metadatas"]
            )
            
            if not result["ids"]:
                return None
                
            return {
                "id": result["ids"][0],
                "text": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        except Exception as e:
            logger.error(f"Error getting document from ChromaDB: {str(e)}")
            return None
    
    async def delete(self, id: str, namespace: str = "default") -> bool:
        try:
            collection = await self._get_collection(namespace)
            
            collection.delete(ids=[id])
            
            logger.debug(f"Deleted document {id} from collection {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document from ChromaDB: {str(e)}")
            return False
    
    async def clear(self, namespace: str = "default") -> bool:
        try:
            # Check if collection exists
            if namespace not in self.collections and namespace not in await self.get_namespaces():
                return True  # Nothing to clear
                
            collection = await self._get_collection(namespace)
            
            # Delete all documents
            collection.delete()
            
            # Remove from cache
            if namespace in self.collections:
                del self.collections[namespace]
                
            logger.info(f"Cleared collection {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection in ChromaDB: {str(e)}")
            return False
    
    async def get_namespaces(self) -> List[str]:
        try:
            if not self.client:
                await self.initialize()
                
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"Error listing collections in ChromaDB: {str(e)}")
            return []
    
    async def search_by_metadata(self, filters: Dict[str, Any], namespace: str = "default",
                               sort_field: Optional[str] = None, sort_order: str = "desc") -> List[Dict[str, Any]]:
        try:
            collection = await self._get_collection(namespace)
            
            # Convert filters to Chroma format
            where_clause = {}
            for key, value in filters.items():
                where_clause[key] = value
            
            # Get all matching documents
            result = collection.get(
                where=where_clause,
                include=["documents", "metadatas"]
            )
            
            if not result["ids"]:
                return []
                
            # Process results
            processed_results = []
            for i, result_id in enumerate(result["ids"]):
                processed_results.append({
                    "id": result_id,
                    "text": result["documents"][i],
                    "metadata": result["metadatas"][i]
                })
            
            # Sort results if requested
            if sort_field:
                reverse = sort_order.lower() == "desc"
                processed_results.sort(
                    key=lambda x: x["metadata"].get(sort_field, ""),
                    reverse=reverse
                )
                
            return processed_results
        except Exception as e:
            logger.error(f"Error searching by metadata in ChromaDB: {str(e)}")
            return []
    
    async def delete_by_metadata(self, filters: Dict[str, Any], namespace: str = "default") -> bool:
        try:
            collection = await self._get_collection(namespace)
            
            # Convert filters to Chroma format
            where_clause = {}
            for key, value in filters.items():
                where_clause[key] = value
            
            # Find documents to delete
            result = collection.get(
                where=where_clause,
                include=["documents"]
            )
            
            if not result["ids"]:
                return True  # Nothing to delete
                
            # Delete matching documents
            collection.delete(
                where=where_clause
            )
            
            logger.debug(f"Deleted {len(result['ids'])} documents from collection {namespace} based on metadata filters")
            return True
        except Exception as e:
            logger.error(f"Error deleting by metadata in ChromaDB: {str(e)}")
            return False


# Create singleton instance
vector_store = ChromaVectorStore(settings.chroma.persist_directory, settings.chroma.embedding_model) 