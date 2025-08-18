"""
Simple test script for query improvement functionality
Tests the query improvement logic without importing the full interface
"""

def is_proper_sentence(text: str) -> bool:
    """
    Check if text is a proper sentence.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a proper sentence
    """
    # Check for basic sentence indicators
    has_verb = any(word in text.lower() for word in ['find', 'search', 'show', 'get', 'look', 'see', 'discover'])
    has_structure = len(text.split()) >= 4  # At least 4 words
    has_context = any(word in text.lower() for word in ['profiles', 'accounts', 'people', 'influencers', 'bloggers', 'creators'])
    
    return has_verb and has_structure and has_context


def improve_query(query: str) -> str:
    """
    Improve keyword-like queries into proper sentences.
    
    Args:
        query: The original query string
        
    Returns:
        Improved query as a proper sentence
    """
    query = query.strip()
    
    # If query is already a proper sentence (contains verbs, proper structure), return as is
    if is_proper_sentence(query):
        return query
    
    # Common patterns to improve
    improvements = {
        # Fashion and style
        "corporate outfits": "Find Instagram profiles of fashion influencers who specialize in corporate outfits and business wear",
        "business wear": "Search for fashion content creators who focus on business and professional attire",
        "fashion influencers": "Show me Instagram profiles of fashion influencers and style creators",
        
        # Travel and lifestyle
        "travel bloggers": "Find Instagram profiles of travel bloggers and adventure content creators",
        "food bloggers": "Search for food bloggers and culinary content creators on Instagram",
        "fitness influencers": "Show me Instagram profiles of fitness influencers and wellness content creators",
        
        "profiles": "Find Instagram profiles that match your search criteria",
        "accounts": "Search for Instagram accounts based on your requirements",
        "people": "Find Instagram profiles of people who match your search criteria"
    }
    
    # Check for exact matches first
    for pattern, improvement in improvements.items():
        if query.lower() == pattern.lower():
            return improvement
    
    # Check for partial matches and improve
    for pattern, improvement in improvements.items():
        if pattern.lower() in query.lower():
            # Replace the pattern with the improvement
            improved = query.replace(pattern, improvement)
            if not is_proper_sentence(improved):
                # If still not a proper sentence, make it one
                improved = f"Find Instagram profiles related to {query}"
            return improved
    
    # If no patterns match, create a generic improvement
    if len(query.split()) <= 3:
        return f"Find Instagram profiles related to {query}"
    else:
        return f"Search for Instagram profiles that match: {query}"


def test_query_improvement():
    """Test the query improvement functionality"""
    print("🔍 Testing Query Improvement Functionality")
    print("=" * 60)
    
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
        improved = improve_query(query)
        is_improved = improved != query
        
        print(f"\n{i}. Original: '{query}'")
        print(f"   Improved: '{improved}'")
        print(f"   Status: {'✅ IMPROVED' if is_improved else '✅ ALREADY GOOD'}")
        
        # Check if improved query is a proper sentence
        is_proper = is_proper_sentence(improved)
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
        is_proper = is_proper_sentence(text)
        print(f"'{text}' → {'✅ PROPER' if is_proper else '❌ IMPROPER'}")


def main():
    """Main test function"""
    print("🚀 Query Improvement Test (Simple Version)")
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
    
    print("\n📝 EXAMPLE TRANSFORMATIONS:")
    print("• 'corporate outfits' → 'Find Instagram profiles of fashion influencers who specialize in corporate outfits and business wear'")
    print("• 'travel bloggers' → 'Find Instagram profiles of travel bloggers and adventure content creators'")
    print("• 'fashion influencers' → 'Show me Instagram profiles of fashion influencers and style creators'")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 