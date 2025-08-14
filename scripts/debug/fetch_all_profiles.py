"""
Script to fetch all profiles from Supabase using pagination.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient

def fetch_all_profiles():
    """Fetch all profiles from Supabase using pagination."""
    # Initialize Supabase client
    supabase = SupabaseClient()
    
    try:
        print("Fetching all profiles from ig_profile_raw_v0_2...")
        
        # First, get the total count
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('*', count='exact') \
            .execute()
            
        total_count = response.count
        print(f"\nTotal count reported by Supabase: {total_count}")
        
        # Fetch profiles in batches
        batch_size = 1000
        all_profiles = []
        
        for offset in range(0, total_count, batch_size):
            print(f"\nFetching batch starting at offset {offset}...")
            response = supabase.client.table('ig_profile_raw_v0_2') \
                .select('instagram_username, follower_count') \
                .range(offset, offset + batch_size - 1) \
                .execute()
                
            batch_profiles = response.data
            all_profiles.extend(batch_profiles)
            print(f"Got {len(batch_profiles)} profiles")
            
            if batch_profiles:
                print("Sample from this batch:")
                for profile in batch_profiles[:3]:
                    print(f"- {profile.get('instagram_username')}: {profile.get('follower_count')}")
                    
        print(f"\nTotal profiles fetched: {len(all_profiles)}")
        
        # Print some statistics
        usernames = set(p['instagram_username'].strip().lower() for p in all_profiles if p.get('instagram_username'))
        print(f"Unique usernames: {len(usernames)}")
        
        print("\nFirst 3 profiles:")
        for profile in all_profiles[:3]:
            print(f"Username: {profile.get('instagram_username')}")
            print(f"Follower Count: {profile.get('follower_count')}")
            print("-" * 30)
            
        print("\nLast 3 profiles:")
        for profile in all_profiles[-3:]:
            print(f"Username: {profile.get('instagram_username')}")
            print(f"Follower Count: {profile.get('follower_count')}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    fetch_all_profiles()