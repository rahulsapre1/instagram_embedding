"""
Utilities for handling Instagram follower counts.
"""
import re
from typing import Optional, Tuple

class FollowerCountConverter:
    # Multipliers for different units
    MULTIPLIERS = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000
    }
    
    @staticmethod
    def parse_follower_count(text: str) -> Optional[int]:
        """
        Convert follower count text (e.g. '19.3K followers', '34.2M+ followers') to numeric value.
        
        Args:
            text: Follower count text (e.g. '19.3K followers', '34.2M+ followers')
            
        Returns:
            Numeric follower count or None if parsing fails
        """
        if not text:
            return None
            
        # Clean and normalize text
        text = text.upper().strip()
        text = text.replace('FOLLOWERS', '').replace('+', '').strip()
        
        try:
            # Extract number and unit
            match = re.match(r'^(\d+\.?\d*)([KMB])?$', text)
            if not match:
                # Try parsing as plain number
                return int(float(text))
                
            number, unit = match.groups()
            number = float(number)
            
            # Apply multiplier if unit exists
            if unit:
                number *= FollowerCountConverter.MULTIPLIERS[unit]
                
            return int(number)
            
        except (ValueError, AttributeError):
            return None
            
    @staticmethod
    def get_follower_category(count: int) -> str:
        """
        Get follower count category (nano, micro, macro, mega).
        
        Args:
            count: Numeric follower count
            
        Returns:
            Category string ('nano', 'micro', 'macro', 'mega')
        """
        if count < 1_000:
            return 'none'  # Less than 1K followers
        elif count < 10_000:
            return 'nano'  # 1K-10K followers
        elif count < 100_000:
            return 'micro'  # 10K-100K followers
        elif count < 1_000_000:
            return 'macro'  # 100K-1M followers
        else:
            return 'mega'  # 1M+ followers
            
    @staticmethod
    def get_category_range(category: str) -> Tuple[int, int]:
        """
        Get follower count range for a category.
        
        Args:
            category: Category string ('nano', 'micro', 'macro', 'mega')
            
        Returns:
            Tuple of (min_followers, max_followers)
        """
        ranges = {
            'nano': (1_000, 10_000),
            'micro': (10_000, 100_000),
            'macro': (100_000, 1_000_000),
            'mega': (1_000_000, float('inf'))
        }
        return ranges.get(category.lower(), (0, 0))