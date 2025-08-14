"""
Script to update full names in Qdrant vectors using data from Supabase.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient

load_dotenv()

async def fetch_full_names_batch(supabase: SupabaseClient, usernames: List[str]) -> Dict[str, str]:
    """
    Fetch full names for a batch of usernames from Supabase.
    
    Args:
        supabase: Supabase client instance
        usernames: List of usernames to look up
        
    Returns:
        Dictionary mapping usernames to full names
    """
    try:
        # Use .in_() filter to fetch multiple profiles at once
        response = supabase.client.table('ig_profile_info_v0_0') \
            .select('username, full_name') \
            .in_('username', usernames) \
            .execute()
            
        # Create username to full_name mapping
        return {
            profile['username']: profile.get('full_name', '')
            for profile in (response.data or [])
            if profile.get('username')
        }
    except Exception as e:
        print(f"Error fetching full names from Supabase: {str(e)}")
        return {}

async def update_full_names(batch_size: int = 100):
    """
    Update full names for all profiles in Qdrant.
    
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
            
        print(f"\n🔍 Processing {total_points} points in batches of {batch_size}")
        
        # Process in batches
        offset = None
        processed = 0
        updated = 0
        failed = 0
        
        with tqdm(total=total_points, desc="Updating full names") as pbar:
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
                        
                    # Extract usernames that need updating (including empty strings)
                    # Extract usernames that need updating
                    points_to_update = [
                        point for point in points
                        if point.payload.get('username')  # Only process points with usernames
                    ]
                    
                    usernames_to_update = [
                        point.payload['username'] for point in points_to_update
                    ]
                    
                    if usernames_to_update:
                        print(f"\nFound {len(usernames_to_update)} usernames to update in current batch")
                        print(f"Sample usernames: {usernames_to_update[:3]}")
                        
                        # Fetch full names from Supabase
                        username_to_full_name = await fetch_full_names_batch(
                            supabase,
                            usernames_to_update
                        )
                        
                        print(f"Found {len(username_to_full_name)} matches in Supabase")
                        if username_to_full_name:
                            print(f"Sample full names: {list(username_to_full_name.items())[:3]}")
                        
                        # Update points in Qdrant
                        for point in points_to_update:
                            username = point.payload['username']
                            if username in username_to_full_name:
                                try:
                                    full_name = username_to_full_name[username]
                                    if full_name and full_name.strip():  # Only update if we got a non-empty full name
                                        print(f"\nUpdating {username} with full name: {full_name}")
                                        qdrant.client.set_payload(
                                            collection_name=qdrant.collection_name,
                                            payload={'full_name': full_name.strip()},
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
    await update_full_names()

if __name__ == "__main__":
    asyncio.run(main())