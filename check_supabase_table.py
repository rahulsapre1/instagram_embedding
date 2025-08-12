"""
Script to check the structure and contents of the Supabase table.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient

def check_table():
    """Check table structure and contents."""
    # Initialize Supabase client
    supabase = SupabaseClient()
    
    try:
        # Get sample of profiles
        response = supabase.client.table('ig_profile_info_v0_0') \
            .select('*') \
            .limit(5) \
            .execute()
            
        print("\nSample profiles:")
        print("-" * 50)
        for profile in response.data:
            print(f"Profile ID: {profile.get('id')}")
            print(f"Username: {profile.get('username')}")
            print(f"Full Name: {profile.get('full_name')}")
            print("-" * 30)
            
        # Check specific user IDs in both tables
        test_user_ids = [49599798700, 51908109693, 52131773000, 69410049705, 70991108955]
        
        print("\nChecking specific user IDs in ig_profile_info_v0_0:")
        print("-" * 50)
        for user_id in test_user_ids:
            response = supabase.client.table('ig_profile_info_v0_0') \
                .select('user_id, username, full_name') \
                .eq('user_id', user_id) \
                .execute()
                
            if response.data:
                print(f"Found user_id {user_id}:")
                print(f"Username: {response.data[0].get('username')}")
                print(f"Full Name: {response.data[0].get('full_name')}")
            else:
                print(f"No match found for user_id {user_id}")
            print("-" * 30)
            
        print("\nChecking specific user IDs in ig_profile_merged_v0_1:")
        print("-" * 50)
        for user_id in test_user_ids:
            response = supabase.client.table('ig_profile_merged_v0_1') \
                .select('*') \
                .eq('user_id', user_id) \
                .execute()
                
            if response.data:
                print(f"Found user_id {user_id}:")
                for key, value in response.data[0].items():
                    print(f"{key}: {value}")
            else:
                print(f"No match found for user_id {user_id}")
            print("-" * 30)
            
        # Get sample of all user IDs from both tables
        print("\nSample user IDs in ig_profile_info_v0_0:")
        print("-" * 50)
        response = supabase.client.table('ig_profile_info_v0_0') \
            .select('user_id, username, full_name') \
            .order('user_id') \
            .limit(5) \
            .execute()
            
        for profile in response.data:
            print(f"User ID: {profile.get('user_id')}")
            print(f"Username: {profile.get('username')}")
            print(f"Full Name: {profile.get('full_name')}")
            print("-" * 30)
            
        print("\nSample user IDs in ig_profile_merged_v0_1:")
        print("-" * 50)
        response = supabase.client.table('ig_profile_merged_v0_1') \
            .select('*') \
            .order('user_id') \
            .limit(5) \
            .execute()
            
        for profile in response.data:
            print(f"Sample profile data:")
            for key, value in profile.items():
                print(f"{key}: {value}")
            print("-" * 30)
        
    except Exception as e:
        print(f"Error checking Supabase table: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    check_table()