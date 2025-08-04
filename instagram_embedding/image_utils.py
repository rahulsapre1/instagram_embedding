"""
Utilities for downloading and processing Instagram images.
"""
import os
import asyncio
from typing import List, Optional, Tuple
from pathlib import Path
import aiohttp
from PIL import Image
import io
from tqdm import tqdm

class ImageDownloader:
    def __init__(self, cache_dir: str = "data/images"):
        """
        Initialize image downloader with caching.
        
        Args:
            cache_dir: Directory to cache downloaded images
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        # Always use URL hash to avoid long filenames
        filename = str(abs(hash(url))) + ".jpg"
        return self.cache_dir / filename

    async def download_image(
        self, 
        url: str, 
        timeout: int = 30,
        size: Tuple[int, int] = (512, 512)  # CLIP v2 expects 512x512
    ) -> Optional[Image.Image]:
        """
        Download and process a single image.
        
        Args:
            url: Image URL to download
            timeout: Download timeout in seconds
            size: Target size to resize image to
            
        Returns:
            PIL Image or None if download/processing fails
        """
        try:
            # Check cache first
            cache_path = self._get_cache_path(url)
            if cache_path.exists():
                return self._process_image(Image.open(cache_path), size)

            # Download if not cached
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        print(f"Error downloading {url}: Status {response.status}")
                        return None
                    
                    data = await response.read()
                    image = Image.open(io.BytesIO(data))
                    
                    # Cache the original image
                    image.save(cache_path)
                    
                    # Process and return
                    return self._process_image(image, size)

        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None

    def _process_image(self, image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """
        Process image: convert to RGB and resize.
        
        Args:
            image: PIL Image to process
            size: Target size tuple (width, height)
            
        Returns:
            Processed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize with aspect ratio preservation
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Create new image with padding to exact size
        new_image = Image.new('RGB', size, (0, 0, 0))
        new_image.paste(
            image,
            ((size[0] - image.size[0]) // 2, 
             (size[1] - image.size[1]) // 2)
        )
        
        return new_image

    async def download_profile_images(
        self,
        profile_pic_url: str,
        post_urls: List[str],
        size: Tuple[int, int] = (512, 512)
    ) -> Tuple[Optional[Image.Image], List[Image.Image]]:
        """
        Download profile picture and post images for a profile.
        
        Args:
            profile_pic_url: URL of profile picture
            post_urls: List of post image URLs
            size: Target size for images
            
        Returns:
            Tuple of (profile_pic, list_of_post_images)
        """
        # Download profile picture
        profile_pic = await self.download_image(profile_pic_url, size=size)
        
        # Download post images sequentially
        post_images = []
        if post_urls:
            for url in post_urls:
                img = await self.download_image(url, size=size)
                if img is not None:
                    post_images.append(img)
            
        return profile_pic, post_images

    async def download_batch_profile_images(
        self,
        profile_data: List[dict],
        size: Tuple[int, int] = (512, 512)
    ) -> List[Tuple[Optional[Image.Image], List[Image.Image]]]:
        """
        Download images for a batch of profiles with progress tracking.
        
        Args:
            profile_data: List of profile dictionaries containing URLs
            size: Target size for images
            
        Returns:
            List of (profile_pic, post_images) tuples
        """
        results = []
        with tqdm(total=len(profile_data), desc="Downloading profile images") as pbar:
            for profile in profile_data:
                profile_pic_url = profile.get('profile_pic_url')
                post_urls = [
                    profile.get(f'post_{i}_url')
                    for i in range(12)
                    if profile.get(f'post_{i}_url')
                ]
                
                result = await self.download_profile_images(
                    profile_pic_url,
                    post_urls,
                    size=size
                )
                results.append(result)
                pbar.update(1)
                
        return results
