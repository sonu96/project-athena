"""
Firestore Client for real-time data storage

Handles agent state, observations, and operational data.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from google.cloud import firestore
from google.api_core import exceptions

from ..config import settings

logger = logging.getLogger(__name__)


class FirestoreClient:
    """
    Client for Google Firestore operations
    
    Collections:
    - agents: Agent state and configuration
    - observations: Pool observations
    - memories: Memory metadata (actual content in Mem0)
    - analytics: Daily summaries
    """
    
    def __init__(self):
        try:
            self.db = firestore.Client(
                project=settings.gcp_project_id,
                database=settings.firestore_database
            )
            self._initialized = True
            logger.info("✅ Firestore client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            self._initialized = False
            self.db = None
    
    async def store_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store a document in Firestore
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data
            
        Returns:
            Success status
        """
        if not self._initialized:
            logger.warning("Firestore not initialized")
            return False
        
        try:
            # Add timestamp
            data["updated_at"] = datetime.utcnow()
            
            # Store document
            self.db.collection(collection).document(document_id).set(data)
            
            logger.debug(f"Stored document {document_id} in {collection}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            return False
    
    async def get_document(
        self,
        collection: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document from Firestore
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            Document data or None
        """
        if not self._initialized:
            return None
        
        try:
            doc = self.db.collection(collection).document(document_id).get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    async def update_document(
        self,
        collection: str,
        document_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update specific fields in a document
        
        Args:
            collection: Collection name
            document_id: Document ID
            updates: Fields to update
            
        Returns:
            Success status
        """
        if not self._initialized:
            return False
        
        try:
            # Add timestamp
            updates["updated_at"] = datetime.utcnow()
            
            # Update document
            self.db.collection(collection).document(document_id).update(updates)
            
            logger.debug(f"Updated document {document_id} in {collection}")
            return True
            
        except exceptions.NotFound:
            logger.warning(f"Document {document_id} not found in {collection}")
            return False
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    async def query_documents(
        self,
        collection: str,
        filters: List[tuple],
        order_by: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query documents with filters
        
        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            order_by: Field to order by
            limit: Maximum results
            
        Returns:
            List of documents
        """
        if not self._initialized:
            return []
        
        try:
            # Build query
            query = self.db.collection(collection)
            
            # Apply filters
            for field, operator, value in filters:
                query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            docs = query.get()
            
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            logger.error(f"Failed to query documents: {e}")
            return []
    
    # Agent-specific methods
    
    async def save_agent_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """Save agent state"""
        return await self.store_document("agents", f"{agent_id}_state", state)
    
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state"""
        return await self.get_document("agents", f"{agent_id}_state")
    
    async def save_observation(
        self,
        agent_id: str,
        observation: Dict[str, Any]
    ) -> bool:
        """Save pool observation"""
        doc_id = f"{agent_id}_{datetime.utcnow().isoformat()}"
        return await self.store_document("observations", doc_id, observation)
    
    async def get_recent_observations(
        self,
        agent_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent observations"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        
        filters = [
            ("agent_id", "==", agent_id),
            ("timestamp", ">=", cutoff)
        ]
        
        return await self.query_documents(
            "observations",
            filters,
            order_by="timestamp",
            limit=100
        )
    
    async def save_memory_metadata(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Save memory metadata (actual content in Mem0)"""
        return await self.store_document("memories", memory_id, metadata)
    
    async def save_daily_summary(
        self,
        agent_id: str,
        summary: Dict[str, Any]
    ) -> bool:
        """Save daily summary"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        doc_id = f"{agent_id}_{date_str}"
        return await self.store_document("analytics", doc_id, summary)