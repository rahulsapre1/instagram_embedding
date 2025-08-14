"""
Script to check Supabase data for full names.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient

def check_full_names():
    """Check full names in Supabase."""
    # Initialize Supabase client
    supabase = SupabaseClient()
    
    try:
        # Get sample of all profiles
        response = supabase.client.table('ig_profile_info_v0_0') \
            .select('username, full_name') \
            .limit(10) \
            .execute()
            
        print("\nSample profiles:")
        print("-" * 50)
        for profile in response.data:
            print(f"Username: {profile.get('username', 'N/A')}")
            print(f"Full Name: {profile.get('full_name', 'N/A')}")
            print("-" * 30)
            
        # Get total count
        response = supabase.client.table('ig_profile_info_v0_0') \
            .select('*', count='exact') \
            .execute()
        total = response.count
        
        # Get all profiles and count manually
        response = supabase.client.table('ig_profile_info_v0_0') \
            .select('full_name') \
            .execute()
        
        # Count profiles with non-empty full names
        with_names = sum(1 for profile in response.data 
                        if profile.get('full_name') and profile['full_name'].strip())
        
        print("\nStatistics:")
        print("-" * 50)
        print(f"Total profiles: {total}")
        print(f"Profiles with full names: {with_names}")
        print(f"Profiles without full names: {total - with_names}")
        
    except Exception as e:
        print(f"Error checking Supabase data: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    check_full_names()