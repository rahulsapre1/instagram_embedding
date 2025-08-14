"""
Script to remove profile_pic_url field from all records in both Qdrant collections.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.qdrant_utils import QdrantManager
from tqdm import tqdm

def remove_profile_pic_url(collection_name: str, batch_size: int = 100):
    """Remove profile_pic_url from all records in a collection."""
    print(f"\n🔄 Removing profile_pic_url from {collection_name} collection...")
    
    # Initialize Qdrant manager
    manager = QdrantManager(collection_name=collection_name)
    
    try:
        # Get collection info
        info = manager.get_collection_info()
        total_points = info.get('points_count', 0)
        
        if total_points == 0:
            print("No records found in collection")
            return
            
        processed = 0
        failed = 0
        offset = None
        
        with tqdm(total=total_points, desc="Processing") as pbar:
            while True:
                # Get batch of points
                response = manager.client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, offset = response
                if not points:
                    break
                    
                # Process each point in the batch
                for point in points:
                    try:
                        if 'profile_pic_url' in point.payload:
                            # Remove profile_pic_url from payload
                            manager.client.set_payload(
                                collection_name=collection_name,
                                payload={
                                    'profile_pic_url': None  # This will remove the field
                                },
                                points=[point.id]
                            )
                            processed += 1
                    except Exception as e:
                        print(f"\nError processing point {point.id}: {str(e)}")
                        failed += 1
                    
                    pbar.update(1)
                
                if offset is None:
                    break
        
        print(f"\n✅ Processed {processed} records")
        if failed > 0:
            print(f"⚠️  Failed to process {failed} records")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Remove profile_pic_url from all collections."""
    # Load environment variables
    load_dotenv()
    
    # Process both collections
    remove_profile_pic_url("instagram_profiles")
    remove_profile_pic_url("query_profiles")
    
    print("\n✨ Done!")

if __name__ == "__main__":
    main()