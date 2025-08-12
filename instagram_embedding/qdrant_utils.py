"""
Qdrant vector database integration for storing and searching Instagram profile embeddings.
"""
import os
import time
from typing import List, Dict, Optional, Union, Tuple, Any
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

class QdrantManager:
    def __init__(
        self,
        collection_name: str = "instagram_profiles",
        vector_size: int = 128,
        max_retries: int = 5,
        retry_delay: int = 2
    ):
        """
        Initialize Qdrant client and ensure collection exists.
        
        Args:
            collection_name: Name of the collection to use
            vector_size: Dimension of vectors to store
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        self.url = os.getenv("QDRANT_HOST", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        
        self.client = self._initialize_client(max_retries, retry_delay)
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Create collections for different vector types
        self._create_collections()
        
    def _initialize_client(self, max_retries: int, retry_delay: int) -> QdrantClient:
        """Initialize Qdrant client with retries."""
        for attempt in range(max_retries):
            try:
                client_kwargs = {
                    "url": self.url,
                    "timeout": 10.0
                }
                
                if self.api_key:
                    client_kwargs["api_key"] = self.api_key
                
                client = QdrantClient(**client_kwargs)
                client.get_collections()
                return client
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ConnectionError(
                        f"Failed to connect to Qdrant after {max_retries} attempts: {str(e)}"
                    )
                print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
        
        raise ConnectionError("Failed to initialize Qdrant client")

    def _create_collections(self):
        """Create collections for different vector types."""
        collection_name = self.collection_name
        try:
            exists = any(
                c.name == collection_name 
                for c in self.client.get_collections().collections
            )
            
            if not exists:
                print(f"Creating collection {collection_name}...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=0
                    )
                )
                
                # Create payload indices
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="username",
                    field_schema="keyword"
                )
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="user_id",
                    field_schema="integer"
                )
                
                print(f"Collection {collection_name} created successfully!")
                
        except Exception as e:
            raise Exception(f"Failed to create collection {collection_name}: {str(e)}")

    def profile_exists(self, profile_id: int) -> bool:
        """
        Check if a profile already exists in the database.
        
        Args:
            profile_id: Unique identifier for the profile
            
        Returns:
            True if profile exists, False otherwise
        """
        try:
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=profile_id)
                        )
                    ]
                ),
                limit=1
            )
            return len(response[0]) > 0
        except Exception as e:
            print(f"Error checking profile existence: {str(e)}")
            return False

    def store_profile_vectors(
        self,
        profile_id: int,
        metadata: Dict,
        combined_vector: np.ndarray,
        skip_existing: bool = True
    ) -> Dict[str, bool]:
        """
        Store the combined vector for a profile.
        
        Args:
            profile_id: Unique identifier for the profile
            metadata: Profile metadata
            combined_vector: Combined embedding vector
            skip_existing: If True, skip profiles that already exist
            
        Returns:
            Dictionary with results and skip status
        """
        results = {"stored": False, "skipped": False}
        
        # Check if profile exists and should be skipped
        if skip_existing and self.profile_exists(profile_id):
            print(f"Profile {profile_id} already exists, skipping...")
            results["skipped"] = True
            return results
        
        # Store combined vector
        results["stored"] = self._store_vector(
            self.collection_name,
            profile_id,
            combined_vector,
            metadata
        )
            
        return results

    def _store_vector(
        self,
        collection_name: str,
        profile_id: int,
        vector: np.ndarray,
        metadata: Dict
    ) -> bool:
        """Store a single vector."""
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=profile_id,
                        vector=vector.reshape(-1).tolist() if isinstance(vector, np.ndarray) else vector.tolist(),
                        payload=metadata
                    )
                ],
                wait=True
            )
            return True
        except Exception as e:
            print(f"Error storing vector in {collection_name}: {str(e)}")
            return False

    def _store_vectors_batch(
        self,
        collection_name: str,
        profile_id: int,
        vectors: List[np.ndarray],
        metadata: Dict
    ) -> bool:
        """Store multiple vectors for the same profile."""
        try:
            points = [
                PointStruct(
                    id=int(f"{profile_id}{i:02d}"),  # Unique ID for each vector (e.g., 12345600, 12345601)
                    vector=vec.reshape(-1).tolist() if isinstance(vec, np.ndarray) else vec.tolist(),
                    payload={
                        **metadata,
                        "vector_index": i  # Track order of vectors
                    }
                )
                for i, vec in enumerate(vectors)
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True
            )
            return True
        except Exception as e:
            print(f"Error storing vectors in {collection_name}: {str(e)}")
            return False

    def search_similar(
        self,
        query_vector: np.ndarray,
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar vectors in the collection.
        
        Args:
            query_vector: Query embedding
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Optional filtering conditions
            
        Returns:
            List of similar profiles with scores
        """
        collection_name = self.collection_name
        
        search_params = models.SearchParams(
            hnsw_ef=128,
            exact=False
        )
        
        filter_query = None
        if filter_conditions:
            filter_query = models.Filter(
                must=[
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                    for key, value in filter_conditions.items()
                ]
            )
        
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=score_threshold,
                search_params=search_params,
                query_filter=filter_query
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "metadata": hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            print(f"Error searching in {collection_name}: {str(e)}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status,
                "optimizer_status": str(collection_info.optimizer_status)
            }
        except Exception as e:
            print(f"Error getting info for {self.collection_name}: {str(e)}")
            return {}
            
    def remove_profile_pic_url(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Remove profile_pic_url field from all records in the collection.
        
        Args:
            batch_size: Number of records to process in each batch
            
        Returns:
            Dictionary with count of processed and failed records
        """
        results = {"processed": 0, "failed": 0}
        offset = None
        
        try:
            while True:
                # Get batch of points
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, offset = response
                if not points:
                    break
                    
                # Process each point in the batch
                for point in points:
                    try:
                        # Remove profile_pic_url from payload
                        self.client.set_payload(
                            collection_name=self.collection_name,
                            payload={
                                'profile_pic_url': None  # This will remove the field
                            },
                            points=[point.id]
                        )
                        results["processed"] += 1
                    except Exception as e:
                        print(f"Error processing point {point.id}: {str(e)}")
                        results["failed"] += 1
                
                if offset is None:
                    break
                    
            return results
            
        except Exception as e:
            print(f"Error in remove_profile_pic_url: {str(e)}")
            return results