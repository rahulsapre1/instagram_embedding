"""
Test script for enhanced weight analyzer with image similarity intent detection
"""

import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from query_embedding.weight_analyzer import WeightAnalyzer


def test_fallback_weights():
    """Test fallback weight assignment without API calls"""
    print("🧠 Testing Enhanced Fallback Weight Assignment")
    print("=" * 60)
    
    # Test queries that should get very high image weights
    very_high_image_queries = [
        "similar to this",
        "like this image", 
        "matching this",
        "same style as this",
        "looks like this",
        "resembles this",
        "comparable to this",
        "in the style of this",
        "based on this image",
        "find profiles like this",
        "show me similar to this",
        "who looks like this",
        "profiles matching this"
    ]
    
    # Test queries with multiple high-image keywords
    multi_keyword_queries = [
        "similar style and appearance",
        "matching look and style",
        "comparable appearance and style",
        "similar matching profiles"
    ]
    
    # Test regular queries
    regular_queries = [
        "find similar profiles",
        "search for travel accounts",
        "profiles with similar style",
        "find people like this",
        "search for fashion influencers"
    ]
    
    print("\n🔍 VERY HIGH IMAGE WEIGHT QUERIES (0.9, 0.1):")
    print("-" * 50)
    for query in very_high_image_queries:
        weights = WeightAnalyzer().get_fallback_weights(query)
        print(f"'{query}' → Image: {weights['image_weight']:.1f}, Text: {weights['text_weight']:.1f}")
    
    print("\n🔍 MULTI-KEYWORD HIGH IMAGE QUERIES (0.9, 0.1):")
    print("-" * 50)
    for query in multi_keyword_queries:
        weights = WeightAnalyzer().get_fallback_weights(query)
        print(f"'{query}' → Image: {weights['image_weight']:.1f}, Text: {weights['text_weight']:.1f}")
    
    print("\n🔍 REGULAR QUERIES (Variable weights):")
    print("-" * 50)
    for query in regular_queries:
        weights = WeightAnalyzer().get_fallback_weights(query)
        print(f"'{query}' → Image: {weights['image_weight']:.1f}, Text: {weights['text_weight']:.1f}")


def test_very_high_intent_detection():
    """Test the very high image intent detection method"""
    print("\n\n🎯 Testing Very High Image Intent Detection")
    print("=" * 60)
    
    analyzer = WeightAnalyzer()
    
    test_queries = [
        "similar to this",
        "like this image",
        "matching this style",
        "find similar profiles",
        "search for travel accounts",
        "profiles with similar style and appearance",
        "show me people like this",
        "who looks like this image"
    ]
    
    for query in test_queries:
        high_intent_weights = analyzer._check_very_high_image_intent(query)
        if high_intent_weights:
            print(f"✅ '{query}' → Very High Image Intent: {high_intent_weights}")
        else:
            print(f"❌ '{query}' → No Very High Image Intent detected")


async def test_gemini_integration():
    """Test Gemini integration (requires API key)"""
    print("\n\n🤖 Testing Gemini Integration")
    print("=" * 60)
    
    try:
        analyzer = WeightAnalyzer()
        print("✅ WeightAnalyzer initialized with API key")
        
        # Test a query that should get very high image weight
        test_query = "similar to this image"
        print(f"\nTesting query: '{test_query}'")
        
        weights = await analyzer.get_weights(test_query)
        print(f"Result: {weights}")
        
        if weights['image_weight'] >= 0.9:
            print("✅ Successfully assigned very high image weight!")
        else:
            print("⚠️  Expected very high image weight but got different result")
            
    except ValueError as e:
        print(f"❌ API key not available: {e}")
        print("   This is expected if GEMINI_API_KEY is not set")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def main():
    """Main test function"""
    print("🚀 Enhanced Weight Analyzer Test")
    print("=" * 60)
    print("This test demonstrates the enhanced weight analyzer with")
    print("image similarity intent detection capabilities.")
    print()
    
    # Test 1: Fallback weights (no API required)
    test_fallback_weights()
    
    # Test 2: Very high intent detection (no API required)
    test_very_high_intent_detection()
    
    # Test 3: Gemini integration (requires API key)
    await test_gemini_integration()
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced weight analyzer test completed!")
    print("\nKey improvements:")
    print("• Very high image weight detection (0.9, 0.1)")
    print("• Priority handling for image similarity intent")
    print("• Enhanced fallback weight assignment")
    print("• Better phrase matching for image-focused queries")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}") 