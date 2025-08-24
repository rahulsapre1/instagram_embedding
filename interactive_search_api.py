#!/usr/bin/env python3
"""
API Wrapper for Interactive Search
Provides a non-interactive interface to the interactive_search.py functionality
"""

import sys
import json
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import logging
from typing import List, Dict, Any, Optional

# Import the working CLI components
from interactive_search import SearchContext, GeminiSearchInterface

# Add the current directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to suppress unnecessary output
logging.basicConfig(level=logging.ERROR)

def process_single_query(user_input, conversation_history):
    """Process a single query using the working CLI logic."""
    try:
        # Initialize the Gemini interface
        gemini_interface = GeminiSearchInterface()
        
        # Initialize search context from conversation history
        search_context = SearchContext()
        if conversation_history:
            search_context.conversation_history = conversation_history
        
        # Add the new user message
        search_context.add_conversation('user', user_input)
        
        # Build conversation context for the AI
        conversation_context = _build_conversation_context(search_context.conversation_history)
        
        # Create the system prompt
        system_prompt = f"""You are an intelligent search assistant for an Instagram profile database. Your role is to help users build search queries incrementally through conversation.

AVAILABLE SEARCH FILTERS:
- follower_category: nano (1K-10K), micro (10K-100K), macro (100K-1M), mega (1M+)
- account_type: human, brand
- min_followers: minimum follower count
- max_followers: maximum follower count
- limit: maximum results (default: 20)
- threshold: minimum similarity score (default: 0.0)

SEARCH BEHAVIOR:
- Build queries incrementally based on user conversation
- Remember and apply previous search criteria
- Always trigger a search when user provides input
- Return search results in a helpful format

{conversation_context}

User: {user_input}

Assistant: I'll help you search for Instagram profiles. Let me execute the search based on our conversation context."""
        
        # Generate response using Gemini
        response = gemini_interface.model.generate_content(system_prompt)
        assistant_response = response.text.strip()
        
        # ALWAYS trigger search - use the working CLI logic
        should_search = True
        
        # Build the search query using the working context builder
        search_query = _build_comprehensive_query(user_input, conversation_history)
        
        # Execute the actual search using the existing search logic
        try:
            # Import and use the working search engine
            from query_embedding.qdrant_utils import QdrantSearcher
            
            # Initialize search engine
            search_engine = QdrantSearcher()
            
            # Execute search with the query
            search_results = search_engine.search(
                query=search_query,
                limit=20
            )
            
            # Format results for frontend
            formatted_results = []
            for result in search_results:
                payload = result.payload
                formatted_results.append({
                    "username": payload.get("username", ""),
                    "full_name": payload.get("full_name", ""),
                    "bio": payload.get("bio", ""),
                    "follower_count": payload.get("follower_count", 0),
                    "category": payload.get("category", ""),
                    "account_type": payload.get("account_type", "human"),
                    "influencer_type": payload.get("influencer_type", ""),
                    "score": result.score,
                    "is_private": payload.get("is_private", False)
                })
            
            return {
                "response": assistant_response,
                "should_search": should_search,
                "search_query": search_query,
                "results": formatted_results,
                "total": len(formatted_results),
                "success": True
            }
            
        except ImportError:
            # Fallback if search engine not available
            return {
                "response": assistant_response,
                "should_search": should_search,
                "search_query": search_query,
                "results": [],
                "total": 0,
                "success": True,
                "note": "Search engine not available, but query was built successfully"
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "response": f"I encountered an error processing your request: {str(e)}",
            "should_search": False,
            "success": False
        }

