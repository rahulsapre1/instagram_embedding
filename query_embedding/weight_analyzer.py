"""
Weight Analyzer for Hybrid Search
Uses Google Gemini to analyze query intent and assign weights to image vs text search
"""

import os
import logging
import re
from typing import Dict, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class WeightAnalyzer:
    """
    Analyzes search queries to determine optimal weights for image vs text search
    Uses Gemini AI to understand query intent and assign weights
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.api_key = api_key
        
        if api_key:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.model = genai.GenerativeModel(model_name)
        else:
            self.model = None
    
    async def get_weights(self, query: str) -> Dict[str, float]:
        """
        Analyze query and return weights for image vs text search
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary with 'image_weight' and 'text_weight' (sum to 1.0)
        """
        try:
            # First check for very high image weight phrases (these get priority)
            high_image_weights = self._check_very_high_image_intent(query)
            if high_image_weights:
                logger.info(f"Query: '{query}' -> Very High Image Weights: {high_image_weights}")
                return high_image_weights
            
            # If no API key available, use fallback weights
            if not self.api_key or not self.model:
                logger.info("No API key available, using fallback weights")
                fallback_weights = self.get_fallback_weights(query)
                logger.info(f"Query: '{query}' -> Fallback Weights: {fallback_weights}")
                return fallback_weights
            
            # Create prompt for Gemini
            prompt = self._create_weight_prompt(query)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse the response to extract weights
            weights = self._parse_gemini_response(response_text)
            
            # Validate weights
            self._validate_weights(weights)
            
            logger.info(f"Query: '{query}' -> Gemini Weights: {weights}")
            return weights
            
        except Exception as e:
            logger.error(f"Error getting weights from Gemini: {str(e)}")
            # Fallback to keyword-based weight assignment
            fallback_weights = self.get_fallback_weights(query)
            logger.info(f"Query: '{query}' -> Fallback Weights: {fallback_weights}")
            return fallback_weights
    
    def _create_weight_prompt(self, query: str) -> str:
        """Create the prompt for Gemini to analyze query intent"""
        return f"""
        Analyze this search query and assign weights to image vs text search.
        
        Query: "{query}"
        
        Rules for weight assignment:
        - Image weight: 0.0 to 1.0 (in 0.1 increments)
        - Text weight: 1.0 - image_weight
        - Weights must sum to exactly 1.0
        
        Weight assignment guidelines for IMAGE SIMILARITY:
        - Very High image weight (0.9-1.0): "similar to this", "like this image", "matching this", "same style as this", "looks like this"
        - High image weight (0.7-0.8): "similar", "matching", "style", "look", "appearance", "like this", "resembles", "comparable to"
        - Medium image weight (0.4-0.6): "with similar", "style and", "appearance of", "inspired by", "based on"
        - Low image weight (0.0-0.3): "profiles", "accounts", "people", "search for", "find", "show me", "get"
        
        Key phrases that indicate HIGH IMAGE WEIGHT:
        - "similar to this" → image_weight: 0.9, text_weight: 0.1
        - "like this image" → image_weight: 0.9, text_weight: 0.1
        - "matching this" → image_weight: 0.9, text_weight: 0.1
        - "same style as this" → image_weight: 0.8, text_weight: 0.2
        - "find similar profiles" → image_weight: 0.8, text_weight: 0.2
        - "profiles with similar style" → image_weight: 0.7, text_weight: 0.3
        
        Examples:
        - "find similar profiles" → image_weight: 0.8, text_weight: 0.2
        - "search for travel accounts" → image_weight: 0.2, text_weight: 0.8
        - "profiles with similar style" → image_weight: 0.7, text_weight: 0.3
        - "like this image" → image_weight: 0.9, text_weight: 0.1
        - "matching this style" → image_weight: 0.9, text_weight: 0.1
        
        Return ONLY the weights in this exact format:
        image_weight: X.X, text_weight: Y.Y
        
        Where X.X and Y.Y are numbers with one decimal place that sum to 1.0
        """
    
    def _parse_gemini_response(self, response: str) -> Dict[str, float]:
        """Parse Gemini's response to extract weights"""
        try:
            # Look for the pattern "image_weight: X.X, text_weight: Y.Y"
            pattern = r'image_weight:\s*(\d+\.\d+),\s*text_weight:\s*(\d+\.\d+)'
            match = re.search(pattern, response)
            
            if match:
                image_weight = float(match.group(1))
                text_weight = float(match.group(2))
                return {"image_weight": image_weight, "text_weight": text_weight}
            
            # Fallback: look for any two decimal numbers
            numbers = re.findall(r'\d+\.\d+', response)
            if len(numbers) >= 2:
                image_weight = float(numbers[0])
                text_weight = float(numbers[1])
                return {"image_weight": image_weight, "text_weight": text_weight}
            
            # If no pattern found, try to extract numbers and assign default
            logger.warning(f"Could not parse Gemini response: {response}")
            return {"image_weight": 0.5, "text_weight": 0.5}
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return {"image_weight": 0.5, "text_weight": 0.5}
    
    def _validate_weights(self, weights: Dict[str, float]):
        """Validate that weights are valid and sum to 1.0"""
        image_weight = weights.get("image_weight", 0)
        text_weight = weights.get("text_weight", 0)
        
        # Check weight ranges
        if not (0.0 <= image_weight <= 1.0):
            raise ValueError(f"Image weight must be between 0.0 and 1.0, got {image_weight}")
        
        if not (0.0 <= text_weight <= 1.0):
            raise ValueError(f"Text weight must be between 0.0 and 1.0, got {text_weight}")
        
        # Check weight increments (0.1)
        if abs(image_weight - round(image_weight * 10) / 10) > 0.001:
            raise ValueError(f"Image weight must be in 0.1 increments, got {image_weight}")
        
        if abs(text_weight - round(text_weight * 10) / 10) > 0.001:
            raise ValueError(f"Text weight must be in 0.1 increments, got {text_weight}")
        
        # Check sum equals 1.0
        if abs(image_weight + text_weight - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {image_weight} + {text_weight} = {image_weight + text_weight}")
    
    def _check_very_high_image_intent(self, query: str) -> Optional[Dict[str, float]]:
        """
        Check if query indicates very high image weight intent
        These queries get priority and bypass Gemini analysis
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary with very high image weights or None if not applicable
        """
        query_lower = query.lower()
        
        # Very high image weight phrases that indicate strong image similarity intent
        very_high_image_phrases = [
            'similar to this', 'like this image', 'matching this', 
            'same style as this', 'looks like this', 'resembles this',
            'comparable to this', 'in the style of this', 'based on this image',
            'find profiles like this', 'show me similar to this',
            'who looks like this', 'profiles matching this'
        ]
        
        # Check for exact phrase matches
        for phrase in very_high_image_phrases:
            if phrase in query_lower:
                return {"image_weight": 0.9, "text_weight": 0.1}
        
        # Check for combination of high-image keywords
        high_image_keywords = ['similar', 'matching', 'style', 'look', 'appearance', 'resembles', 'comparable']
        high_image_count = sum(1 for kw in high_image_keywords if kw in query_lower)
        
        # If multiple high-image keywords are present, assign very high weight
        if high_image_count >= 2:
            return {"image_weight": 0.9, "text_weight": 0.1}
        
        return None
    
    def get_fallback_weights(self, query: str) -> Dict[str, float]:
        """
        Fallback weight assignment based on simple keyword matching
        Used when Gemini is unavailable
        """
        query_lower = query.lower()
        
        # Very high image weight phrases (0.9-1.0)
        very_high_image_phrases = [
            'similar to this', 'like this image', 'matching this', 
            'same style as this', 'looks like this', 'resembles this'
        ]
        
        # High image weight keywords (0.7-0.8)
        high_image_keywords = ['similar', 'matching', 'style', 'look', 'appearance', 'resembles', 'comparable']
        
        # Medium image weight keywords (0.4-0.6)
        medium_image_keywords = ['with similar', 'style and', 'appearance of', 'inspired by', 'based on']
        
        # Low image weight keywords (0.0-0.3)
        text_keywords = ['profiles', 'accounts', 'people', 'search for', 'find', 'show me', 'get']
        
        # Check for very high image weight phrases first
        for phrase in very_high_image_phrases:
            if phrase in query_lower:
                return {"image_weight": 0.9, "text_weight": 0.1}
        
        # Calculate scores for other categories
        high_image_score = sum(1 for kw in high_image_keywords if kw in query_lower)
        medium_image_score = sum(1 for kw in medium_image_keywords if kw in query_lower)
        text_score = sum(1 for kw in text_keywords if kw in query_lower)
        
        # Weight calculation with emphasis on image similarity
        if high_image_score > 0:
            # High image weight queries
            image_weight = min(0.8, 0.6 + (high_image_score * 0.1))
        elif medium_image_score > 0:
            # Medium image weight queries
            image_weight = min(0.6, 0.4 + (medium_image_score * 0.1))
        else:
            # Low image weight queries
            image_weight = max(0.1, 0.3 - (text_score * 0.1))
        
        # Round to 0.1 increments
        image_weight = round(image_weight, 1)
        text_weight = round(1.0 - image_weight, 1)
        
        # Ensure weights sum to 1.0
        if abs(image_weight + text_weight - 1.0) > 0.001:
            text_weight = round(1.0 - image_weight, 1)
        
        return {"image_weight": image_weight, "text_weight": text_weight}


# Test function
async def test_weight_analyzer():
    """Test the weight analyzer with sample queries"""
    analyzer = WeightAnalyzer()
    
    test_queries = [
        "find similar profiles",
        "search for travel accounts", 
        "profiles with similar style",
        "find people like this",
        "search for fashion influencers"
    ]
    
    for query in test_queries:
        try:
            weights = await analyzer.get_weights(query)
            print(f"Query: '{query}' -> {weights}")
        except Exception as e:
            print(f"Error with query '{query}': {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_weight_analyzer()) 