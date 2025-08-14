"""
Script to update follower counts in Qdrant vectors using data from Supabase.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient
from query_embedding.follower_utils import FollowerCountConverter

load_dotenv()

async def fetch_all_follower_counts(supabase: SupabaseClient) -> Dict[str, int]:
    """
    Fetch all follower counts from Supabase using pagination.
    
    Args:
        supabase: Supabase client instance
        
    Returns:
        Dictionary mapping usernames to follower counts
    """
    try:
        # Get total count
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('*', count='exact') \
            .execute()
            
        total_count = response.count
        print(f"\nTotal profiles in Supabase: {total_count}")
        
        # Fetch profiles in batches
        batch_size = 1000
        results = {}
        converter = FollowerCountConverter()
        
        for offset in range(0, total_count, batch_size):
            print(f"\nFetching batch starting at offset {offset}...")
            response = supabase.client.table('ig_profile_raw_v0_2') \
                .select('instagram_username, follower_count') \
                .range(offset, offset + batch_size - 1) \
                .execute()
                
            # Process batch
            for profile in response.data:
                if profile.get('instagram_username') and profile.get('follower_count'):
                    username = profile['instagram_username'].strip()
                    follower_count = converter.parse_follower_count(profile['follower_count'])
                    if follower_count is not None:
                        results[username] = follower_count
                        
            print(f"Processed {len(response.data)} profiles")
            print(f"Current total unique usernames: {len(results)}")
                    
        return results
        
    except Exception as e:
        print(f"Error fetching follower counts: {str(e)}")
        return {}

async def update_follower_counts(batch_size: int = 100):
    """
    Update follower counts for all vectors in Qdrant.
    
    Args:
        batch_size: Number of vectors to process in each batch
    """
    # Initialize clients
    qdrant = QdrantManager()
    supabase = SupabaseClient()
    
    try:
        # Get collection info
        collection_info = qdrant.get_collection_info()
        total_points = collection_info.get('points_count', 0)
        
        if total_points == 0:
            print("No points found in Qdrant collection")
            return
            
        print(f"Found {total_points} points in collection")
        print("\n🔍 Fetching follower counts from Supabase...")
        
        # Get all follower counts
        username_to_followers = await fetch_all_follower_counts(supabase)
        
        if not username_to_followers:
            print("No follower counts found in Supabase")
            return
            
        print(f"\nFound {len(username_to_followers)} usernames with follower counts")
        print("\n🔄 Processing points to update follower counts...")
        
        # Process in batches
        offset = None
        processed = 0
        updated = 0
        failed = 0
        
        with tqdm(total=total_points, desc="Updating follower counts") as pbar:
            while True:
                try:
                    # Get batch of points
                    response = qdrant.client.scroll(
                        collection_name=qdrant.collection_name,
                        limit=batch_size,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    points, offset = response
                    if not points:
                        break
                        
                    # Extract points that need follower count updates
                    points_to_update = []
                    for point in points:
                        if point.payload and point.payload.get('username'):
                            points_to_update.append(point)
                    
                    if points_to_update:
                        # Update points in Qdrant
                        for point in points_to_update:
                            username = point.payload['username']
                            if username in username_to_followers:
                                try:
                                    follower_count = username_to_followers[username]
                                    print(f"\nUpdating {username} with follower count: {follower_count:,}")
                                    qdrant.client.set_payload(
                                        collection_name=qdrant.collection_name,
                                        payload={'follower_count': follower_count},
                                        points=[point.id]
                                    )
                                    updated += 1
                                except Exception as e:
                                    print(f"\nError updating point {point.id}: {str(e)}")
                                    failed += 1
                    
                    processed += len(points)
                    pbar.update(len(points))
                    
                    if offset is None:
                        break
                        
                except Exception as e:
                    print(f"\nError processing batch: {str(e)}")
                    failed += batch_size
                    if offset:
                        processed += batch_size
                        pbar.update(batch_size)
                    break
    
        print(f"\n✅ Successfully processed {processed} vectors")
        print(f"  - Updated: {updated}")
        print(f"  - Failed: {failed}")
        print(f"  - Skipped: {processed - updated - failed}")
        
        # Print follower count distribution
        if updated > 0:
            print("\n📊 Follower Count Distribution:")
            print("-" * 50)
            
            categories = {
                'none': 0,    # < 1K
                'nano': 0,    # 1K-10K
                'micro': 0,   # 10K-100K
                'macro': 0,   # 100K-1M
                'mega': 0     # > 1M
            }
            
            for follower_count in username_to_followers.values():
                if follower_count < 1_000:
                    categories['none'] += 1
                elif follower_count < 10_000:
                    categories['nano'] += 1
                elif follower_count < 100_000:
                    categories['micro'] += 1
                elif follower_count < 1_000_000:
                    categories['macro'] += 1
                else:
                    categories['mega'] += 1
                    
            for category, count in categories.items():
                percentage = (count / updated) * 100
                print(f"{category.capitalize():6} ({count:5} profiles): {percentage:6.2f}%")
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await update_follower_counts()

if __name__ == "__main__":
    asyncio.run(main())