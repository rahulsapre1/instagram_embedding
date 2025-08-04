"""
CLIP model integration for generating embeddings from images and text.
"""
import os
from typing import List, Dict, Union, Optional, Tuple
import numpy as np
from PIL import Image
import torch
from transformers import AutoModel, AutoProcessor
from tqdm import tqdm

class CLIPEmbedder:
    def __init__(self, model_name: str = "jinaai/jina-clip-v2", device: Optional[str] = None):
        """
        Initialize CLIP embedder with specified model.
        
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
        self.model.eval()  # Set model to evaluation mode
        print("Model and processor loaded successfully!")

    def embed_images(
        self,
        images: List[Image.Image],
        batch_size: int = 32,
        output_dim: int = 128,
        normalize: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings for a list of images.
        
        Args:
            images: List of PIL images
            batch_size: Batch size for processing
            output_dim: Output embedding dimension
            normalize: Whether to L2-normalize embeddings
            
        Returns:
            List of image embeddings
        """
        all_embeddings = []
        
        for i in tqdm(range(0, len(images), batch_size), desc="Embedding images"):
            batch = images[i:i + batch_size]
            with torch.no_grad():
                print(f"Processing batch of {len(batch)} images")
                print(f"First image size: {batch[0].size}")
                
                # Process images
                inputs = self.processor(
                    images=batch,
                    return_tensors="pt",
                    padding=True
                ).to(self.device)
                
                # Get embeddings
                embeddings = self.model.get_image_features(
                    **inputs,
                    normalize=normalize
                )
                
                # Reduce dimension if needed
                if output_dim != embeddings.shape[1]:
                    print(f"Reducing dimension from {embeddings.shape[1]} to {output_dim}")
                    embeddings = embeddings[:, :output_dim]
                print(f"Raw embeddings shape: {embeddings.shape}")
                embeddings = embeddings.cpu().numpy()
                print(f"Numpy embeddings shape: {embeddings.shape}")
                all_embeddings.append(embeddings)
                print(f"Current all_embeddings length: {len(all_embeddings)}")
                
        return all_embeddings

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        output_dim: int = 128,
        normalize: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings for a list of text strings.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            output_dim: Output embedding dimension
            normalize: Whether to L2-normalize embeddings
            
        Returns:
            List of text embeddings
        """
        all_embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding texts"):
            batch = texts[i:i + batch_size]
            with torch.no_grad():
                # Process text
                inputs = self.processor(
                    text=batch,
                    return_tensors="pt",
                    padding=True
                ).to(self.device)
                
                # Get embeddings
                embeddings = self.model.get_text_features(
                    **inputs,
                    normalize=normalize
                )
                
                # Reduce dimension if needed
                if output_dim != embeddings.shape[1]:
                    print(f"Reducing dimension from {embeddings.shape[1]} to {output_dim}")
                    embeddings = embeddings[:, :output_dim]
                print(f"Raw text embeddings shape: {embeddings.shape}")
                embeddings = embeddings.cpu().numpy()
                print(f"Numpy text embeddings shape: {embeddings.shape}")
                all_embeddings.append(embeddings)
                print(f"Current text all_embeddings length: {len(all_embeddings)}")
                
        return all_embeddings

    def process_profile(
        self,
        profile_pic: Optional[Image.Image],
        post_images: List[Image.Image],
        captions: List[str],
        bio: Optional[str] = None,
        output_dim: int = 128
    ) -> Dict[str, Union[np.ndarray, List[np.ndarray]]]:
        """
        Generate separate embeddings for each profile component.
        
        Args:
            profile_pic: Profile picture (PIL Image)
            post_images: List of post images
            captions: List of post captions
            bio: Profile bio text
            output_dim: Output embedding dimension
            
        Returns:
            Dictionary containing embeddings for each component
        """
        print("\n🔄 Starting Embedding Generation")
        print("=" * 40)
        
        all_vectors = []
        weights = []
        
        # Profile picture embedding (weight: 2)
        if profile_pic:
            print("\n📸 Processing Profile Picture")
            print("-" * 30)
            print(f"Image size: {profile_pic.size}")
            profile_pic_embeddings = self.embed_images(
                [profile_pic],
                output_dim=output_dim
            )
            profile_pic_embedding = profile_pic_embeddings[0][0]  # Get first (and only) embedding
            all_vectors.append(profile_pic_embedding)
            weights.append(2.0)
            print(f"✅ Profile picture embedding generated: shape {profile_pic_embedding.shape}")
        else:
            print("⚠️  No profile picture to process")
        
        # Post images embeddings (weight: 1 each)
        if post_images:
            print(f"\n🖼️  Processing {len(post_images)} Post Images")
            print("-" * 30)
            for i, img in enumerate(post_images):
                print(f"  Post {i+1}: size {img.size}")
            
            post_embeddings = self.embed_images(
                post_images,
                output_dim=output_dim
            )
            post_vectors = post_embeddings[0]  # Get the first (and only) batch
            all_vectors.extend(post_vectors)
            weights.extend([1.0] * len(post_vectors))
            print(f"✅ Generated {len(post_vectors)} post embeddings")
            print(f"  Vector shape: {post_vectors[0].shape}")
        else:
            print("⚠️  No post images to process")
        
        # Caption embeddings (weight: 1 each)
        if captions:
            print(f"\n📝 Processing {len(captions)} Captions")
            print("-" * 30)
            for i, caption in enumerate(captions):
                print(f"  Caption {i+1}: {len(caption)} chars")
            
            caption_embeddings = self.embed_texts(
                captions,
                output_dim=output_dim
            )
            caption_vectors = caption_embeddings[0]  # Get the first (and only) batch
            all_vectors.extend(caption_vectors)
            weights.extend([1.0] * len(caption_vectors))
            print(f"✅ Generated {len(caption_vectors)} caption embeddings")
            print(f"  Vector shape: {caption_vectors[0].shape}")
        else:
            print("⚠️  No captions to process")
        
        # Bio embedding (weight: 3)
        if bio:
            print("\n👤 Processing Bio")
            print("-" * 30)
            print(f"Bio length: {len(bio)} chars")
            bio_embeddings = self.embed_texts(
                [bio],
                output_dim=output_dim
            )
            bio_embedding = bio_embeddings[0][0]  # Get first (and only) embedding
            all_vectors.append(bio_embedding)
            weights.append(3.0)
            print(f"✅ Bio embedding generated: shape {bio_embedding.shape}")
        else:
            print("⚠️  No bio to process")
        
        # Combine all vectors with weights
        print("\n🔄 Combining Embeddings")
        print("-" * 30)
        print(f"Total vectors: {len(all_vectors)}")
        print(f"Weights: {weights}")
        
        # Normalize weights
        weights = np.array(weights) / sum(weights)
        
        # Compute weighted average
        combined_embedding = np.average(all_vectors, axis=0, weights=weights)
        
        # Normalize the combined embedding
        combined_embedding = combined_embedding / np.linalg.norm(combined_embedding)
        
        print(f"✅ Combined embedding shape: {combined_embedding.shape}")
        print("\n✨ Embedding Generation Complete")
            
        return {'combined': combined_embedding}

    def process_batch_profiles(
        self,
        profiles: List[Dict],
        output_dim: int = 128
    ) -> List[Dict]:
        """
        Generate embeddings for a batch of profiles.
        
        Args:
            profiles: List of profile dictionaries containing images and texts
            output_dim: Output embedding dimension
            
        Returns:
            List of dictionaries containing embeddings for each profile
        """
        results = []
        
        for profile in tqdm(profiles, desc="Processing profiles"):
            try:
                embeddings = self.process_profile(
                    profile_pic=profile.get('profile_pic'),
                    post_images=profile.get('post_images', []),
                    captions=profile.get('captions', []),
                    bio=profile.get('bio'),
                    output_dim=output_dim
                )
                
                results.append({
                    'profile_id': profile.get('id'),
                    'embeddings': embeddings
                })
                
            except Exception as e:
                print(f"Error processing profile {profile.get('id')}: {str(e)}")
                continue
                
        return results

    @staticmethod
    def combine_vectors(
        vectors: List[np.ndarray],
        weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        Utility method to combine vectors with optional weights.
        Can be used later to experiment with different combination strategies.
        
        Args:
            vectors: List of vectors to combine
            weights: Optional weights for each vector
            
        Returns:
            Combined vector
        """
        if not vectors:
            raise ValueError("No vectors provided for combination")
            
        if weights is None:
            weights = [1.0] * len(vectors)
            
        if len(weights) != len(vectors):
            raise ValueError("Number of weights must match number of vectors")
            
        # Normalize weights
        weights = np.array(weights) / sum(weights)
        
        # Weighted sum
        combined = sum(w * v for w, v in zip(weights, vectors))
        
        # L2 normalize
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined /= norm
            
        return combined