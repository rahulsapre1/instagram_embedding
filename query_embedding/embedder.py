"""
Text embedding using Jina CLIP model for natural language queries.
"""
import os
import logging
from typing import Optional
import numpy as np
import torch
from transformers import AutoModel, AutoProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueryEmbedder:
    def __init__(self, model_name: str = "jinaai/jina-clip-v2", device: Optional[str] = None):
        """
        Initialize CLIP model for query embedding.
        
        Args:
            model_name: Name of the CLIP model to use
            device: Device to run model on ('cuda' or 'cpu'). If None, automatically detect.
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"Loading {model_name} on {self.device}...")
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model.to(self.device)
        self.model.eval()
        print("Model loaded successfully!")

    def embed_query(self, query: str, output_dim: int = 128) -> np.ndarray:
        """
        Generate embedding for a natural language query.
        
        Args:
            query: Natural language query text
            output_dim: Output embedding dimension (must match stored vectors)
            
        Returns:
            Query embedding vector
        """
        try:
            # Process text
            inputs = self.processor(
                text=[query],
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                embeddings = self.model.get_text_features(
                    **inputs,
                    normalize=True
                )
                
                # Reduce dimension if needed
                if output_dim != embeddings.shape[1]:
                    print(f"Reducing dimension from {embeddings.shape[1]} to {output_dim}")
                    embeddings = embeddings[:, :output_dim]
                
                # Convert to numpy and ensure shape
                embeddings = embeddings.cpu().numpy()
                
                # Return first (and only) embedding
                return embeddings[0]
                
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise