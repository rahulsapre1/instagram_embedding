"""
Account type classifier using CLIP embeddings.
"""
import numpy as np
from typing import List, Dict
from query_embedding.embedder import QueryEmbedder

class AccountTypeClassifier:
    def __init__(self, embedder: QueryEmbedder = None):
        """
        Initialize account type classifier.
        
        Args:
            embedder: Optional QueryEmbedder instance to reuse
        """
        self.embedder = embedder or QueryEmbedder()
        
        # Example queries for each account type
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
        
        # Pre-compute embeddings
        self.brand_embeddings = np.stack([
            self.embedder.embed_query(q) 
            for q in self.brand_queries
        ])
        
        self.human_embeddings = np.stack([
            self.embedder.embed_query(q) 
            for q in self.human_queries
        ])
        
    def classify_account(self, profile_embedding: np.ndarray) -> str:
        """
        Classify account as 'human' or 'brand' using embedding similarity.
        
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
        
    def classify_accounts(self, profile_embeddings: Dict[str, np.ndarray]) -> Dict[str, str]:
        """
        Classify multiple accounts using their embeddings.
        
        Args:
            profile_embeddings: Dictionary mapping usernames to embeddings
            
        Returns:
            Dictionary mapping usernames to account types
        """
        return {
            username: self.classify_account(embedding)
            for username, embedding in profile_embeddings.items()
        }