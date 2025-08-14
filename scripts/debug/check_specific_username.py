"""
Script to check a specific username in Supabase.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient

def check_username(username: str):
    """Check a specific username in Supabase."""
    # Initialize Supabase client
    supabase = SupabaseClient()
    
    try:
        print(f"\nChecking username: '{username}'")
        print("-" * 50)
        
        # Get all rows
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('*') \
            .execute()
            
        # Print all usernames
        print("\nAll usernames in Supabase:")
        print("-" * 50)
        for profile in response.data:
            if profile.get('instagram_username'):
                print(f"ID: {profile.get('id')}, Username: '{profile.get('instagram_username')}'")
                
        # Print all rows that contain the username (case-insensitive)
        matches = []
        for profile in response.data:
            if profile.get('instagram_username'):
                if username.lower() in profile['instagram_username'].lower():
                    matches.append(profile)
                    
        if matches:
            print(f"\nFound {len(matches)} potential matches:")
            for i, profile in enumerate(matches, 1):
                print(f"\nMatch {i}:")
                print(f"ID: {profile.get('id')}")
                print(f"Username: '{profile.get('instagram_username')}'")
                print(f"Full Name: {profile.get('full_name_profile')}")
                print(f"Follower Count: {profile.get('follower_count')}")
                print(f"Profile URL: {profile.get('profile_url')}")
                print("-" * 30)
        else:
            print("\nNo matches found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    check_username('nrl')