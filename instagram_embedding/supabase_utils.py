"""
Supabase database utilities for fetching Instagram profile data.
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

load_dotenv()

class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client with credentials from environment variables."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client = create_client(url, key)
        self.table_name = "ig_profile_merged_v0_0"

    async def fetch_profiles(self, batch_size: int = 32, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch Instagram profiles in batches.
        
        Args:
            batch_size: Number of profiles to fetch per batch
            offset: Starting offset for pagination
            
        Returns:
            List of profile dictionaries containing profile data
        """
        try:
            print(f"\n📊 Fetching profiles from offset {offset} (batch size: {batch_size})")
            response = self.client.table(self.table_name)\
                .select("*")\
                .limit(batch_size)\
                .offset(offset)\
                .execute()
            
            profiles = response.data
            if profiles:
                sample_profile = profiles[0]
                print(f"\n📱 Sample Profile Details:")
                print(f"  • Username: {sample_profile.get('username')}")
                print(f"  • Full Name: {sample_profile.get('full_name')}")
                print(f"  • Bio Length: {len(sample_profile.get('bio', '')) if sample_profile.get('bio') else 0} chars")
                print(f"  • Has Profile Pic: {'✓' if sample_profile.get('profile_pic_url_hd') else '✗'}")
                
                post_urls = [sample_profile.get(f'post_{i}_url') for i in range(12)]
                valid_posts = len([url for url in post_urls if url])
                print(f"  • Valid Posts: {valid_posts}/12")
                
                captions = [sample_profile.get(f'caption_{i}') for i in range(12)]
                valid_captions = len([cap for cap in captions if cap])
                print(f"  • Valid Captions: {valid_captions}/12")
            
            print(f"\n✅ Successfully fetched {len(profiles)} profiles")
            return profiles
        except Exception as e:
            print(f"❌ Error fetching profiles: {e}")
            return []

    async def fetch_all_profiles(self, batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Fetch all Instagram profiles with progress tracking.
        
        Args:
            batch_size: Number of profiles to fetch per batch
            
        Returns:
            List of all profile dictionaries
        """
        all_profiles = []
        offset = 0
        
        # Get total count
        total = await self.get_total_profiles()
        
        with tqdm(total=total, desc="Fetching profiles") as pbar:
            while True:
                batch = await self.fetch_profiles(batch_size, offset)
                if not batch:
                    break
                    
                all_profiles.extend(batch)
                offset += batch_size
                pbar.update(len(batch))
                
                if len(batch) < batch_size:
                    break
        
        return all_profiles

    async def get_total_profiles(self) -> int:
        """Get total number of profiles in the database."""
        try:
            response = self.client.table(self.table_name)\
                .select("*", count="exact")\
                .execute()
            return len(response.data)
        except Exception as e:
            print(f"Error getting total profiles: {e}")
            return 0

    def extract_post_urls(self, profile: Dict[str, Any]) -> List[str]:
        """Extract post URLs from a profile dictionary."""
        return [
            profile.get(f"post_{i}_url")
            for i in range(12)
            if profile.get(f"post_{i}_url")
        ]

    def extract_captions(self, profile: Dict[str, Any]) -> List[str]:
        """Extract post captions from a profile dictionary."""
        return [
            profile.get(f"caption_{i}")
            for i in range(12)
            if profile.get(f"caption_{i}")
        ]

    def extract_bio(self, profile: Dict[str, Any]) -> Optional[str]:
        """Extract bio from a profile dictionary."""
        return profile.get("bio")