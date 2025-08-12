"""
Script to reclassify Instagram profiles using OpenAI's GPT model.
"""
import os
import time
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, UpdateStatus
from query_embedding.qdrant_utils import QdrantSearcher
from query_embedding.embedder import QueryEmbedder
from query_embedding.supabase_utils import SupabaseClient
from query_embedding.openai_classifier import OpenAIClassifier

# Load environment variables
load_dotenv()

def get_all_usernames(searcher: QdrantSearcher) -> Set[str]:
    """Get all unique usernames from Qdrant."""
    try:
        all_usernames = set()
        offset = None
        
        while True:
            # Get next batch of usernames
            results, next_offset = searcher.client.scroll(
                collection_name=searcher.collection_name,
                offset=offset,
                limit=1000,  # Large batch size for efficiency
                with_payload=['username'],  # Only fetch username
                with_vectors=False
            )
            
            if not results:
                break
                
            # Add valid usernames to set
            for result in results:
                username = result.payload.get('username')
                if username:
                    all_usernames.add(username)
                    
            # Update offset for next batch
            offset = next_offset
            if not offset:
                break
                
        return all_usernames
    except Exception as e:
        print(f"Error getting usernames: {str(e)}")
        return set()

def get_profile_by_username(searcher: QdrantSearcher, username: str) -> Optional[Dict]:
    """Get profile data for a specific username."""
    try:
        # Search for profile with exact username match
        results = searcher.client.search(
            collection_name=searcher.collection_name,
            query_vector=[0] * 128,  # Dummy vector
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="username",
                        match=MatchValue(value=username)
                    )
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        if not results:
            return None
            
        result = results[0]
        return {
            'id': result.id,
            'username': username,
            'full_name': result.payload.get('full_name'),
            'bio': result.payload.get('bio'),
            'follower_count': result.payload.get('follower_count'),
            'influencer_type': result.payload.get('influencer_type'),
            'current_type': result.payload.get('account_type'),
            'is_private': result.payload.get('is_private', False)
        }
    except Exception as e:
        print(f"Error fetching profile for {username}: {str(e)}")
        return None

