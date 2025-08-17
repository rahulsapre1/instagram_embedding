"""
Demo script for testing hybrid image + text search functionality
Uses the Melbourne tram image URL provided in requirements
"""

import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from query_embedding.hybrid_search import HybridSearchEngine
from query_embedding.weight_analyzer import WeightAnalyzer
from query_embedding.image_processor import ImageProcessor


async def test_hybrid_search():
    """Test the complete hybrid search pipeline"""
    print("🚀 HYBRID SEARCH DEMO")
    print("=" * 60)
    
    # Test URL from requirements
    test_url = "https://seniorsinmelbourne.com.au/wp-content/uploads/2024/03/City_Circle_Tram_Melbourne-25.jpg"
    test_queries = [
        "find similar profiles",
        "search for travel accounts",
        "profiles with similar style",
        "find people like this",
        "search for fashion influencers"
    ]
    
    print(f"🖼️  Test Image: {test_url}")
    print("=" * 60)
    
    try:
        # Test 1: Weight Analyzer
        print("\n🧠 TEST 1: Weight Analyzer")
        print("-" * 40)
        weight_analyzer = WeightAnalyzer()
        
        for query in test_queries:
            try:
                weights = await weight_analyzer.get_weights(query)
                print(f"Query: '{query}'")
                print(f"  → Image weight: {weights['image_weight']:.1f}")
                print(f"  → Text weight: {weights['text_weight']:.1f}")
                print()
            except Exception as e:
                print(f"Query: '{query}' → Error: {str(e)}")
        
        # Test 2: Image Processor
        print("\n🖼️  TEST 2: Image Processor")
        print("-" * 40)
        image_processor = ImageProcessor()
        
        # Validate URL
        is_valid = await image_processor.validate_image_url(test_url)
        print(f"URL validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        if is_valid:
            # Download and process image
            embedding = await image_processor.get_embedding_from_url(test_url)
            if embedding:
                print(f"✅ Successfully generated embedding: {len(embedding)} dimensions")
                print(f"First 5 values: {embedding[:5]}")
            else:
                print("❌ Failed to generate embedding")
        else:
            print("❌ Cannot proceed with invalid URL")
        
        # Test 3: Complete Hybrid Search
        print("\n🔍 TEST 3: Complete Hybrid Search")
        print("-" * 40)
        
        if is_valid and embedding:
            hybrid_engine = HybridSearchEngine()
            
            # Test with different queries
            for query in test_queries[:3]:  # Test first 3 queries
                try:
                    print(f"\nSearching with query: '{query}'")
                    results, weights = await hybrid_engine.search(test_url, query)
                    
                    print(f"✅ Search completed!")
                    print(f"  Weights: Image={weights['image_weight']:.1f}, Text={weights['text_weight']:.1f}")
                    print(f"  Results: {len(results)} profiles found")
                    
                    if results:
                        print("  Top 3 results:")
                        for i, result in enumerate(results[:3], 1):
                            payload = result.payload
                            print(f"    {i}. {payload.get('username', 'N/A')} "
                                  f"({payload.get('full_name', 'N/A')}) - "
                                  f"Score: {result.score:.3f}")
                    
                except Exception as e:
                    print(f"❌ Search failed: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 Demo completed!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        print("Please check your environment and dependencies.")


async def test_simple_components():
    """Test individual components separately"""
    print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
    print("=" * 60)
    
    # Test Weight Analyzer
    try:
        print("\n🧠 Testing Weight Analyzer...")
        analyzer = WeightAnalyzer()
        weights = await analyzer.get_weights("find similar profiles")
        print(f"✅ Weight analyzer works: {weights}")
    except Exception as e:
        print(f"❌ Weight analyzer failed: {str(e)}")
    
    # Test Image Processor
    try:
        print("\n🖼️  Testing Image Processor...")
        processor = ImageProcessor()
        is_valid = await processor.validate_image_url("https://example.com/test.jpg")
        print(f"✅ Image processor works (validation result: {is_valid})")
    except Exception as e:
        print(f"❌ Image processor failed: {str(e)}")


async def main():
    """Main demo function"""
    print("Welcome to the Hybrid Search Demo!")
    print("This demo tests the image + text search functionality.")
    print()
    
    # Test individual components first
    await test_simple_components()
    
    # Test complete pipeline
    await test_hybrid_search()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("Please check your environment variables and dependencies.") 