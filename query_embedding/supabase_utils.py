"""
Supabase client for fetching Instagram profile data.
"""
import os
import time
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from query_embedding.follower_utils import FollowerCountConverter

# Load environment variables
load_dotenv()

class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
            
        self.client: Client = create_client(self.url, self.key)
        self.follower_converter = FollowerCountConverter()
        
    def fetch_profile_data(self, usernames: List[str]) -> Dict[str, Dict]:
        """
        Fetch profile data for given usernames.
        
        Args:
            usernames: List of Instagram usernames
            
        Returns:
            Dictionary mapping usernames to their profile data
        """
        try:
            # Add non-breaking space prefix to usernames to match Supabase format
            spaced_usernames = [f"\xa0{username}" for username in usernames]
            
            # Split usernames into chunks of 100 to avoid URL length limits
            chunk_size = 100
            username_chunks = [usernames[i:i + chunk_size] for i in range(0, len(usernames), chunk_size)]
            
            # Process each chunk
            profile_data = {}
            for chunk in username_chunks:
                # Query Supabase
                response = self.client.table('ig_profile_merged_v0_0') \
                    .select('*') \
                    .in_('username', chunk) \
                    .execute()
                    
                # Process results
                for record in response.data:
                    username = record.get('username')
                    if not username:
                        continue
                        
                    # Extract captions
                    captions = []
                    for i in range(12):
                        caption = record.get(f'caption_{i}')
                        if caption:
                            captions.append(caption)
                    
                    profile_data[username] = {
                        'username': username,
                        'full_name': record.get('full_name', ''),
                        'bio': record.get('bio', ''),
                        'captions': captions,
                        'is_private': record.get('is_private', False)
                    }
                    
                # Rate limiting
                time.sleep(0.1)  # 100ms delay between chunks
                
            return profile_data
            
        except Exception as e:
            print(f"Error fetching profile data: {str(e)}")
            return {}