"""
Tests for follower count conversion utilities.
"""
import unittest
from query_embedding.follower_utils import FollowerCountConverter

class TestFollowerCountConverter(unittest.TestCase):
    def setUp(self):
        self.converter = FollowerCountConverter()
        
    def test_parse_follower_count(self):
        """Test follower count text parsing."""
        test_cases = [
            # Basic numbers
            ("1000", 1000),
            ("1234", 1234),
            
            # K format
            ("1K", 1000),
            ("1.5K", 1500),
            ("10K", 10000),
            ("19.3K", 19300),
            
            # M format
            ("1M", 1000000),
            ("1.5M", 1500000),
            ("34.2M", 34200000),
            
            # B format
            ("1B", 1000000000),
            ("1.5B", 1500000000),
            
            # With 'followers' text
            ("1K followers", 1000),
            ("19.3K followers", 19300),
            ("34.2M followers", 34200000),
            
            # With plus sign
            ("1K+ followers", 1000),
            ("19.3K+", 19300),
            ("34.2M+ followers", 34200000),
            
            # Case insensitive
            ("1k", 1000),
            ("19.3k followers", 19300),
            ("34.2m+ followers", 34200000),
            
            # Invalid formats
            ("", None),
            ("invalid", None),
            ("K followers", None),
            ("1.5.K", None)
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = self.converter.parse_follower_count(text)
                self.assertEqual(result, expected)
                
    def test_get_follower_category(self):
        """Test follower count categorization."""
        test_cases = [
            (500, "none"),      # Less than 1K
            (1000, "nano"),     # 1K
            (5000, "nano"),     # Middle of nano
            (9999, "nano"),     # Upper nano
            (10000, "micro"),   # Lower micro
            (50000, "micro"),   # Middle of micro
            (99999, "micro"),   # Upper micro
            (100000, "macro"),  # Lower macro
            (500000, "macro"),  # Middle of macro
            (999999, "macro"),  # Upper macro
            (1000000, "mega"),  # Lower mega
            (5000000, "mega"),  # Middle of mega
            (1000000000, "mega") # Billion followers
        ]
        
        for count, expected in test_cases:
            with self.subTest(count=count):
                result = self.converter.get_follower_category(count)
                self.assertEqual(result, expected)
                
    def test_get_category_range(self):
        """Test category range lookup."""
        test_cases = [
            ("nano", (1000, 10000)),
            ("micro", (10000, 100000)),
            ("macro", (100000, 1000000)),
            ("mega", (1000000, float('inf'))),
            ("invalid", (0, 0))
        ]
        
        for category, expected in test_cases:
            with self.subTest(category=category):
                result = self.converter.get_category_range(category)
                self.assertEqual(result, expected)
                
if __name__ == '__main__':
    unittest.main()