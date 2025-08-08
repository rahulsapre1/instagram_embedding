"""
Account type classifier using CLIP embeddings and Gemini 2.5 Flash-Lite.
"""
import os
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv
from query_embedding.embedder import QueryEmbedder

# Load environment variables
load_dotenv()

class AccountTypeClassifier:
    def __init__(self, embedder: QueryEmbedder = None):
        """
        Initialize account type classifier with both CLIP and Gemini.
        
        Args:
            embedder: Optional QueryEmbedder instance to reuse
        """
        self.embedder = embedder or QueryEmbedder()
        
        # Initialize Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be set in .env")
            
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel(self.gemini_model)
        
        # Rate limiting for Gemini (10 RPM, 250000 TPM, 1000 RPD)
        self.last_request_time = 0
        self.requests_per_minute = 0
        self.requests_per_day = 0
        self.day_start = time.time()
        self.minute_start = time.time()
        self.max_rpm = 10  # Gemini free tier limit
        
        # Example queries for each account type (CLIP method)
        self.brand_queries = [
            "this is a business account",
            "company profile page",
            "brand account",
            "official business profile",
            "corporate instagram account"
        ]
        
        self.human_queries = [
            "this is a personal account",
            "individual profile",
            "human user account",
            "personal instagram profile",
            "real person's account"
        ]
        
        # Pre-compute embeddings for CLIP method
        self.brand_embeddings = np.stack([
            self.embedder.embed_query(q) 
            for q in self.brand_queries
        ])
        
        self.human_embeddings = np.stack([
            self.embedder.embed_query(q) 
            for q in self.human_queries
        ])
        
    def _check_rate_limits(self):
        """Check and enforce Gemini rate limits."""
        current_time = time.time()
        
        # Reset daily counter if new day
        if current_time - self.day_start > 86400:  # 24 hours
            self.requests_per_day = 0
            self.day_start = current_time
            
        # Check daily limit
        if self.requests_per_day >= 1000:
            raise Exception("Daily rate limit exceeded (1000 requests)")
            
        # Reset minute counter if new minute
        if current_time - self.minute_start > 60:
            self.requests_per_minute = 0
            self.minute_start = current_time
            
        # Check minute limit
        if self.requests_per_minute >= self.max_rpm:
            sleep_time = 60 - (current_time - self.minute_start)
            print(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
            self.requests_per_minute = 0
            self.minute_start = time.time()
            
        self.last_request_time = current_time
        self.requests_per_minute += 1
        self.requests_per_day += 1
        
    def _classify_with_gemini(self, profile_data: Dict) -> str:
        """
        Classify account using Gemini 2.5 Flash-Lite.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            'human', 'brand', or 'unknown'
        """
        try:
            self._check_rate_limits()
            
            # Prepare profile information for Gemini
            username = profile_data.get('username', '')
            full_name = profile_data.get('full_name', '')
            bio = profile_data.get('bio', '')
            captions = profile_data.get('captions', [])
            
            # Create prompt for Gemini
            prompt = f"""
            Analyze this Instagram profile and classify it as either 'human' or 'brand':
            
            Username: {username}
            Full Name: {full_name}
            Bio: {bio}
            
            Recent Post Captions:
            {chr(10).join([f"- {caption}" for caption in captions[:5]]) if captions else "No captions available"}
            
            Instructions:
            - A 'human' account is a personal account belonging to an individual person
            - A 'brand' account is a business, company, organization, or commercial entity
            - Look for indicators like business language, promotional content, company names, etc.
            - If the account seems to be a personal account of a real person, classify as 'human'
            - If the account represents a business, brand, or organization, classify as 'brand'
            
            Respond with ONLY one word: 'human' or 'brand'
            """
            
            response = self.gemini_model.generate_content(prompt)
            result = response.text.strip().lower()
            
            if result in ['human', 'brand']:
                return result
            else:
                print(f"Unexpected Gemini response: '{result}'")
                return 'unknown'
                
        except Exception as e:
            print(f"Error in Gemini classification: {str(e)}")
            return 'unknown'
    
    def _classify_with_clip(self, profile_embedding: np.ndarray) -> str:
        """
        Classify account using CLIP embeddings (existing method).
        
        Args:
            profile_embedding: Profile embedding vector
            
        Returns:
            'human' or 'brand'
        """
        # Calculate similarities
        brand_sims = np.mean([
            np.dot(profile_embedding, brand_emb)
            for brand_emb in self.brand_embeddings
        ])
        
        human_sims = np.mean([
            np.dot(profile_embedding, human_emb)
            for human_emb in self.human_embeddings
        ])
        
        # Return type with highest similarity
        return 'brand' if brand_sims > human_sims else 'human'
        
    def classify_account(self, profile_embedding: np.ndarray, profile_data: Dict) -> str:
        """
        Classify account using hybrid approach (CLIP + Gemini).
        
        Args:
            profile_embedding: Profile embedding vector
            profile_data: Dictionary containing profile information for Gemini
            
        Returns:
            'human', 'brand', or 'unknown'
        """
        # Get classification from both methods
        clip_result = self._classify_with_clip(profile_embedding)
        gemini_result = self._classify_with_gemini(profile_data)
        
        print(f"CLIP classification: {clip_result}")
        print(f"Gemini classification: {gemini_result}")
        
        # If both methods agree, return the result
        if clip_result == gemini_result:
            return clip_result
        else:
            return 'unknown'
        
    def classify_accounts(self, profile_embeddings: Dict[str, np.ndarray], 
                         profile_data: Dict[str, Dict]) -> Dict[str, str]:
        """
        Classify multiple accounts using hybrid approach.
        
        Args:
            profile_embeddings: Dictionary mapping usernames to embeddings
            profile_data: Dictionary mapping usernames to profile data
            
        Returns:
            Dictionary mapping usernames to account types
        """
        results = {}
        
        for username, embedding in profile_embeddings.items():
            print(f"\n🔍 Classifying account: {username}")
            print("=" * 50)
            
            data = profile_data.get(username, {})
            account_type = self.classify_account(embedding, data)
            results[username] = account_type
            
            print(f"Final classification: {account_type}")
            
        return results