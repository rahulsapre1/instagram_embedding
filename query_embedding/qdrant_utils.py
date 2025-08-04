"""
Qdrant vector database utilities for searching Instagram profile embeddings.
"""
import os
from typing import List, Dict, Any
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, SearchParams
from dotenv import load_dotenv

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
            score_threshold: Minimum similarity score (0 to 1)
        """
        self.url = os.getenv("QDRANT_HOST", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name
        self.top_k = top_k
        self.score_threshold = score_threshold
        
        # Initialize client
        client_kwargs = {
            "url": self.url,
            "timeout": 10.0
        }
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
            
        self.client = QdrantClient(**client_kwargs)
        
        # Verify collection exists
        collections = self.client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            raise ValueError(f"Collection '{collection_name}' not found")

    def search_profiles(
        self,
        query_vector: np.ndarray,
        limit: int = None,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar profiles using a query vector.
        
        Args:
            query_vector: Query embedding vector
            limit: Optional override for number of results
            threshold: Optional override for score threshold
            
        Returns:
            List of matching profiles with similarity scores
        """
        try:
            # Set search parameters
            search_params = SearchParams(
                hnsw_ef=128,
                exact=False
            )
            
            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=limit or self.top_k,
                score_threshold=threshold or self.score_threshold,
                search_params=search_params
            )
            
            # Format results
            matches = []
            for hit in results:
                # Convert similarity score to percentage
                score_pct = round(hit.score * 100, 2)
                
                # Extract profile data
                profile = {
                    "username": hit.payload.get("username"),
                    "user_id": hit.payload.get("user_id"),
                    "full_name": hit.payload.get("full_name"),
                    "is_private": hit.payload.get("is_private"),
                    "profile_pic_url": hit.payload.get("profile_pic_url"),
                    "similarity_score": score_pct
                }
                matches.append(profile)
            
            return matches
            
        except Exception as e:
            print(f"Error searching profiles: {str(e)}")
            return []