"""
Script to add account type (human/brand) to each vector's payload from Supabase.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient

load_dotenv()

def normalize_account_type(account_type: str) -> str:
    """
    Normalize account type to human, brand, or unknown.
    
    Args:
        account_type: Raw account type from database
        
    Returns:
        Normalized account type: 'human', 'brand', or 'unknown'
    """
    if not account_type:
        return 'unknown'
    
    # Convert to lowercase and strip whitespace
    normalized = account_type.lower().strip()
    
    if normalized in ['human', 'person', 'individual', 'personal']:
        return 'human'
    elif normalized in ['brand', 'business', 'company', 'organization', 'corporate']:
        return 'brand'
    else:
        return 'unknown'

async def fetch_all_account_types(supabase: SupabaseClient) -> Dict[int, str]:
    """
    Fetch all account types from Supabase using pagination.
    
    Args:
        supabase: Supabase client instance
        
    Returns:
        Dictionary mapping user_id to account_type
    """
    try:
        # Get total count
        response = supabase.client.table('ig_profile_merged_v0_1') \
            .select('*', count='exact') \
            .execute()
            
        total_count = response.count
        print(f"\nTotal profiles in ig_profile_merged_v0_1: {total_count}")
        
        # Fetch profiles in batches
        batch_size = 1000
        results = {}
        
        for offset in range(0, total_count, batch_size):
            print(f"\nFetching batch starting at offset {offset}...")
            response = supabase.client.table('ig_profile_merged_v0_1') \
                .select('user_id, account_type') \
                .range(offset, offset + batch_size - 1) \
                .execute()
                
            # Process batch
            for profile in response.data:
                if profile.get('user_id') is not None:
                    user_id = profile['user_id']
                    account_type = normalize_account_type(profile.get('account_type'))
                    results[user_id] = account_type
                        
            print(f"Processed {len(response.data)} profiles")
            print(f"Current total unique user_ids: {len(results)}")
                    
        return results
        
    except Exception as e:
        print(f"Error fetching account types: {str(e)}")
        return {}

async def update_account_types(batch_size: int = 100):
    """
    Update account types for all vectors in Qdrant based on user_id.
    
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
        print("\n🔍 Fetching account types from Supabase...")
        
        # Get all account types
        user_id_to_account_type = await fetch_all_account_types(supabase)
        
        if not user_id_to_account_type:
            print("No account types found in Supabase")
            return
            
        print(f"\nFound {len(user_id_to_account_type)} user_ids with account types")
        print("\n🔄 Processing points to add account types...")
        
        # Process in batches
        offset = None
        processed = 0
        updated = 0
        failed = 0
        skipped = 0
        
        # Track account type distribution
        type_counts = {
            'human': 0,
            'brand': 0,
            'unknown': 0
        }
        
        with tqdm(total=total_points, desc="Adding account types") as pbar:
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
                        
                    # Process points that have user_id
                    for point in points:
                        if point.payload and point.payload.get('user_id') is not None:
                            try:
                                user_id = point.payload['user_id']
                                if user_id in user_id_to_account_type:
                                    account_type = user_id_to_account_type[user_id]
                                    
                                    # Update the point with account type
                                    qdrant.client.set_payload(
                                        collection_name=qdrant.collection_name,
                                        payload={'account_type': account_type},
                                        points=[point.id]
                                    )
                                    
                                    # Track counts
                                    type_counts[account_type] += 1
                                    updated += 1
                                    
                                    # Print some examples
                                    if updated <= 10:  # Only print first 10 for brevity
                                        username = point.payload.get('username', 'unknown')
                                        print(f"\nUpdated {username} (user_id: {user_id}): {account_type}")
                                    
                                else:
                                    skipped += 1
                                    
                            except Exception as e:
                                print(f"\nError updating point {point.id}: {str(e)}")
                                failed += 1
                        else:
                            skipped += 1
                    
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
        print(f"  - Skipped: {skipped}")
        
        # Print account type distribution
        if updated > 0:
            print(f"\n📊 Account Type Distribution:")
            print("-" * 50)
            
            for account_type, count in type_counts.items():
                percentage = (count / updated) * 100
                print(f"{account_type.capitalize():7} ({count:5} profiles): {percentage:6.2f}%")
                
            # Print some examples for each type
            print(f"\n🔍 Examples by account type:")
            print("-" * 50)
            
            # Get examples for each type
            for account_type in ['human', 'brand', 'unknown']:
                if type_counts[account_type] > 0:
                    print(f"\n{account_type.upper()} ACCOUNTS:")
                    
                    # Get a few examples
                    response = qdrant.client.scroll(
                        collection_name=qdrant.collection_name,
                        limit=10,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    examples = []
                    for point in response[0]:
                        if (point.payload.get('account_type') == account_type and 
                            point.payload.get('username') and 
                            point.payload.get('user_id') is not None):
                            examples.append({
                                'username': point.payload['username'],
                                'user_id': point.payload['user_id']
                            })
                            if len(examples) >= 3:
                                break
                    
                    for example in examples:
                        print(f"  • {example['username']} (user_id: {example['user_id']})")
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await update_account_types()

if __name__ == "__main__":
    asyncio.run(main()) 