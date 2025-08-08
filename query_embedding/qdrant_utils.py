"""
Qdrant vector database utilities for searching Instagram profile embeddings.
"""
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, SearchParams, Filter, FieldCondition, Range, MatchValue
from dotenv import load_dotenv
from query_embedding.follower_utils import FollowerCountConverter
from query_embedding.embedder import QueryEmbedder

# Load environment variables
load_dotenv()

class QdrantSearcher:
    def __init__(
        self,
        collection_name: str = "instagram_profiles",
        top_k: int = 20,
        score_threshold: float = 0.0
    ):
        """
        Initialize Qdrant client for searching profile embeddings.
        
        Args:
            collection_name: Name of the collection to search
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
        """
        self.client = QdrantClient(
            url=os.getenv("QDRANT_HOST", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = collection_name
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.embedder = QueryEmbedder()
    
    def build_filters(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """
        Build Qdrant filters from filter dictionary.
        
        Args:
            filters: Dictionary of filters
                - follower_count: Tuple[int, Optional[int]] for (min, max) range
                - account_type: str for exact match
        
        Returns:
            Qdrant Filter object or None if no filters
        """
        if not filters:
            return None
            
        conditions = []
        
        # Handle follower count range
        if "follower_count" in filters:
            min_followers, max_followers = filters["follower_count"]
            range_filter = {"gte": min_followers}
            if max_followers is not None:
                range_filter["lt"] = max_followers
            conditions.append(
                FieldCondition(
                    key="follower_count",
                    range=Range(**range_filter)
                )
            )
        
        # Handle account type
        if "account_type" in filters:
            conditions.append(
                FieldCondition(
                    key="account_type",
                    match=MatchValue(value=filters["account_type"])
                )
            )
        
        if not conditions:
            return None
            
        return Filter(must=conditions)
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List[models.ScoredPoint]:
        """
        Search for profiles using a natural language query.
        
        Args:
            query: Natural language query string
            filters: Optional dictionary of filters
                - follower_count: Tuple[int, Optional[int]] for (min, max) range
                - account_type: str for exact match
                - username: str for exact match
            offset: Starting offset for pagination
            limit: Maximum number of results to return (overrides top_k)
            
        Returns:
            List of scored points with payloads
        """
        # Get query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Build filter conditions
        conditions = []
        
        if filters:
            # Handle follower count range
            if "follower_count" in filters:
                min_followers, max_followers = filters["follower_count"]
                range_filter = {"gte": min_followers}
                if max_followers is not None:
                    range_filter["lt"] = max_followers
                conditions.append(
                    FieldCondition(
                        key="follower_count",
                        range=Range(**range_filter)
                    )
                )
            
            # Handle account type
            if "account_type" in filters:
                conditions.append(
                    FieldCondition(
                        key="account_type",
                        match=MatchValue(value=filters["account_type"])
                    )
                )
                
            # Handle username exact match
            if "username" in filters:
                conditions.append(
                    FieldCondition(
                        key="username",
                        match=MatchValue(value=filters["username"])
                    )
                )
        
        # Create filter object if conditions exist
        filter_obj = Filter(must=conditions) if conditions else None
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit or self.top_k,
            offset=offset,
            score_threshold=self.score_threshold,
            query_filter=filter_obj,
            with_vectors=True  # Include vectors in results
        )
        
        return results