"""
Basic test script for hybrid search functionality
Tests core components without requiring full environment setup
"""

import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from query_embedding.hybrid_search import HybridSearchEngine
        print("✅ HybridSearchEngine imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import HybridSearchEngine: {e}")
        return False
    
    try:
        from query_embedding.weight_analyzer import WeightAnalyzer
        print("✅ WeightAnalyzer imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import WeightAnalyzer: {e}")
        return False
    
    try:
        from query_embedding.image_processor import ImageProcessor
        print("✅ ImageProcessor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ImageProcessor: {e}")
        return False
    
    return True


def test_environment():
    """Test environment variables"""
    print("\n🔧 Testing environment...")
    
    required_vars = ['GEMINI_API_KEY', 'GOOGLE_API_KEY']
    found_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            found_vars.append(var)
            print(f"✅ {var} found")
        else:
            print(f"⚠️  {var} not found")
    
    if not found_vars:
        print("❌ No API keys found. Please set GEMINI_API_KEY or GOOGLE_API_KEY")
        return False
    
    return True


async def test_weight_analyzer():
    """Test weight analyzer with mock query"""
    print("\n🧠 Testing Weight Analyzer...")
    
    try:
        from query_embedding.weight_analyzer import WeightAnalyzer
        
        analyzer = WeightAnalyzer()
        print("✅ WeightAnalyzer initialized")
        
        # Test fallback weights (doesn't require API call)
        fallback_weights = analyzer.get_fallback_weights("find similar profiles")
        print(f"✅ Fallback weights: {fallback_weights}")
        
        return True
        
    except Exception as e:
        print(f"❌ WeightAnalyzer test failed: {e}")
        return False


async def test_image_processor():
    """Test image processor initialization"""
    print("\n🖼️  Testing Image Processor...")
    
    try:
        from query_embedding.image_processor import ImageProcessor
        
        processor = ImageProcessor()
        print("✅ ImageProcessor initialized")
        
        # Test URL validation with a simple test
        is_valid = await processor.validate_image_url("https://example.com/test.jpg")
        print(f"✅ URL validation test completed (result: {is_valid})")
        
        return True
        
    except Exception as e:
        print(f"❌ ImageProcessor test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Basic Hybrid Search Test")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed. Cannot proceed.")
        return
    
    # Test 2: Environment
    if not test_environment():
        print("\n⚠️  Environment issues detected. Some tests may fail.")
    
    # Test 3: Weight Analyzer
    if not await test_weight_analyzer():
        print("\n❌ Weight Analyzer test failed.")
    
    # Test 4: Image Processor
    if not await test_image_processor():
        print("\n❌ Image Processor test failed.")
    
    print("\n" + "=" * 50)
    print("🎉 Basic tests completed!")
    print("\nNext steps:")
    print("1. Set your GEMINI_API_KEY environment variable")
    print("2. Run the full demo: python scripts/demo/hybrid_search_demo.py")
    print("3. Test in interactive mode: python interactive_search.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}") 