def update_profile_type(searcher: QdrantSearcher, profile_id: str, username: str, new_type: str, retry_count: int = 3) -> bool:
    """
    Update profile type in Qdrant with retry mechanism.
    
    Args:
        searcher: QdrantSearcher instance
        profile_id: ID of the profile to update
        username: Username for verification
        new_type: New account type classification
        retry_count: Number of retries on failure
        
    Returns:
        bool: True if update was successful
    """
    for attempt in range(retry_count):
        try:
            # Update the profile type and remove profile_pic_url
            searcher.client.set_payload(
                collection_name=searcher.collection_name,
                payload={
                    'account_type': new_type,
                    'profile_pic_url': None  # This will remove the field
                },
                points=[profile_id]
            )
            return True
            
        except Exception as e:
            print(f"Error updating profile {username} (attempt {attempt + 1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(1)  # Wait before retry
                
    return False

def get_percentage(value: int, total: int) -> float:
    """Calculate percentage safely."""
    return (value / total * 100) if total > 0 else 0

def save_progress(stats: Dict, filename: str = "classification_progress.txt"):
    """Save classification progress to a file."""
    with open(filename, 'w') as f:
        f.write("Classification Progress:\n")
        f.write(f"Total Profiles Processed: {stats['processed']}\n")
        f.write(f"Changes Made: {stats['changes']}\n")
        f.write(f"Human: {stats['human']} ({get_percentage(stats['human'], stats['processed']):.1f}%)\n")
        f.write(f"Brand: {stats['brand']} ({get_percentage(stats['brand'], stats['processed']):.1f}%)\n")
        f.write(f"Unknown: {stats['unknown']} ({get_percentage(stats['unknown'], stats['processed']):.1f}%)\n")
        f.write(f"Errors: {stats['errors']}\n")
        f.write(f"Processed Usernames: {','.join(stats['processed_usernames'])}\n")

def load_progress(filename: str = "classification_progress.txt") -> Dict:
    """Load progress from file if it exists."""
    default_stats = {
        'processed': 0,
        'changes': 0,
        'human': 0,
        'brand': 0,
        'unknown': 0,
        'errors': 0,
        'processed_usernames': set()
    }
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            stats = default_stats.copy()
            for line in lines:
                if 'Total Profiles Processed:' in line:
                    stats['processed'] = int(line.split(':')[1].strip())
                elif 'Changes Made:' in line:
                    stats['changes'] = int(line.split(':')[1].strip())
                elif 'Human:' in line:
                    stats['human'] = int(line.split(':')[1].split('(')[0].strip())
                elif 'Brand:' in line:
                    stats['brand'] = int(line.split(':')[1].split('(')[0].strip())
                elif 'Unknown:' in line:
                    stats['unknown'] = int(line.split(':')[1].split('(')[0].strip())
                elif 'Errors:' in line:
                    stats['errors'] = int(line.split(':')[1].strip())
                elif 'Processed Usernames:' in line:
                    usernames = line.split(':')[1].strip().split(',')
                    stats['processed_usernames'] = set(u for u in usernames if u)
            return stats
    except:
        return default_stats

def process_profile(searcher: QdrantSearcher, classifier: OpenAIClassifier, username: str, stats: Dict) -> Dict:
    """Process a single profile and update the database."""
    # Get profile data
    profile = get_profile_by_username(searcher, username)
    if not profile:
        print(f"⚠️  Could not fetch profile for @{username}")
        return stats
        
    # Skip if already processed
    if username in stats['processed_usernames']:
        return stats
        
    # Mark as processed
    stats['processed_usernames'].add(username)
    
    # Classify profile
    old_type = profile['current_type']
    result = classifier.classify_profile(profile)
    new_type = result['classification']
    confidence = result['confidence']
    reasoning = result['reasoning']
    
    # Update statistics
    stats['processed'] += 1
    stats[new_type] += 1
    
    # Check if type changed
    if old_type != new_type:
        stats['changes'] += 1
        print(f"\n📝 Reclassifying @{profile['username']}")
        print(f"  • Full Name: {profile['full_name']}")
        print(f"  • Old Type: {old_type}")
        print(f"  • New Type: {new_type}")
        print(f"  • Confidence: {confidence}%")
        print(f"  • Reasoning: {reasoning}")
        
        # Update in database
        success = update_profile_type(
            searcher=searcher,
            profile_id=profile['id'],
            username=profile['username'],
            new_type=new_type
        )
        if not success:
            stats['errors'] += 1
            
        # Small delay after update
        time.sleep(0.5)
        
    return stats

def main():
    """Main entry point."""
    print("\n🔄 Starting Profile Reclassification using OpenAI")
    print("=" * 50)
    
    # Initialize components
    searcher = QdrantSearcher()
    classifier = OpenAIClassifier()
    
    # Get all unique usernames
    print("\n📊 Getting all unique usernames...")
    all_usernames = get_all_usernames(searcher)
    total_profiles = len(all_usernames)
    
    if total_profiles == 0:
        print("❌ No profiles found in database")
        return
        
    print(f"Found {total_profiles} unique profiles")
    
    # Load progress if exists
    stats = load_progress()
    print(f"Previously processed: {len(stats['processed_usernames'])} profiles")
    
    # Get unprocessed usernames
    unprocessed_usernames = all_usernames - stats['processed_usernames']
    print(f"Remaining to process: {len(unprocessed_usernames)} profiles")
    
    # Process profiles
    print("\n🔍 Reclassifying profiles...")
    
    try:
        for username in sorted(unprocessed_usernames):
            # Process profile
            stats = process_profile(searcher, classifier, username, stats)
            
            # Save progress
            save_progress(stats)
            
            # Progress update
            print(f"\n✅ Processed {stats['processed']}/{total_profiles} profiles ({(stats['processed']/total_profiles*100):.1f}%)")
            if stats['processed'] > 0:
                print(f"Current Distribution:")
                print(f"  • Human: {stats['human']} ({get_percentage(stats['human'], stats['processed']):.1f}%)")
                print(f"  • Brand: {stats['brand']} ({get_percentage(stats['brand'], stats['processed']):.1f}%)")
                print(f"  • Unknown: {stats['unknown']} ({get_percentage(stats['unknown'], stats['processed']):.1f}%)")
                if stats['errors'] > 0:
                    print(f"⚠️  Errors: {stats['errors']}")
                    
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        print("Saving progress...")
        save_progress(stats)
        print("Progress saved. You can resume later.")
        return
            
    # Print final statistics
    print("\n📊 Reclassification Results")
    print("=" * 30)
    print(f"Total Profiles Processed: {stats['processed']}")
    print(f"Changes Made: {stats['changes']}")
    if stats['processed'] > 0:
        print(f"Final Distribution:")
        print(f"  • Human: {stats['human']} ({get_percentage(stats['human'], stats['processed']):.1f}%)")
        print(f"  • Brand: {stats['brand']} ({get_percentage(stats['brand'], stats['processed']):.1f}%)")
        print(f"  • Unknown: {stats['unknown']} ({get_percentage(stats['unknown'], stats['processed']):.1f}%)")
        if stats['errors'] > 0:
            print(f"⚠️  Errors: {stats['errors']}")
        
    print("\n✅ Reclassification completed!")
    save_progress(stats)

if __name__ == "__main__":
    main()