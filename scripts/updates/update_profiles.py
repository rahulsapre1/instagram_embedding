"""
Script to update Qdrant collection with follower counts and account types.
"""
import os
from typing import List, Dict, Any
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http.models import UpdateStatus

from query_embedding.supabase_utils import SupabaseClient
from query_embedding.account_classifier import AccountTypeClassifier
from query_embedding.embedder import QueryEmbedder

def update_profiles():
    """Update profile data in Qdrant collection."""
    # Initialize clients
    print("Initializing clients...")
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_HOST", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30.0  # Increase timeout
    )
    supabase = SupabaseClient()
    
    # Get all profiles from Qdrant
    print("Fetching profiles from Qdrant...")
    profiles = qdrant.scroll(
        collection_name="instagram_profiles",
        limit=10000,  # Adjust based on collection size
        with_payload=True,
        with_vectors=True
    )[0]
    
    # Extract usernames and embeddings
    usernames = [p.payload["username"] for p in profiles]
    embeddings = {p.payload["username"]: p.vector for p in profiles}
    
    # Process in smaller batches
    batch_size = 100
    total_processed = 0
    
    for i in range(0, len(usernames), batch_size):
        batch_usernames = usernames[i:i + batch_size]
        batch_embeddings = {k: embeddings[k] for k in batch_usernames}
        
        # Fetch follower counts from Supabase
        print(f"\nFetching follower counts for batch {i//batch_size + 1}...")
        profile_data = supabase.fetch_profile_data(batch_usernames)
        
        # Classify account types for batch
        print("Classifying account types...")
        classifier = AccountTypeClassifier()
        account_types = classifier.classify_accounts(batch_embeddings)
        
        # Update Qdrant records
        print("Updating Qdrant records...")
        for profile in tqdm(profiles[i:i + batch_size]):
            username = profile.payload["username"]
            
            # Get follower data
            follower_data = profile_data.get(username, {})
            follower_count = follower_data.get("follower_count")
            follower_category = follower_data.get("follower_category")
            
            # Get account type
            account_type = account_types.get(username)
            
            # Update payload
            new_payload = {
                **profile.payload,
                "follower_count": follower_count,
                "follower_category": follower_category,
                "account_type": account_type
            }
            
            # Update record
            try:
                qdrant.set_payload(
                    collection_name="instagram_profiles",
                    payload=new_payload,
                    points=[profile.id]
                )
                total_processed += 1
            except Exception as e:
                print(f"Error updating profile {username}: {str(e)}")
                continue
                
        print(f"Processed {total_processed} profiles")
        
    print("\nUpdate complete!")

if __name__ == "__main__":
    update_profiles()