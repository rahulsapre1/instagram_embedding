"""
Main processing pipeline for Instagram profile embedding generation and storage.
"""
import os
import asyncio
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.supabase_utils import SupabaseClient
from instagram_embedding.image_utils import ImageDownloader
from instagram_embedding.embedder import CLIPEmbedder
from instagram_embedding.qdrant_utils import QdrantManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InstagramEmbeddingPipeline:
    def __init__(self):
        """Initialize pipeline components."""
        self.supabase = SupabaseClient()
        self.image_downloader = ImageDownloader()
        self.embedder = CLIPEmbedder()
        self.qdrant = QdrantManager()
        
        # Configuration
        self.batch_size = int(os.getenv('BATCH_SIZE', 32))
        self.vector_dim = int(os.getenv('VECTOR_DIM', 128))

    async def process_profile(
        self,
        profile: Dict,
        skip_existing: bool = True
    ) -> Optional[Dict]:
        """
        Process a single profile through the pipeline.
        
        Args:
            profile: Profile data dictionary
            skip_existing: Whether to skip if profile exists in Qdrant
            
        Returns:
            Dictionary with profile data and embeddings if successful
        """
        try:
            profile_id = profile.get('user_id')
            print(f"\n🔍 Processing Profile: {profile_id}")
            print("=" * 50)
            
            # Skip if already exists
            if skip_existing:
                print("\n📊 Checking if profile exists in Qdrant...")
                if self.qdrant.profile_exists(profile_id):
                    print(f"⏭️  Profile {profile_id} already exists, skipping...")
                    return {"skipped": True, "profile_id": profile_id}
                print("✅ Profile not found in Qdrant, proceeding...")
            
            # Download images
            print("\n📥 Downloading Images")
            print("-" * 30)
            post_urls = self.supabase.extract_post_urls(profile)
            print(f"Found {len(post_urls)} post URLs to download")
            
            profile_pic, post_images = await self.image_downloader.download_profile_images(
                profile['profile_pic_url_hd'],
                post_urls
            )
            
            if not profile_pic and not post_images:
                print("⚠️  Warning: No images downloaded")
            else:
                print("Download Results:")
                print(f"  - Profile Picture: {'✅ Downloaded' if profile_pic else '❌ Failed'}")
                print(f"  - Post Images: {len(post_images)} downloaded successfully")
            
            # Get text content
            print("\n📝 Extracting Text Content")
            print("-" * 30)
            captions = self.supabase.extract_captions(profile)
            bio = self.supabase.extract_bio(profile)
            
            print(f"Found {len(captions)} captions")
            if bio:
                print("Bio found and extracted")
            else:
                print("No bio available")
            
            # Generate embeddings
            print("\n🧮 Generating Embeddings")
            print("-" * 30)
            print(f"Using vector dimension: {self.vector_dim}")
            
            embeddings = self.embedder.process_profile(
                profile_pic=profile_pic,
                post_images=post_images,
                captions=captions,
                bio=bio,
                output_dim=self.vector_dim
            )
            
            # Log which embeddings were generated
            print("\nEmbedding Generation Results:")
            for key, value in embeddings.items():
                if isinstance(value, list):
                    print(f"  ▪️ {key}: {len(value)} embeddings")
                    if len(value) > 0:
                        print(f"    - Shape: {value[0].shape}")
                else:
                    print(f"  ▪️ {key}: 1 embedding")
                    print(f"    - Shape: {value.shape}")
            
            # Prepare metadata
            print("\n📋 Preparing Metadata")
            print("-" * 30)
            metadata = {
                'username': profile.get('username'),
                'user_id': profile.get('user_id'),
                'full_name': profile.get('full_name'),
                'is_private': profile.get('is_private')
            }
            print("Metadata fields prepared:", ", ".join(metadata.keys()))
            
            # Store vectors separately
            print("\n💾 Storing Vectors in Qdrant")
            print("-" * 30)
            storage_results = self.qdrant.store_profile_vectors(
                profile_id=profile_id,
                metadata=metadata,
                combined_vector=embeddings.get('combined'),
                skip_existing=skip_existing
            )
            
            # Log storage results
            print("\nStorage Results:")
            if storage_results["skipped"]:
                print("⏭️  Profile was skipped (already exists)")
                return {"skipped": True, "profile_id": profile_id}
            elif storage_results["stored"]:
                print("✅ Successfully stored profile vectors")
                print(f"\n✨ Successfully processed profile {profile_id}")
                return {
                    'profile_id': profile_id,
                    'embeddings': embeddings,
                    'metadata': metadata,
                    'storage_results': storage_results,
                    'skipped': False
                }
            else:
                print(f"\n❌ Failed to store vectors for profile {profile_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing profile {profile.get('user_id')}: {str(e)}")
            return None

    async def test_single_profile(self, profile_id: Optional[int] = None):
        """
        Test the pipeline on a single profile.
        
        Args:
            profile_id: Optional specific profile ID to process.
                      If None, gets the first profile from the database.
        """
        try:
            print("\n=== Starting Single Profile Test ===")
            print(f"Attempting to fetch {'specific profile ' + str(profile_id) if profile_id else 'first profile'}")
            
            # Get single profile
            if profile_id is not None:
                profiles = self.supabase.fetch_profiles(batch_size=1, offset=profile_id-1)
            else:
                profiles = self.supabase.fetch_profiles(batch_size=1, offset=0)
            
            if not profiles:
                logger.error("No profile found")
                print("❌ Error: No profile found in database")
                return
            
            profile = profiles[0]
            print("\n📋 Profile Details:")
            print(f"  - Username: {profile.get('username', 'N/A')}")
            print(f"  - User ID: {profile.get('user_id', 'N/A')}")
            print(f"  - Private: {profile.get('is_private', 'N/A')}")
            print(f"  - Has profile pic: {bool(profile.get('profile_pic_url_hd'))}")
            
            # Count valid posts
            post_count = sum(1 for i in range(12) if profile.get(f'post_{i}_url'))
            
            logger.info(f"Testing pipeline with profile: {profile.get('username', profile.get('user_id'))}")
            
            print("\n🔄 Starting profile processing...")
            # Process profile with detailed logging
            result = await self.process_profile(profile, skip_existing=False)
            
            if result:
                print("\n✅ Test completed successfully!")
                print("\nEmbedding Results:")
                for key, value in result['embeddings'].items():
                    print(f"  ▪️ {key}: 1 vector generated")
                    print(f"    - Vector shape: {value.shape}")
                    
                print("\nStorage Results:")
                for component, success in result['storage_results'].items():
                    status = "✅ Success" if success else "❌ Failed"
                    print(f"  ▪️ {component}: {status}")
            else:
                print("\n❌ Test failed - no results returned")
                logger.error("Test failed - no results returned")
                
        except Exception as e:
            logger.error(f"Test failed with error: {str(e)}")

    async def process_batch(
        self,
        profiles: List[Dict],
        skip_existing: bool = True
    ) -> List[Dict]:
        """Process a batch of profiles."""
        results = []
        
        for profile in tqdm(profiles, desc="Processing profiles"):
            result = await self.process_profile(profile, skip_existing)
            if result:
                results.append(result)
                
        return results

    async def run_pipeline(
        self,
        batch_size: Optional[int] = None,
        skip_existing: bool = True
    ):
        """Run the complete pipeline."""
        batch_size = batch_size or self.batch_size
        
        try:
            total = await self.supabase.get_total_profiles()
            logger.info(f"Found {total} profiles to process")
            
            processed = 0
            while processed < total:
                profiles = await self.supabase.fetch_profiles(
                    batch_size=batch_size,
                    offset=processed
                )
                
                if not profiles:
                    break
                
                results = await self.process_batch(profiles, skip_existing)
                processed += len(profiles)
                
                # Count successful and skipped profiles
                successful = sum(1 for r in results if r and not r.get('skipped', False))
                skipped = sum(1 for r in results if r and r.get('skipped', False))
                
                logger.info(
                    f"Processed {processed}/{total} profiles "
                    f"({successful} successful, {skipped} skipped)"
                )
                
            logger.info("Pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

async def main():
    """Main entry point."""
    pipeline = InstagramEmbeddingPipeline()
    
    # Run the full pipeline
    await pipeline.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())