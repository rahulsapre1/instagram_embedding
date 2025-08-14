"""
Script to find matching usernames between Qdrant and Supabase.
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

async def get_all_usernames():
    """Get all usernames from both Qdrant and Supabase."""
    # Initialize clients
    qdrant = QdrantManager()
    supabase = SupabaseClient()
    
    try:
        # Get all Qdrant usernames
        qdrant_usernames = set()
        offset = None
        while True:
            response = qdrant.client.scroll(
                collection_name=qdrant.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, offset = response
            if not points:
                break
                
            for point in points:
                if point.payload and point.payload.get('username'):
                    qdrant_usernames.add(point.payload['username'])
                    
            if offset is None:
                break
                
        # Get all Supabase usernames
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('instagram_username') \
            .execute()
            
        supabase_usernames = set()
        for profile in response.data:
            if profile.get('instagram_username'):
                username = profile['instagram_username'].strip()
                supabase_usernames.add(username)
                
        # Find matches
        matches = qdrant_usernames.intersection(supabase_usernames)
        
        print(f"\nTotal usernames in Qdrant: {len(qdrant_usernames)}")
        print(f"Total usernames in Supabase: {len(supabase_usernames)}")
        print(f"Total matches: {len(matches)}")
        
        print("\nSample Qdrant usernames:")
        print("-" * 50)
        for username in list(qdrant_usernames)[:10]:
            print(username)
            
        print("\nSample Supabase usernames:")
        print("-" * 50)
        for username in list(supabase_usernames)[:10]:
            print(username)
            
        print("\nSample matches:")
        print("-" * 50)
        for username in list(matches)[:10]:
            print(username)
            
        # Get follower counts for matches
        if matches:
            print("\nGetting follower counts for matches:")
            print("-" * 50)
            converter = FollowerCountConverter()
            
            for username in list(matches)[:10]:
                response = supabase.client.table('ig_profile_raw_v0_2') \
                    .select('instagram_username, follower_count') \
                    .eq('instagram_username', username) \
                    .execute()
                    
                if response.data:
                    follower_count_text = response.data[0].get('follower_count')
                    follower_count = converter.parse_follower_count(follower_count_text) if follower_count_text else None
                    print(f"Username: {username}")
                    print(f"Follower Count (raw): {follower_count_text}")
                    print(f"Follower Count (parsed): {follower_count:,}" if follower_count else "Follower Count (parsed): None")
                    print("-" * 30)
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await get_all_usernames()

if __name__ == "__main__":
    asyncio.run(main())