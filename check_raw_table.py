"""
Script to check the contents of the ig_profile_raw_v0_2 table.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient
from query_embedding.follower_utils import FollowerCountConverter

def check_table():
    """Check table structure and contents."""
    # Initialize clients
    supabase = SupabaseClient()
    converter = FollowerCountConverter()
    
    try:
        # Get all profiles
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('instagram_username, follower_count') \
            .execute()
            
        # Print total count
        print(f"Total profiles in table: {len(response.data)}")
        
        print("\nFirst 5 profiles:")
        print("-" * 50)
        for profile in response.data[:5]:
            username = profile.get('instagram_username')
            follower_count_text = profile.get('follower_count')
            follower_count = converter.parse_follower_count(follower_count_text) if follower_count_text else None
            
            print(f"Username: {username}")
            print(f"Follower Count (raw): {follower_count_text}")
            print(f"Follower Count (parsed): {follower_count:,}" if follower_count else "Follower Count (parsed): None")
            print("-" * 30)
            
        # Print all unique usernames
        usernames = sorted(set(p.get('instagram_username', '').strip() for p in response.data if p.get('instagram_username')))
        print("\nAll unique usernames:")
        print("-" * 50)
        for username in usernames:
            print(username)
            
        # Check specific usernames
        test_usernames = ['nrl', 'kurtcoleman', 'paulpayasalad']
        print("\nChecking specific usernames:")
        print("-" * 50)
        for username in test_usernames:
            # Try different variations of the username
            variations = [
                username,
                f" {username}",
                f"{username} ",
                f" {username} ",
                username.lower(),
                f" {username.lower()}",
                f"{username.lower()} ",
                f" {username.lower()} ",
                username.upper(),
                f" {username.upper()}",
                f"{username.upper()} ",
                f" {username.upper()} "
            ]
            found = False
            for variation in variations:
                response = supabase.client.table('ig_profile_raw_v0_2') \
                    .select('instagram_username, follower_count') \
                    .eq('instagram_username', variation) \
                    .execute()
                    
                if response.data:
                    found = True
                    follower_count_text = response.data[0].get('follower_count')
                    follower_count = converter.parse_follower_count(follower_count_text) if follower_count_text else None
                    print(f"Found {username} as '{variation}':")
                    print(f"Follower Count (raw): {follower_count_text}")
                    print(f"Follower Count (parsed): {follower_count:,}" if follower_count else "Follower Count (parsed): None")
                    break
                    
            if not found:
                print(f"No match found for {username} (tried variations: {variations})")
            print("-" * 30)
                
            
            
    except Exception as e:
        print(f"Error checking Supabase table: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    check_table()