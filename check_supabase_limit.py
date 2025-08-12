"""
Script to check if Supabase is returning all profiles.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient

def check_table():
    """Check if we can get all profiles from Supabase."""
    # Initialize Supabase client
    supabase = SupabaseClient()
    
    try:
        print("Fetching all profiles from ig_profile_raw_v0_2...")
        
        # First, try to get a count
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('*', count='exact') \
            .execute()
            
        total_count = response.count
        print(f"\nTotal count reported by Supabase: {total_count}")
        
        # Now try different batch sizes
        batch_sizes = [100, 500, 1000, 2000, 3000, 5000]
        for size in batch_sizes:
            print(f"\nTrying batch size: {size}")
            response = supabase.client.table('ig_profile_raw_v0_2') \
                .select('instagram_username, follower_count') \
                .limit(size) \
                .execute()
                
            print(f"Profiles returned: {len(response.data)}")
            if response.data:
                print("Sample usernames:")
                for profile in response.data[:3]:
                    print(f"- {profile.get('instagram_username')}")
                    
        # Try without limit to get all profiles
        print("\nTrying to get all profiles without limit...")
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('instagram_username, follower_count') \
            .execute()
            
        print(f"Total profiles returned: {len(response.data)}")
        if response.data:
            print("\nFirst 3 profiles:")
            for profile in response.data[:3]:
                print(f"Username: {profile.get('instagram_username')}")
                print(f"Follower Count: {profile.get('follower_count')}")
                print("-" * 30)
                
            print("\nLast 3 profiles:")
            for profile in response.data[-3:]:
                print(f"Username: {profile.get('instagram_username')}")
                print(f"Follower Count: {profile.get('follower_count')}")
                print("-" * 30)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    check_table()