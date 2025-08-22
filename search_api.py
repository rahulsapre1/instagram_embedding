#!/usr/bin/env python3
"""
Search API for Instagram Profiles
Provides search functionality using Qdrant vector database
"""

import sys
import json
import os
from typing import Dict, List, Any, Optional
import io
from contextlib import redirect_stdout

# Add the current directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to suppress unnecessary output
import logging
logging.basicConfig(level=logging.ERROR)

# Global variables for caching
_embedder = None
_searcher = None

def get_cached_components():
    """Get or create cached components to avoid reloading models (suppress stdout noise)."""
    global _embedder, _searcher

    if _embedder is None:
        # Suppress stdout from model loading prints
        with redirect_stdout(io.StringIO()):
            from query_embedding.embedder import QueryEmbedder
            _embedder = QueryEmbedder()

    if _searcher is None:
        from query_embedding.qdrant_utils import QdrantSearcher
        _searcher = QdrantSearcher(top_k=100)  # Higher limit for flexibility

    return _embedder, _searcher

def search_profiles(query: str, filters: Optional[Dict] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Search for Instagram profiles using Qdrant
    """
    try:
        # Import required modules
        from query_embedding.follower_utils import FollowerCountConverter

        # Run heavy operations with stdout suppressed to avoid polluting JSON output
        with redirect_stdout(io.StringIO()):
            # Get cached components (models loaded once)
            embedder, searcher = get_cached_components()

            # Generate query embedding
            query_embedding = embedder.embed_query(query)

            # Build search filters
            search_filters = {}
            if filters:
                if 'follower_count' in filters and filters['follower_count']:
                    min_followers, max_followers = filters['follower_count']
                    search_filters['follower_count'] = (min_followers or 0, max_followers)

                if 'account_type' in filters:
                    search_filters['account_type'] = filters['account_type']

                if 'influencer_type' in filters:
                    search_filters['influencer_type'] = filters['influencer_type']

            # Perform search
            results = searcher.search(query, filters=search_filters, offset=offset, limit=limit)

            # Convert results to the expected format
            profiles = []
            for result in results:
                payload = result.payload

                # Get follower category
                follower_count = payload.get('follower_count', 0)
                category = FollowerCountConverter.get_follower_category(follower_count)

                profile = {
                    'username': payload.get('username', ''),
                    'full_name': payload.get('full_name', ''),
                    'bio': payload.get('bio', ''),
                    'follower_count': follower_count,
                    'category': category,
                    'account_type': payload.get('account_type', 'unknown'),
                    'influencer_type': payload.get('influencer_type', 'unknown'),
                    'score': float(result.score),
                    'profile_pic_url': payload.get('profile_pic_url'),
                    'is_private': payload.get('is_private', False)
                }
                profiles.append(profile)

        # Only JSON is printed to stdout below
        return {
            'results': profiles,
            'total': len(profiles),
            'has_more': len(profiles) == limit,
            'query': query
        }

    except Exception as e:
        print(f"Error in search_profiles: {str(e)}", file=sys.stderr)
        return {
            'error': str(e),
            'results': [],
            'total': 0,
            'has_more': False,
            'query': query
        }


def main():
    """
    Main function that reads from stdin and writes JSON response to stdout
    """
    try:
        # Read input from stdin
        input_data = sys.stdin.read().strip()

        if not input_data:
            print(json.dumps({
                'error': 'No input provided',
                'results': [],
                'total': 0,
                'has_more': False
            }))
            return

        # Parse input
        try:
            search_params = json.loads(input_data)
        except json.JSONDecodeError:
            print(json.dumps({
                'error': 'Invalid JSON input',
                'results': [],
                'total': 0,
                'has_more': False
            }))
            return

        # Extract parameters
        query = search_params.get('query', '')
        filters = search_params.get('filters', {})
        limit = search_params.get('limit', 20)
        offset = search_params.get('offset', 0)

        if not query:
            print(json.dumps({
                'error': 'Query is required',
                'results': [],
                'total': 0,
                'has_more': False
            }))
            return

        # Perform search
        result = search_profiles(query, filters, limit, offset)

        # Output JSON response
        print(json.dumps(result, indent=2))

    except Exception as e:
        error_response = {
            'error': str(e),
            'results': [],
            'total': 0,
            'has_more': False
        }
        print(json.dumps(error_response, indent=2))


if __name__ == "__main__":
    main()
