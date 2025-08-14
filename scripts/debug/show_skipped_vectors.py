"""
Script to show examples of vectors that were skipped during follower count update.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient

load_dotenv()

async def get_supabase_usernames() -> set:
    """Get all usernames from Supabase."""
    supabase = SupabaseClient()
    response = supabase.client.table('ig_profile_raw_v0_2') \
        .select('instagram_username') \
        .execute()
        
    return {p['instagram_username'].strip() for p in response.data if p.get('instagram_username')}

async def show_skipped_vectors(limit: int = 10):
    """
    Show examples of vectors that were skipped.
    
    Args:
        limit: Number of examples to show
    """
    # Initialize clients
    qdrant = QdrantManager()
    
    try:
        # Get all Supabase usernames
        print("Fetching Supabase usernames...")
        supabase_usernames = await get_supabase_usernames()
        
        # Get vectors from Qdrant
        print("\nFetching vectors from Qdrant...")
        response = qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            limit=100,  # Get a batch of vectors
            with_payload=True,
            with_vectors=False
        )
        
        points, _ = response
        
        # Find skipped vectors
        skipped = []
        for point in points:
            if point.payload and point.payload.get('username'):
                username = point.payload['username']
                if username not in supabase_usernames:
                    skipped.append({
                        'id': point.id,
                        'username': username,
                        'payload': point.payload
                    })
                    
                if len(skipped) >= limit:
                    break
        
        # Print results
        print(f"\nFound {len(skipped)} skipped vectors (showing first {limit}):")
        print("-" * 50)
        for i, vector in enumerate(skipped, 1):
            print(f"\n{i}. Vector ID: {vector['id']}")
            print(f"   Username: {vector['username']}")
            print(f"   Full Name: {vector['payload'].get('full_name', 'N/A')}")
            print(f"   User ID: {vector['payload'].get('user_id', 'N/A')}")
            print(f"   Is Private: {vector['payload'].get('is_private', 'N/A')}")
            print(f"   Follower Count: {vector['payload'].get('follower_count', 'N/A')}")
            print("-" * 30)
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await show_skipped_vectors()

if __name__ == "__main__":
    asyncio.run(main())