"""
Batch process all profiles with hybrid classification and update Qdrant.
"""
import os
import time
from typing import Dict, List, Optional, Set
from tqdm import tqdm
from dotenv import load_dotenv

from query_embedding.account_classifier import AccountTypeClassifier
from query_embedding.qdrant_utils import QdrantSearcher
from query_embedding.supabase_utils import SupabaseClient

# Load environment variables
load_dotenv()

class BatchClassifier:
    def __init__(self, batch_size: int = 100):
        """
        Initialize batch classifier.
        
        Args:
            batch_size: Number of profiles to process in each batch
        """
        self.batch_size = batch_size
        self.classifier = AccountTypeClassifier()
        self.qdrant = QdrantSearcher()
        self.supabase = SupabaseClient()
        
        # Track processed profiles to avoid duplicates
        self.processed_profiles: Set[str] = set()
        
        # Statistics
        self.stats = {
            'total': 0,
            'human': 0,
            'brand': 0,
            'unknown': 0,
            'error': 0
        }
        
    def get_profiles_batch(self, offset: int) -> List[Dict]:
        """
        Get a batch of profiles from Qdrant.
        
        Args:
            offset: Starting offset for pagination
            
        Returns:
            List of profile dictionaries
        """
        try:
            # Use a generic query to get all profiles
            results = self.qdrant.search(
                query="instagram profile",
                filters=None,
                offset=offset,
                limit=self.batch_size
            )
            
            profiles = []
            for result in results:
                payload = result.payload
                username = payload.get('username')
                if username and username not in self.processed_profiles:
                    profiles.append({
                        'username': username,
                        'full_name': payload.get('full_name', ''),
                        'bio': payload.get('bio', ''),
                        'captions': payload.get('captions', []),
                        'follower_count': payload.get('follower_count', 0),
                        'influencer_type': payload.get('influencer_type', ''),
                        'embedding': result.vector
                    })
                    self.processed_profiles.add(username)
            
            return profiles
            
        except Exception as e:
            print(f"❌ Error fetching profiles from Qdrant: {str(e)}")
            return []
            
    def get_profile_data_from_supabase(self, usernames: List[str]) -> Dict[str, Dict]:
        """
        Get additional profile data from Supabase.
        
        Args:
            usernames: List of usernames to fetch data for
            
        Returns:
            Dictionary mapping usernames to profile data
        """
        try:
            return self.supabase.fetch_profile_data(usernames)
        except Exception as e:
            print(f"❌ Error fetching profile data from Supabase: {str(e)}")
            return {}
            
    def update_qdrant_profiles(self, updates: Dict[str, str]) -> Dict[str, bool]:
        """
        Update account types in Qdrant in batch.
        
        Args:
            updates: Dictionary mapping usernames to account types
            
        Returns:
            Dictionary mapping usernames to update success status
        """
        try:
            # Get all profile IDs in one query
            usernames = list(updates.keys())
            results = {}
            
            # Process in chunks of 100 to avoid large queries
            chunk_size = 100
            for i in range(0, len(usernames), chunk_size):
                chunk = usernames[i:i + chunk_size]
                
                # Search for profiles to get their IDs
                chunk_results = self.qdrant.search(
                    query="instagram profile",  # Generic query
                    filters={"username": {"$in": chunk}},
                    limit=len(chunk)
                )
                
                # Map usernames to point IDs
                point_ids = []
                for result in chunk_results:
                    username = result.payload.get('username')
                    if username in updates:
                        point_ids.append(result.id)
                        results[username] = True
                    
                # Update payloads in batch
                if point_ids:
                    try:
                        self.qdrant.client.set_payload(
                            collection_name=self.qdrant.collection_name,
                            payload={'account_type': updates[username]},
                            points=point_ids
                        )
                    except Exception as e:
                        print(f"❌ Error updating chunk in Qdrant: {str(e)}")
                        for username in chunk:
                            results[username] = False
                
                # Rate limiting
                time.sleep(0.1)  # 100ms delay between chunks
            
            # Mark any usernames that weren't found as failed
            for username in updates:
                if username not in results:
                    results[username] = False
                    print(f"❌ Could not find profile {username} in Qdrant")
            
            return results
            
        except Exception as e:
            print(f"❌ Error during batch update in Qdrant: {str(e)}")
            return {username: False for username in updates}
            
    def process_batch(self, profiles: List[Dict]) -> None:
        """
        Process a batch of profiles.
        
        Args:
            profiles: List of profile dictionaries
        """
        if not profiles:
            return
            
        # Get usernames for this batch
        usernames = [p['username'] for p in profiles]
        
        # Get additional data from Supabase
        supabase_data = self.get_profile_data_from_supabase(usernames)
        
        # Prepare data for classification
        profile_embeddings = {}
        profile_data = {}
        
        for profile in profiles:
            username = profile['username']
            embedding = profile.get('embedding')
            
            if embedding is not None:
                profile_embeddings[username] = embedding
                
                # Combine Qdrant and Supabase data
                supabase_profile = supabase_data.get(username, {})
                profile_data[username] = {
                    'username': username,
                    'full_name': profile.get('full_name') or supabase_profile.get('full_name', ''),
                    'bio': profile.get('bio') or supabase_profile.get('bio', ''),
                    'captions': profile.get('captions') or supabase_profile.get('captions', [])
                }
        
        # Run classification
        try:
            classification_results = self.classifier.classify_accounts(
                profile_embeddings,
                profile_data
            )
            
            # Update Qdrant in batch
            update_results = self.update_qdrant_profiles(classification_results)
            
            # Track statistics
            for username, success in update_results.items():
                if success:
                    self.stats['total'] += 1
                    self.stats[classification_results[username]] += 1
                else:
                    self.stats['error'] += 1
                    
        except Exception as e:
            print(f"❌ Error in batch classification: {str(e)}")
            self.stats['error'] += len(profile_embeddings)
            
    def process_all_profiles(self) -> None:
        """Process all profiles in the database."""
        print("\n🔄 Starting Batch Classification")
        print("=" * 50)
        
        offset = 0
        total_processed = 0
        error_count = 0
        max_retries = 3
        
        try:
            with tqdm(desc="Processing profiles", unit="profiles") as pbar:
                while True:
                    try:
                        # Get next batch
                        profiles = self.get_profiles_batch(offset)
                        if not profiles:
                            break
                            
                        # Process batch
                        batch_size = len(profiles)
                        pbar.total = total_processed + batch_size
                        
                        self.process_batch(profiles)
                        
                        # Update progress
                        total_processed += batch_size
                        pbar.update(batch_size)
                        
                        # Show current statistics
                        pbar.set_postfix({
                            'human': self.stats['human'],
                            'brand': self.stats['brand'],
                            'unknown': self.stats['unknown'],
                            'errors': self.stats['error']
                        })
                        
                        # Move to next batch
                        offset += self.batch_size
                        
                        # Reset error count on successful batch
                        error_count = 0
                        
                        # Rate limiting for Gemini API
                        time.sleep(1)  # 1 second delay between batches
                        
                    except Exception as e:
                        error_count += 1
                        print(f"\n❌ Error processing batch: {str(e)}")
                        
                        if error_count >= max_retries:
                            print(f"\n⚠️  Too many errors ({error_count}), stopping process")
                            break
                            
                        print(f"Retrying in 5 seconds... (attempt {error_count}/{max_retries})")
                        time.sleep(5)
                        continue
                        
        except KeyboardInterrupt:
            print("\n⚠️  Process interrupted by user")
            
        finally:
            # Save progress to file
            try:
                with open('classification_progress.txt', 'w') as f:
                    f.write(f"Last processed offset: {offset}\n")
                    f.write(f"Total profiles processed: {total_processed}\n")
                    f.write(f"Human accounts: {self.stats['human']}\n")
                    f.write(f"Brand accounts: {self.stats['brand']}\n")
                    f.write(f"Unknown accounts: {self.stats['unknown']}\n")
                    f.write(f"Errors: {self.stats['error']}\n")
                print("\n✅ Progress saved to classification_progress.txt")
            except Exception as e:
                print(f"\n❌ Error saving progress: {str(e)}")
            
            # Print final statistics
            print("\n📊 Final Statistics")
            print("=" * 30)
            print(f"Total Profiles Processed: {self.stats['total']}")
            if self.stats['total'] > 0:
                print(f"Human Accounts: {self.stats['human']} ({self.stats['human']/self.stats['total']*100:.1f}%)")
                print(f"Brand Accounts: {self.stats['brand']} ({self.stats['brand']/self.stats['total']*100:.1f}%)")
                print(f"Unknown/Disagreement: {self.stats['unknown']} ({self.stats['unknown']/self.stats['total']*100:.1f}%)")
            print(f"Errors: {self.stats['error']}")
            
            if error_count >= max_retries:
                print("\n⚠️  Process stopped due to too many errors")
                print(f"Last successful offset: {offset - self.batch_size}")
                print("To continue from this point, update the offset in the script")
            
def main():
    """Main entry point."""
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not set in .env file")
        print("Please add your Gemini API key to the .env file:")
        print("GEMINI_API_KEY=your_api_key_here")
        return
    
    # Create and run batch classifier
    classifier = BatchClassifier(batch_size=100)
    classifier.process_all_profiles()

if __name__ == "__main__":
    main()