"""
Test script for complete hybrid search using a working image URL
"""

import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from query_embedding.hybrid_search import HybridSearchEngine


async def test_working_hybrid_search():
    """Test hybrid search with a working image URL"""
    print("🚀 Working Hybrid Search Test")
    print("=" * 60)
    
    # Use the working image URL from our previous test
    working_url = "https://httpbin.org/image/jpeg"
    test_queries = [
        "find similar profiles",
        "search for travel accounts",
        "profiles with similar style"
    ]
    
    print(f"🖼️  Working Image URL: {working_url}")
    print("=" * 60)
    
    try:
        # Initialize hybrid search engine
        hybrid_engine = HybridSearchEngine()
        print("✅ HybridSearchEngine initialized")
        
        # Test with different queries
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            print("-" * 40)
            
            try:
                print("🤖 Analyzing query intent and generating weights...")
                results, weights = await hybrid_engine.search(working_url, query)
                
                print(f"✅ Search completed!")
                print(f"  Weights: Image={weights['image_weight']:.1f}, Text={weights['text_weight']:.1f}")
                print(f"  Results: {len(results)} profiles found")
                
                if results:
                    print("  Top 3 results:")
                    for j, result in enumerate(results[:3], 1):
                        payload = result.payload
                        print(f"    {j}. {payload.get('username', 'N/A')} "
                              f"({payload.get('full_name', 'N/A')}) - "
                              f"Score: {result.score:.3f}")
                else:
                    print("  No results found")
                
            except Exception as e:
                print(f"❌ Search failed: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function"""
    print("Welcome to the Working Hybrid Search Test!")
    print("This test uses a verified working image URL.")
    print()
    
    await test_working_hybrid_search()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}") 