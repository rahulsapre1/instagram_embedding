from instagram_embedding.qdrant_utils import QdrantManager
import time

def check_qdrant_status():
    # Initialize QdrantManager with default settings
    try:
        manager = QdrantManager()
        
        # Get collection info
        info = manager.get_collection_info()
        
        print("\nQdrant Collection Status:")
        print("-" * 30)
        for key, value in info.items():
            print(f"{key}: {value}")
            
        # Try to get collections list
        collections = manager.client.get_collections()
        print("\nAvailable Collections:")
        print("-" * 30)
        for collection in collections.collections:
            print(f"Collection: {collection.name}")
            
    except Exception as e:
        print(f"Error checking Qdrant status: {str(e)}")

if __name__ == "__main__":
    # Wait a bit for Qdrant to initialize
    print("Waiting for Qdrant to initialize...")
    time.sleep(5)
    check_qdrant_status()