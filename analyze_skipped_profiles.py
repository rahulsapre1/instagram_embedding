"""
Script to analyze profiles that were skipped during follower count update.
"""
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from instagram_embedding.qdrant_utils import QdrantManager
from instagram_embedding.supabase_utils import SupabaseClient

load_dotenv()

async def analyze_skipped_profiles():
    """Analyze profiles that were skipped during follower count update."""
    # Initialize clients
    qdrant = QdrantManager()
    supabase = SupabaseClient()
    
    try:
        # Get all Supabase usernames
        print("Fetching usernames from Supabase...")
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('instagram_username') \
            .execute()
            
        supabase_usernames = set()
        for profile in response.data:
            if profile.get('instagram_username'):
                username = profile['instagram_username'].strip()
                supabase_usernames.add(username.lower())  # Convert to lowercase for case-insensitive comparison
                
        print(f"\nFound {len(supabase_usernames)} unique usernames in Supabase")
        
        # Get all Qdrant usernames
        print("\nFetching profiles from Qdrant...")
        qdrant_profiles = []
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
                    qdrant_profiles.append({
                        'id': point.id,
                        'username': point.payload['username'],
                        'full_name': point.payload.get('full_name', 'N/A'),
                        'user_id': point.payload.get('user_id', 'N/A')
                    })
                    
            if offset is None:
                break
                
        print(f"Found {len(qdrant_profiles)} profiles in Qdrant")
        
        # Analyze skipped profiles
        skipped = []
        categories = {
            'partial_match': [],  # Username is part of another username
            'case_mismatch': [],  # Same username but different case
            'no_match': []        # No similar username found
        }
        
        for profile in qdrant_profiles:
            username = profile['username'].lower()
            if username not in supabase_usernames:
                skipped.append(profile)
                
                # Check for case mismatch
                if any(u.lower() == username for u in supabase_usernames):
                    categories['case_mismatch'].append(profile)
                # Check for partial match
                elif any(username in u or u in username for u in supabase_usernames):
                    categories['partial_match'].append(profile)
                else:
                    categories['no_match'].append(profile)
                    
        print(f"\nSkipped Profiles Analysis:")
        print("-" * 50)
        print(f"Total skipped: {len(skipped)}")
        print("\nBreakdown by category:")
        for category, profiles in categories.items():
            print(f"{category}: {len(profiles)} profiles")
            
        # Print examples from each category
        for category, profiles in categories.items():
            if profiles:
                print(f"\nSample of {category} profiles:")
                print("-" * 50)
                for profile in profiles[:5]:
                    print(f"ID: {profile['id']}")
                    print(f"Username: {profile['username']}")
                    print(f"Full Name: {profile['full_name']}")
                    print(f"User ID: {profile['user_id']}")
                    
                    if category in ['partial_match', 'case_mismatch']:
                        # Show similar usernames
                        username = profile['username'].lower()
                        similar = [u for u in supabase_usernames if (
                            category == 'case_mismatch' and u.lower() == username
                        ) or (
                            category == 'partial_match' and (username in u or u in username)
                        )]
                        if similar:
                            print("Similar usernames in Supabase:")
                            for s in similar[:3]:
                                print(f"- {s}")
                    print("-" * 30)
        
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    """Main entry point."""
    await analyze_skipped_profiles()

if __name__ == "__main__":
    asyncio.run(main())