def _compose_concise_query(conversation_history, user_input):
    """Use the LLM to compose a single-line, concise search query from history + latest input.
    Returns None on failure so callers can fallback.
    """
    try:
        if conversation_history is None:
            return None
        # Build a compact textual history
        history_lines = []
        recent_history = conversation_history[-12:]  # keep it short but enough context
        for msg in recent_history:
            role = msg.get("role", "user")
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            history_lines.append(f"{role}: {content}")
        history_text = "\n".join(history_lines)

        system_guidance = (
            "You are a search-query composer.\n"
            "Given the entire previous chat and the latest user message, produce ONE concise, natural-language search query that preserves ALL prior constraints and inferred intent.\n"
            "Rules:\n"
            "- Output ONLY the final query as a single line. No JSON, no extra text.\n"
            "- Do not include verbs like 'find', 'search', 'show', 'get'.\n"
            "- Preserve locations, categories (e.g., fitness, fashion), genders, styles, follower ranges, and any other constraints mentioned previously.\n"
            "- Do not add any default geography (e.g., Australian) unless explicitly present in conversation.\n"
            "- Keep it succinct and readable. Use lowercase except proper nouns and place names.\n"
        )

        prompt = (
            f"{system_guidance}\n\n"
            f"Conversation so far:\n{history_text}\n\n"
            f"Latest user message:\nuser: {user_input}\n\n"
            f"Return only the final query line:"
        )

        response = gemini_interface.model.generate_content(prompt)
        raw = (response.text or "").strip()
        # Normalize to one line, strip quotes
        query_line = raw.replace("\n", " ").strip().strip('"\'')
        if not query_line:
            return None
        # Guardrails: avoid leading helper verbs
        forbidden_prefixes = (
            "find ", "search ", "show ", "get ", "look ", "see ", "discover ",
        )
        lowered = query_line.lower()
        for pref in forbidden_prefixes:
            if lowered.startswith(pref):
                query_line = query_line[len(pref):].strip()
                break
        return query_line
    except Exception:
        # Any issue -> let caller fallback
        return None

def _build_conversation_context(conversation_history):
    """Build conversation context exactly like CLI version."""
    context_parts = []
    
    # Add recent conversation history (last 10 turns)
    if conversation_history:
        context_parts.append("RECENT CONVERSATION:")
        recent_history = conversation_history[-10:]
        for turn in recent_history:
            role = "User" if turn["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {turn['content']}")
    
    return "\n".join(context_parts)

