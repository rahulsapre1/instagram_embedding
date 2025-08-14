"""
Script to add influencer type to each vector's payload based on follower count.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from query_embedding.follower_utils import FollowerCountConverter

load_dotenv()

def get_influencer_type(follower_count: int) -> str:
    """
    Determine influencer type based on follower count.
    
    Args:
        follower_count: Number of followers
        
    Returns:
        Influencer type: 'nano', 'micro', 'macro', or 'mega'
    """
    if follower_count < 1_000:
        return 'none'
    elif follower_count < 10_000:
        return 'nano'
    elif follower_count < 100_000:
        return 'micro'
    elif follower_count < 1_000_000:
        return 'macro'
    else:
        return 'mega'

async def update_influencer_types(batch_size: int = 100):
    """
    Update influencer types for all vectors in Qdrant based on their follower count.
    
    Args:
        batch_size: Number of vectors to process in each batch
    """
    # Initialize Qdrant client
    qdrant = QdrantManager()
    
    try:
        # Get collection info
        collection_info = qdrant.get_collection_info()
        total_points = collection_info.get('points_count', 0)
        
        if total_points == 0:
            print("No points found in Qdrant collection")
            return
            
        print(f"Found {total_points} points in collection")
        print("\n🔄 Processing points to add influencer types...")
        
        # Process in batches
        offset = None
        processed = 0
        updated = 0
        failed = 0
        skipped = 0
        
        # Track influencer type distribution
        type_counts = {
            'none': 0,
            'nano': 0,
            'micro': 0,
            'macro': 0,
            'mega': 0
        }
        
        with tqdm(total=total_points, desc="Adding influencer types") as pbar:
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
                        
                    # Process points that have follower counts
                    for point in points:
                        if point.payload and point.payload.get('follower_count') is not None:
                            try:
                                follower_count = point.payload['follower_count']
                                influencer_type = get_influencer_type(follower_count)
                                
                                # Update the point with influencer type
                                qdrant.client.set_payload(
                                    collection_name=qdrant.collection_name,
                                    payload={'influencer_type': influencer_type},
                                    points=[point.id]
                                )
                                
                                # Track counts
                                type_counts[influencer_type] += 1
                                updated += 1
                                
                                # Print some examples
                                if updated <= 10:  # Only print first 10 for brevity
                                    username = point.payload.get('username', 'unknown')
                                    print(f"\nUpdated {username}: {follower_count:,} followers → {influencer_type}")
                                
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
        
        # Print influencer type distribution
        if updated > 0:
            print(f"\n📊 Influencer Type Distribution:")
            print("-" * 50)
            
            for influencer_type, count in type_counts.items():
                percentage = (count / updated) * 100
                print(f"{influencer_type.capitalize():6} ({count:5} profiles): {percentage:6.2f}%")
                
            # Print some examples for each type
            print(f"\n🔍 Examples by type:")
            print("-" * 50)
            
            # Get examples for each type
            for influencer_type in ['none', 'nano', 'micro', 'macro', 'mega']:
                if type_counts[influencer_type] > 0:
                    print(f"\n{influencer_type.upper()} INFLUENCERS:")
                    
                    # Get a few examples
                    response = qdrant.client.scroll(
                        collection_name=qdrant.collection_name,
                        limit=5,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    examples = []
                    for point in response[0]:
                        if (point.payload.get('influencer_type') == influencer_type and 
                            point.payload.get('username') and 
                            point.payload.get('follower_count') is not None):
                            examples.append({
                                'username': point.payload['username'],
                                'followers': point.payload['follower_count']
                            })
                            if len(examples) >= 3:
                                break
                    
                    for example in examples:
                        print(f"  • {example['username']}: {example['followers']:,} followers")
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await update_influencer_types()

if __name__ == "__main__":
    asyncio.run(main()) 