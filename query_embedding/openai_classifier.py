"""
OpenAI-based Instagram profile classifier.
"""
import os
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OpenAIClassifier:
    def __init__(self, model: str = "gpt-5-mini"):  # Keeping the model as requested
        """Initialize the OpenAI classifier."""
        self.model = model
        self.system_prompt = """You are an expert at classifying Instagram profiles into three categories:
1. Human: Personal accounts of real individuals
2. Brand: Business accounts, organizations, or commercial entities
3. Unknown: When there's not enough information or mixed signals

Key indicators for each category:

HUMAN INDICATORS:
- Personal name in username/full name
- First-person narrative in bio
- Personal life content and stories
- Individual achievements and experiences
- Personal pronouns (I, my, me)
- Life updates and personal journey sharing

BRAND INDICATORS:
- Business name or terms in username/full name
- Business hours
- Company/organization descriptions
- Multiple team members mentioned
- Professional services or products
- Marketing language
- Business contact information
- Professional titles

MIXED/UNKNOWN INDICATORS:
- Minimal or ambiguous profile information
- Equal mix of personal/business indicators
- Unclear whether personal brand or business
- Generic content without clear ownership

Analyze all available information and provide a classification with your reasoning.
If confidence is less than 70%, classify as "unknown".
Output format: {"classification": "human|brand|unknown", "confidence": 0-100, "reasoning": "brief explanation"}
"""

    def classify_profile(self, profile_data: Dict) -> Dict:
        """
        Classify a profile using OpenAI's model.
        
        Args:
            profile_data: Dictionary containing profile information
                Required keys: username, full_name
                Optional keys: bio, follower_count, influencer_type, 
                             profile_pic_url, is_private, recent_posts
                
        Returns:
            Dictionary with classification results
        """
        # Construct the profile description
        profile_desc = []
        
        # Basic info
        profile_desc.append(f"Username: @{profile_data.get('username', 'N/A')}")
        profile_desc.append(f"Full Name: {profile_data.get('full_name', 'N/A')}")
        
        # Bio and metrics
        if profile_data.get('bio'):
            profile_desc.append(f"Bio: {profile_data['bio']}")
        if profile_data.get('follower_count'):
            profile_desc.append(f"Followers: {profile_data['follower_count']}")
        if profile_data.get('influencer_type'):
            profile_desc.append(f"Influencer Type: {profile_data['influencer_type']}")
            
        # Privacy status
        is_private = profile_data.get('is_private', 'N/A')
        profile_desc.append(f"Private Account: {is_private}")
        
        # Recent posts if available
        if profile_data.get('recent_posts'):
            posts = profile_data['recent_posts']
            profile_desc.append("\nRecent Posts:")
            for post in posts[:3]:  # Only include last 3 posts
                profile_desc.append(f"- {post}")
                
        # Join all information
        profile_text = "\n".join(profile_desc)
        
        # Construct the user message
        user_message = f"""Please classify this Instagram profile:

{profile_text}

Provide your classification as human, brand, or unknown based on the available information.
If your confidence is less than 70%, classify as unknown."""

        try:
            # Make API call to OpenAI using the new client
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract the classification result
            result = response.choices[0].message.content
            
            # Parse the JSON-like response
            import json
            try:
                parsed = json.loads(result)
                # If confidence is less than 70%, force unknown classification
                if parsed['confidence'] < 70:
                    parsed['classification'] = 'unknown'
                return {
                    'classification': parsed['classification'],
                    'confidence': parsed['confidence'],
                    'reasoning': parsed['reasoning']
                }
            except json.JSONDecodeError:
                # Fallback parsing if response isn't proper JSON
                if 'human' in result.lower():
                    classification = 'human'
                elif 'brand' in result.lower():
                    classification = 'brand'
                else:
                    classification = 'unknown'
                    
                return {
                    'classification': classification,
                    'confidence': 50,  # Default confidence when parsing fails
                    'reasoning': result
                }
                
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return {
                'classification': 'unknown',
                'confidence': 0,
                'reasoning': f"Error: {str(e)}"
            }

    def batch_classify(self, profiles: list[Dict], batch_size: int = 10) -> list[Dict]:
        """
        Classify multiple profiles in batches.
        
        Args:
            profiles: List of profile dictionaries
            batch_size: Number of profiles to process in each batch
            
        Returns:
            List of classification results
        """
        results = []
        for i in range(0, len(profiles), batch_size):
            batch = profiles[i:i + batch_size]
            batch_results = []
            for profile in batch:
                result = self.classify_profile(profile)
                batch_results.append({
                    'username': profile['username'],
                    'classification': result['classification'],
                    'confidence': result['confidence'],
                    'reasoning': result['reasoning']
                })
            results.extend(batch_results)
            
            # Progress update
            processed = min(i + batch_size, len(profiles))
            print(f"Processed {processed}/{len(profiles)} profiles")
            
        return results