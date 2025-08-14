"""
Script to debug follower count updates.
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

async def get_follower_counts() -> Dict[str, int]:
    """Get all follower counts from Supabase."""
    supabase = SupabaseClient()
    converter = FollowerCountConverter()
    
    try:
        # Get all profiles
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('instagram_username, follower_count') \
            .execute()
            
        # Process results
        results = {}
        for profile in (response.data or []):
            if profile.get('instagram_username') and profile.get('follower_count'):
                username = profile['instagram_username'].strip()
                follower_count = converter.parse_follower_count(profile['follower_count'])
                if follower_count is not None:
                    results[username] = follower_count
                    print(f"Found in Supabase: '{username}' -> {follower_count:,} followers")
                    
        return results
        
    except Exception as e:
        print(f"Error fetching follower counts: {str(e)}")
        return {}

async def update_test_vectors():
    """Update test vectors with follower counts."""
    # Initialize clients
    qdrant = QdrantManager()
    
    try:
        # Get all follower counts
        print("Fetching follower counts from Supabase...")
        username_to_followers = await get_follower_counts()
        
        print(f"\nFound {len(username_to_followers)} usernames with follower counts")
        
        # Get test vectors
        print("\nFetching test vectors from Qdrant...")
        response = qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            limit=10,  # Just get a few vectors for testing
            with_payload=True,
            with_vectors=False
        )
        
        points, _ = response
        
        # Try to update vectors
        print("\nAttempting to update vectors:")
        print("-" * 50)
        
        for point in points:
            if point.payload and point.payload.get('username'):
                username = point.payload['username']
                print(f"\nChecking vector {point.id}:")
                print(f"Username in vector: '{username}'")
                
                if username in username_to_followers:
                    follower_count = username_to_followers[username]
                    print(f"✅ Found match! Follower count: {follower_count:,}")
                    
                    try:
                        qdrant.client.set_payload(
                            collection_name=qdrant.collection_name,
                            payload={'follower_count': follower_count},
                            points=[point.id]
                        )
                        print("✅ Successfully updated vector")
                    except Exception as e:
                        print(f"❌ Error updating vector: {str(e)}")
                else:
                    print("❌ No matching username found in Supabase")
                    # Print nearby matches for debugging
                    close_matches = [
                        u for u in username_to_followers.keys()
                        if username.lower() in u.lower() or u.lower() in username.lower()
                    ]
                    if close_matches:
                        print("Similar usernames in Supabase:")
                        for match in close_matches[:5]:
                            print(f"- '{match}'")
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await update_test_vectors()

if __name__ == "__main__":
    asyncio.run(main())