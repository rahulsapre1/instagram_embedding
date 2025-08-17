"""
Hybrid Search Engine for Instagram Profiles
Combines image and text embeddings with dynamic weighting based on query intent
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import requests
from PIL import Image
import io
import numpy as np

from .embedder import QueryEmbedder
from .qdrant_utils import QdrantSearcher
from .weight_analyzer import WeightAnalyzer
from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    Hybrid search engine that combines image and text embeddings
    with dynamic weighting based on query intent
    """
    
    def __init__(self):
        self.query_embedder = QueryEmbedder()
        self.qdrant_searcher = QdrantSearcher()
        self.weight_analyzer = WeightAnalyzer()
        self.image_processor = ImageProcessor()
    
    async def search(self, image_url: str, text_query: str) -> Tuple[List, Dict[str, float]]:
        """
        Perform hybrid search combining image and text
        
        Args:
            image_url: URL of the image to search with
            text_query: Text query for search
            
        Returns:
            Tuple of (search_results, weights_used)
        """
        try:
            # Step 1: Analyze query intent and get weights
            weights = await self.weight_analyzer.get_weights(text_query)
            logger.info(f"Query weights: Image={weights['image_weight']}, Text={weights['text_weight']}")
            
            # Step 2: Process image and get embedding
            image_embedding = await self.image_processor.get_embedding_from_url(image_url)
            if image_embedding is None:
                raise ValueError(f"Failed to process image from URL: {image_url}")
            
            # Step 3: Generate text embedding
            text_embedding = self.query_embedder.embed_query(text_query)
            
            # Step 4: Create hybrid vector
            hybrid_vector = self._create_hybrid_vector(image_embedding, text_embedding, weights)
            
            # Step 5: Search Qdrant directly with the hybrid vector
            results = self.qdrant_searcher.search_with_vector(hybrid_vector, limit=20)
            
            return results, weights
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise
    
    def _create_hybrid_vector(self, image_embedding: List[float], 
                             text_embedding: List[float], 
                             weights: Dict[str, float]) -> List[float]:
        """
        Create weighted combination of image and text embeddings
        
        Args:
            image_embedding: Image vector
            text_embedding: Text vector  
            weights: Dictionary with 'image_weight' and 'text_weight'
            
        Returns:
            Hybrid vector combining both embeddings
        """
        if len(image_embedding) != len(text_embedding):
            raise ValueError("Image and text embeddings must have same dimensions")
        
        image_weight = weights['image_weight']
        text_weight = weights['text_weight']
        
        # Validate weights sum to 1.0
        if abs(image_weight + text_weight - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {image_weight} + {text_weight}")
        
        # Create weighted combination
        hybrid_vector = []
        for i in range(len(image_embedding)):
            weighted_sum = (image_weight * image_embedding[i] + 
                           text_weight * text_embedding[i])
            hybrid_vector.append(weighted_sum)
        
        return hybrid_vector
    
    async def validate_image_url(self, image_url: str) -> bool:
        """
        Validate if image URL is accessible and contains valid image
        
        Args:
            image_url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            response = requests.head(image_url, timeout=10)
            if response.status_code != 200:
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating image URL {image_url}: {str(e)}")
            return False


async def main():
    """Test function for hybrid search"""
    engine = HybridSearchEngine()
    
    # Test URL validation
    test_url = "https://seniorsinmelbourne.com.au/wp-content/uploads/2024/03/City_Circle_Tram_Melbourne-25.jpg"
    is_valid = await engine.validate_image_url(test_url)
    print(f"Image URL valid: {is_valid}")
    
    if is_valid:
        try:
            results, weights = await engine.search(test_url, "find similar profiles")
            print(f"Search completed with weights: {weights}")
            print(f"Found {len(results)} results")
        except Exception as e:
            print(f"Search failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 