"""
Script to update empty full names in Qdrant vectors using data from both Supabase tables.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient

load_dotenv()

async def fetch_full_names_batch(supabase: SupabaseClient, user_ids: List[int]) -> Dict[int, str]:
    """
    Fetch full names for a batch of user IDs from Supabase.
    
    Args:
        supabase: Supabase client instance
        user_ids: List of user IDs to look up
        
    Returns:
        Dictionary mapping user IDs to full names
    """
    try:
        # Try both tables to find full names
        response1 = supabase.client.table('ig_profile_info_v0_0') \
            .select('user_id, full_name') \
            .in_('user_id', user_ids) \
            .execute()
            
        response2 = supabase.client.table('ig_profile_merged_v0_1') \
            .select('user_id, full_name, bio') \
            .in_('user_id', user_ids) \
            .execute()
            
        # Process results
        results = {}
        
        # First try full names from info table
        for profile in (response1.data or []):
            if profile.get('user_id') and profile.get('full_name'):
                if profile['full_name'].strip():
                    results[profile['user_id']] = profile['full_name'].strip()
                    
        # Then try full names or bios from merged table
        for profile in (response2.data or []):
            if profile.get('user_id'):
                user_id = profile['user_id']
                if user_id not in results:  # Only use if we don't have a name yet
                    # Try full name first
                    if profile.get('full_name') and profile['full_name'].strip():
                        results[user_id] = profile['full_name'].strip()
                    # Fall back to bio if available
                    elif profile.get('bio') and profile['bio'].strip():
                        # Extract first line of bio
                        bio = profile['bio'].strip().split('\n')[0]
                        results[user_id] = bio
            
        return results
    except Exception as e:
        print(f"Error fetching full names from Supabase: {str(e)}")
        return {}

async def update_empty_full_names(batch_size: int = 100):
    """
    Update empty full names for profiles in Qdrant.
    
    Args:
        batch_size: Number of profiles to process in each batch
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
        print("\n🔍 Processing points to find those with empty full names...")
        
        # Process in batches
        offset = None
        processed = 0
        updated = 0
        failed = 0
        
        with tqdm(total=total_points, desc="Updating empty full names") as pbar:
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
                        
                    # Extract points that need full name updates
                    points_to_update = []
                    for point in points:
                        if point.payload:
                            # Check for missing or empty full names
                            full_name = point.payload.get('full_name')
                            user_id = point.payload.get('user_id')
                            if user_id and (full_name is None or full_name.strip() == ''):
                                points_to_update.append(point)
                    
                    if points_to_update:
                        user_ids = [point.payload['user_id'] for point in points_to_update]
                        print(f"\nFound {len(user_ids)} points with empty full names in current batch")
                        print(f"Sample user IDs: {user_ids[:3]}")
                        
                        # Fetch full names from Supabase
                        user_id_to_full_name = await fetch_full_names_batch(supabase, user_ids)
                        
                        print(f"Found {len(user_id_to_full_name)} matches in Supabase")
                        if user_id_to_full_name:
                            print(f"Sample mappings: {list(user_id_to_full_name.items())[:3]}")
                        
                        # Update points in Qdrant
                        for point in points_to_update:
                            user_id = point.payload['user_id']
                            if user_id in user_id_to_full_name:
                                try:
                                    full_name = user_id_to_full_name[user_id]
                                    print(f"\nUpdating user_id {user_id} with full name: {full_name}")
                                    qdrant.client.set_payload(
                                        collection_name=qdrant.collection_name,
                                        payload={'full_name': full_name},
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
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await update_empty_full_names()

if __name__ == "__main__":
    asyncio.run(main())