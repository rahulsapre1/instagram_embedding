"""
Image Processor for Hybrid Search
Downloads images from URLs and generates embeddings for search
"""

import asyncio
import logging
import requests
from typing import Optional, List
from PIL import Image
import io
import numpy as np
import os
import sys

# Add parent directory to path to import from instagram_embedding
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from instagram_embedding.embedder import CLIPEmbedder

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Processes images from URLs and generates embeddings for hybrid search
    """
    
    def __init__(self):
        self.clip_embedder = CLIPEmbedder()
        self.timeout = 30  # seconds for image download
    
    async def get_embedding_from_url(self, image_url: str) -> Optional[List[float]]:
        """
        Download image from URL and generate embedding
        
        Args:
            image_url: URL of the image to process
            
        Returns:
            Image embedding vector or None if failed
        """
        try:
            # Download image
            image = await self._download_image(image_url)
            if image is None:
                return None
            
            # Generate embedding using Instagram image processor
            embedding = self._generate_embedding(image)
            
            logger.info(f"Successfully generated embedding for image: {image_url}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error processing image from URL {image_url}: {str(e)}")
            return None
    
    async def _download_image(self, image_url: str) -> Optional[Image.Image]:
        """
        Download image from URL
        
        Args:
            image_url: URL to download from
            
        Returns:
            PIL Image object or None if failed
        """
        try:
            # Use aiohttp for async download if available, fallback to requests
            try:
                import aiohttp
                # Create session with SSL verification disabled for problematic URLs
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(image_url, timeout=self.timeout) as response:
                        if response.status != 200:
                            logger.error(f"Failed to download image: HTTP {response.status}")
                            return None
                        
                        image_data = await response.read()
                        
            except ImportError:
                # Fallback to requests with SSL verification disabled
                response = requests.get(image_url, timeout=self.timeout, verify=False)
                if response.status_code != 200:
                    logger.error(f"Failed to download image: HTTP {response.status_code}")
                    return None
                
                image_data = response.content
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"Successfully downloaded image: {image.size} {image.mode}")
            return image
            
        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {str(e)}")
            return None
    
    def _generate_embedding(self, image: Image.Image) -> Optional[List[float]]:
        """
        Generate embedding for the given image
        
        Args:
            image: PIL Image object
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            # Use the CLIP embedder to generate embedding
            # This should match the same embedding method used for profile images
            embeddings = self.clip_embedder.embed_images([image], output_dim=128)
            
            if not embeddings or len(embeddings) == 0:
                logger.error("Failed to generate embedding from CLIP embedder")
                return None
            
            # Get the first (and only) embedding
            embedding = embeddings[0]
            
            # Ensure embedding is a 1D array/list
            if isinstance(embedding, np.ndarray):
                if embedding.ndim > 1:
                    # Flatten if it's 2D or higher
                    embedding = embedding.flatten()
                embedding = embedding.tolist()
            
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def validate_image_url(self, image_url: str) -> bool:
        """
        Validate if image URL is accessible and contains valid image
        
        Args:
            image_url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if URL is accessible with SSL verification disabled
            response = requests.head(image_url, timeout=10, verify=False)
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
    
    def get_image_info(self, image: Image.Image) -> dict:
        """
        Get basic information about the image
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with image information
        """
        return {
            'size': image.size,
            'mode': image.mode,
            'format': getattr(image, 'format', 'Unknown'),
            'width': image.width,
            'height': image.height
        }


async def test_image_processor():
    """Test the image processor with the demo URL"""
    processor = ImageProcessor()
    
    # Test URL from requirements
    test_url = "https://seniorsinmelbourne.com.au/wp-content/uploads/2024/03/City_Circle_Tram_Melbourne-25.jpg"
    
    print(f"Testing image processor with URL: {test_url}")
    
    # Validate URL
    is_valid = await processor.validate_image_url(test_url)
    print(f"URL validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    if is_valid:
        # Download and process image
        embedding = await processor.get_embedding_from_url(test_url)
        if embedding:
            print(f"✅ Successfully generated embedding: {len(embedding)} dimensions")
            print(f"First 5 values: {embedding[:5]}")
        else:
            print("❌ Failed to generate embedding")
    else:
        print("❌ Cannot proceed with invalid URL")


if __name__ == "__main__":
    asyncio.run(test_image_processor()) 