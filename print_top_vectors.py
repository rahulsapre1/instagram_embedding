"""
Script to print information about top 10 vectors from each collection.
"""
import os
from dotenv import load_dotenv
from instagram_embedding.qdrant_utils import QdrantManager
import numpy as np

def print_vector_info(collection_name: str):
    """Print information about top 10 vectors from a collection."""
    print(f"\n📊 Top 10 vectors from {collection_name}")
    print("=" * 50)
    
    # Initialize Qdrant manager
    manager = QdrantManager(collection_name=collection_name)
    
    try:
        # Get collection info
        info = manager.get_collection_info()
        print(f"\nCollection Info:")
        print(f"  • Total vectors: {info['vectors_count']}")
        print(f"  • Indexed vectors: {info['indexed_vectors_count']}")
        print(f"  • Points count: {info['points_count']}")
        
        # Get first 10 points with vectors
        response = manager.client.scroll(
            collection_name=collection_name,
            limit=10,
            with_payload=True,
            with_vectors=True
        )
        
        points = response[0]
        if not points:
            print("\nNo vectors found in collection")
            return
            
        print(f"\nVector Details:")
        for i, point in enumerate(points, 1):
            print(f"\n🔹 Vector {i}")
            print(f"  • ID: {point.id}")
            
            # Print metadata
            print("  • Metadata:")
            for key, value in point.payload.items():
                print(f"    - {key}: {value}")
            
            # Print vector statistics
            vector = np.array(point.vector)
            print("  • Vector Statistics:")
            print(f"    - Shape: {vector.shape}")
            print(f"    - Mean: {vector.mean():.6f}")
            print(f"    - Std: {vector.std():.6f}")
            print(f"    - Min: {vector.min():.6f}")
            print(f"    - Max: {vector.max():.6f}")
            print(f"    - First 5 values: {vector[:5]}")
            print(f"    - Last 5 values: {vector[-5:]}")
            
    except Exception as e:
        print(f"Error getting vectors from {collection_name}: {str(e)}")

def main():
    """Print vector information from both collections."""
    # Load environment variables
    load_dotenv()
    
    # Print vectors from both collections
    print_vector_info("instagram_profiles")
    print_vector_info("query_profiles")

if __name__ == "__main__":
    main()