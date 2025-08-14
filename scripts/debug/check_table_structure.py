"""
Script to check the structure of the Supabase table.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient

def check_table():
    """Check table structure."""
    # Initialize Supabase client
    supabase = SupabaseClient()
    
    try:
        # Get a sample row
        response = supabase.client.table('ig_profile_raw_v0_2') \
            .select('*') \
            .limit(1) \
            .execute()
            
        if response.data:
            print("\nTable structure:")
            print("-" * 50)
            for key, value in response.data[0].items():
                print(f"{key}: {type(value).__name__}")
                print(f"Value: {value}")
                print("-" * 30)
        else:
            print("No data found in table")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    check_table()