def _improve_query(query):
    """Improve keyword-like queries into proper sentences exactly like CLI version."""
    query = query.strip()
    
    # If query is already a proper sentence, return as is
    if _is_proper_sentence(query):
        return query
    
    # If it already starts with "Instagram profiles", don't wrap again
    if query.lower().startswith('instagram profiles'):
        return query
    
    # Common patterns to improve
    improvements = {
        # Fashion and style
        "corporate outfits": "fashion influencers who specialize in corporate outfits and business wear",
        "business wear": "fashion content creators who focus on business and professional attire",
        "fashion influencers": "fashion influencers and style creators",
        
        # Travel and lifestyle
        "travel bloggers": "travel bloggers and adventure content creators",
        "food bloggers": "food bloggers and culinary content creators",
        "fitness influencers": "fitness influencers and wellness content creators",
        
        "profiles": "Instagram profiles that match your search criteria",
        "accounts": "Instagram accounts based on your requirements",
        "people": "Instagram profiles of people who match your search criteria"
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
            if not _is_proper_sentence(improved):
                # If still not a proper sentence, make it one
                improved = f"Instagram profiles related to {query}"
            return improved
    
    # If no patterns match, create a generic improvement
    if len(query.split()) <= 3:
        return f"Instagram profiles related to {query}"
    else:
        return f"Instagram profiles that match: {query}"

def _is_proper_sentence(text):
    """Check if text is a proper sentence for search purposes."""
    text = text.strip()
    
    # If it already starts with "Instagram profiles", it's already been processed
    if text.lower().startswith('instagram profiles'):
        return True
    
    # If it already starts with common search prefixes, it's already been processed
    search_prefixes = ['find', 'search', 'show', 'get', 'look', 'see', 'discover']
    if any(text.lower().startswith(prefix) for prefix in search_prefixes):
        return True
    
    # Check if it's a natural language query (has at least 3 words and doesn't look like keywords)
    words = text.split()
    if len(words) >= 3:
        # Check if it contains natural language indicators
        natural_indicators = ['in', 'of', 'with', 'for', 'and', 'or', 'the', 'a', 'an']
        if any(indicator in text.lower() for indicator in natural_indicators):
            return True
    
    return False

def _parse_gemini_response(response):
    """Parse Gemini response to extract structured data exactly like CLI version."""
    try:
        # Try to extract JSON from response
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["action", "query", "filters", "explanation"]
            if all(field in parsed for field in required_fields):
                return parsed
        
        # Fallback parsing
        fallback_query = _improve_query(response.strip())
        return {
            "action": "search",
            "query": fallback_query,
            "filters": {},
            "explanation": "Parsed response as search query"
        }
        
    except json.JSONDecodeError:
        # If JSON parsing fails, treat as search query
        fallback_query = _improve_query(response.strip())
        return {
            "action": "search",
            "query": fallback_query,
            "filters": {},
            "explanation": "Parsed response as search query"
        }

def _build_comprehensive_query(user_input, conversation_history):
    """Build a comprehensive search query from conversation context."""
    if not conversation_history:
        return user_input
    
    # Extract key context from the ENTIRE conversation history
    context_keywords = []
    
    # Look at ALL messages, not just the last 3
    for msg in conversation_history:
        if msg["role"] == "user":
            content = msg["content"].lower()
            
            # Extract influencer type (keep the first one mentioned)
            if "lifestyle" in content and "lifestyle" not in context_keywords:
                context_keywords.append("lifestyle")
            elif "fitness" in content and "fitness" not in context_keywords:
                context_keywords.append("fitness")
            elif "fashion" in content and "fashion" not in context_keywords:
                context_keywords.append("fashion")
            elif "food" in content and "food" not in context_keywords:
                context_keywords.append("food")
            elif "travel" in content and "travel" not in context_keywords:
                context_keywords.append("travel")
            elif "beauty" in content and "beauty" not in context_keywords:
                context_keywords.append("beauty")
            
            # Extract style/type context (keep all relevant ones)
            if "corporate" in content:
                context_keywords.append("corporate")
            if "clothing" in content or "clothes" in content:
                context_keywords.append("clothing")
            if "outdoor" in content or "outdoors" in content:
                context_keywords.append("outdoor")
            if "healthy" in content:
                context_keywords.append("healthy")
            if "strength" in content or "strength training" in content:
                context_keywords.append("strength training")
            if "female" in content or "women" in content or "girls" in content:
                context_keywords.append("female")
            if "male" in content or "men" in content or "boys" in content:
                context_keywords.append("male")
    
    # Clean up the user input by removing common search words
    cleaned_input = user_input.lower()
    search_words = ['find', 'search', 'show', 'get', 'look', 'see', 'discover', 'looking for', 'want to find']
    for word in search_words:
        cleaned_input = cleaned_input.replace(word, '').strip()
    
    # Combine context with cleaned input intelligently
    if context_keywords:
        # Remove duplicates while preserving order
        unique_context = []
        for keyword in context_keywords:
            if keyword not in unique_context:
                unique_context.append(keyword)
        
        # Create a natural search query
        if cleaned_input:
            # If we have both context and input, combine them naturally
            if any(keyword in cleaned_input.lower() for keyword in unique_context):
                # Context is already in the input, just use the input
                search_query = cleaned_input
            else:
                # Add context to the input, but be smart about it
                if len(cleaned_input.split()) <= 2:
                    # Short input like "females only" - combine with context
                    search_query = f"{' '.join(unique_context)} {cleaned_input}"
                else:
                    # Longer input - use the input as is, context is already captured
                    search_query = cleaned_input
        else:
            # Only context available
            search_query = f"{' '.join(unique_context)} influencers"
    else:
        # No context, just use the cleaned input
        search_query = cleaned_input if cleaned_input else user_input
    
    # Only wrap if it's not already a proper sentence and hasn't been wrapped before
    if not _is_proper_sentence(search_query) and not search_query.lower().startswith('instagram profiles'):
        search_query = f"Instagram profiles of {search_query}"
    
    return search_query

def main():
    """
    Main function that reads from stdin and writes JSON response to stdout
    """
    try:
        # Read input from stdin
        if len(sys.argv) > 1:
            # Command line argument
            user_input = " ".join(sys.argv[1:])
            conversation_history = None
        else:
            # Read from stdin - expect JSON with message and optional conversation_history
            input_data = sys.stdin.read().strip()
            if not input_data:
                print(json.dumps({
                    "error": "No input provided",
                    "response": "I didn't receive any input. Please tell me what you're looking for.",
                    "should_search": False
                }))
                return
            
            try:
                # Try to parse as JSON first
                parsed_input = json.loads(input_data)
                user_input = parsed_input.get('message', '')
                conversation_history = parsed_input.get('conversation_history', None)
            except json.JSONDecodeError:
                # Fallback to plain text
                user_input = input_data
                conversation_history = None
        
        if not user_input:
            print(json.dumps({
                "error": "No message provided",
                "response": "I didn't receive any message. Please tell me what you're looking for.",
                "should_search": False
            }))
            return
        
        # Process the query
        result = process_single_query(user_input, conversation_history)
        
        # Output JSON response
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_response = {
            "error": str(e),
            "response": "I encountered an unexpected error. Please try again.",
            "should_search": False,
            "success": False
        }
        print(json.dumps(error_response, indent=2))

if __name__ == "__main__":
    main()