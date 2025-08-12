"""
Script to retrieve profile information from Qdrant.
"""
import os
from dotenv import load_dotenv
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from query_embedding.qdrant_utils import QdrantSearcher
from query_embedding.embedder import QueryEmbedder

# Load environment variables
load_dotenv()

def get_profile_info(username: str):
    """Get all stored information for a profile."""
    print("\n🔄 Initializing...")
    
    try:
        # Initialize searcher
        searcher = QdrantSearcher(top_k=1)
        embedder = QueryEmbedder()
        
        print("✅ Connected to Qdrant")
        print(f"\n🔍 Searching for profile: @{username}")
        
        # Create a simple query embedding
        query_embedding = embedder.embed_query(f"instagram profile {username}")
        
        # Search for the profile
        results = searcher.client.search(
            collection_name=searcher.collection_name,
            query_vector=query_embedding.tolist(),
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="username",
                        match=MatchValue(value=username)
                    )
                ]
            ),
            limit=1,
            with_vectors=True
        )
        
        if not results:
            print(f"❌ Profile {username} not found in database")
            return
            
        # Get profile data
        profile = results[0]
        payload = profile.payload
        vector = profile.vector
        
        # Print information
        print(f"\n📊 Profile Information for @{username}")
        print("=" * 50)
        
        # Basic info
        print("\n🔍 Basic Information:")
        print(f"  • Username: {payload.get('username', 'N/A')}")
        print(f"  • Full Name: {payload.get('full_name', 'N/A')}")
        print(f"  • User ID: {payload.get('user_id', 'N/A')}")
        print(f"  • Is Private: {payload.get('is_private', 'N/A')}")
        
        # Classification
        print("\n🏷️  Classification:")
        print(f"  • Account Type: {payload.get('account_type', 'N/A')}")
        print(f"  • Follower Count: {payload.get('follower_count', 'N/A'):,}")
        print(f"  • Influencer Type: {payload.get('influencer_type', 'N/A').capitalize()}")
        
        # Content
        print("\n📝 Content:")
        print(f"  • Bio: {payload.get('bio', 'N/A')}")
        
        captions = payload.get('captions', [])
        if captions:
            print(f"\n📸 Recent Captions ({len(captions)}):")
            for i, caption in enumerate(captions[:5], 1):
                print(f"  {i}. {caption[:100]}{'...' if len(caption) > 100 else ''}")
                
        # URLs
        print("\n🔗 URLs:")
        print(f"  • Profile Picture: {payload.get('profile_pic_url', 'N/A')}")
        
        # Vector information
        if vector:
            print(f"\n🧮 Embedding Vector:")
            print(f"  • Dimensions: {len(vector)}")
            print(f"  • Sample (first 5): {vector[:5]}")
            
        # Search score
        print(f"\n📈 Search Score: {profile.score:.3f}")
        
    except Exception as e:
        print(f"❌ Error retrieving profile: {str(e)}")

def main():
    """Main entry point."""
    username = "tonyavinci"
    get_profile_info(username)

if __name__ == "__main__":
    main()