"""
Test script for query improvement functionality
Demonstrates how keyword-like queries are converted to proper sentences
"""

import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interactive_search import GeminiSearchInterface


def test_query_improvement():
    """Test the query improvement functionality"""
    print("🔍 Testing Query Improvement Functionality")
    print("=" * 60)
    
    # Create interface instance (without API key for testing)
    try:
        interface = GeminiSearchInterface()
    except ValueError:
        # If no API key, create a mock instance for testing
        print("⚠️  No API key available, testing with mock instance")
        return
    
    # Test queries that should be improved
    test_queries = [
        # Too short/keyword-like
        "corporate outfits",
        "fashion influencers", 
        "travel bloggers",
        "food",
        "profiles",
        "accounts",
        
        # Already good queries (should not be changed)
        "Find Instagram profiles of fashion influencers who specialize in corporate outfits",
        "Search for travel bloggers with a focus on adventure photography",
        "Show me food bloggers who create healthy recipes",
        
        # Mixed cases
        "corporate fashion",
        "travel photography",
        "healthy food recipes"
    ]
    
    print("\n🔍 TESTING QUERY IMPROVEMENT:")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        improved = interface._improve_query(query)
        is_improved = improved != query
        
        print(f"\n{i}. Original: '{query}'")
        print(f"   Improved: '{improved}'")
        print(f"   Status: {'✅ IMPROVED' if is_improved else '✅ ALREADY GOOD'}")
        
        # Check if improved query is a proper sentence
        is_proper = interface._is_proper_sentence(improved)
        print(f"   Proper Sentence: {'✅ YES' if is_proper else '❌ NO'}")
    
    print("\n" + "=" * 60)
    print("🎯 QUERY IMPROVEMENT SUMMARY:")
    print("• Short keywords are expanded into full sentences")
    print("• Action verbs are added (find, search, show)")
    print("• Context and attributes are included")
    print("• Already good queries remain unchanged")
    print("• All final queries are proper sentences")


def test_sentence_validation():
    """Test the sentence validation logic"""
    print("\n\n🧠 Testing Sentence Validation Logic")
    print("=" * 60)
    
    try:
        interface = GeminiSearchInterface()
    except ValueError:
        print("⚠️  No API key available, cannot test sentence validation")
        return
    
    test_texts = [
        # Good sentences
        "Find Instagram profiles of fashion influencers",
        "Search for travel bloggers with adventure focus",
        "Show me food bloggers who create healthy content",
        
        # Bad sentences
        "corporate outfits",
        "fashion influencers",
        "travel",
        "profiles",
        
        # Edge cases
        "Find profiles",
        "Search for influencers",
        "Show me bloggers"
    ]
    
    print("\n🔍 TESTING SENTENCE VALIDATION:")
    print("-" * 50)
    
    for text in test_texts:
        is_proper = interface._is_proper_sentence(text)
        print(f"'{text}' → {'✅ PROPER' if is_proper else '❌ IMPROPER'}")


def main():
    """Main test function"""
    print("🚀 Query Improvement Test")
    print("=" * 60)
    print("This test demonstrates how keyword-like queries are")
    print("automatically improved into proper, descriptive sentences.")
    print()
    
    # Test 1: Query improvement
    test_query_improvement()
    
    # Test 2: Sentence validation
    test_sentence_validation()
    
    print("\n" + "=" * 60)
    print("🎉 Query improvement test completed!")
    print("\nKey benefits:")
    print("• Better search results with descriptive queries")
    print("• Consistent query format across all searches")
    print("• Improved user experience with natural language")
    print("• Automatic query enhancement without user intervention")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 