"""
Script to check username matching between Qdrant and Supabase.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient

load_dotenv()

async def check_username(username: str):
    """
    Check a specific username in both Qdrant and Supabase.
    
    Args:
        username: Username to check
    """
    # Initialize clients
    qdrant = QdrantManager()
    supabase = SupabaseClient()
    
    try:
        print(f"\nChecking username: '{username}'")
        print("-" * 50)
        
        # Check in Qdrant
        print("\nQdrant data:")
        print("-" * 20)
        response = qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        
        points, _ = response
        qdrant_matches = []
        for point in points:
            if point.payload and point.payload.get('username') == username:
                qdrant_matches.append(point)
                
        if qdrant_matches:
            for i, point in enumerate(qdrant_matches, 1):
                print(f"\nMatch {i}:")
                print(f"Vector ID: {point.id}")
                print(f"Username: '{point.payload.get('username')}'")
                print(f"Full Name: {point.payload.get('full_name')}")
                print(f"User ID: {point.payload.get('user_id')}")
                print(f"Follower Count: {point.payload.get('follower_count', 'N/A')}")
        else:
            print("No matches found")
            
        # Check in Supabase
        print("\nSupabase data:")
        print("-" * 20)
        
        # Try exact match
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('*') \
            .eq('instagram_username', username) \
            .execute()
            
        if not response.data:
            # Try with leading/trailing spaces
            variations = [
                f" {username}",
                f"{username} ",
                f" {username} "
            ]
            for variation in variations:
                response = supabase.client.table('ig_profile_raw_v0_2') \
                    .select('*') \
                    .eq('instagram_username', variation) \
                    .execute()
                if response.data:
                    break
                    
        if response.data:
            for i, profile in enumerate(response.data, 1):
                print(f"\nMatch {i}:")
                print(f"ID: {profile.get('id')}")
                print(f"Username: '{profile.get('instagram_username')}'")
                print(f"Full Name: {profile.get('full_name_profile')}")
                print(f"Follower Count: {profile.get('follower_count')}")
                print(f"Profile URL: {profile.get('profile_url')}")
        else:
            print("No matches found")
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await check_username('nrl')

if __name__ == "__main__":
    asyncio.run(main())