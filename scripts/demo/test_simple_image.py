"""
Simple test script for image download functionality
Uses a reliable public image URL for testing
"""

import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from query_embedding.image_processor import ImageProcessor


async def test_image_download():
    """Test image download with a reliable public image"""
    print("🖼️  Testing Image Download")
    print("=" * 50)
    
    # Use a reliable public image URL
    test_urls = [
        "https://httpbin.org/image/jpeg",  # Simple test image
        "https://picsum.photos/512/512",   # Random placeholder image
        "https://via.placeholder.com/512x512/FF0000/FFFFFF?text=Test"  # Placeholder
    ]
    
    processor = ImageProcessor()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: {url}")
        print("-" * 40)
        
        try:
            # Validate URL
            is_valid = await processor.validate_image_url(url)
            print(f"URL validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
            if is_valid:
                # Download and process image
                embedding = await processor.get_embedding_from_url(url)
                if embedding:
                    print(f"✅ Successfully generated embedding: {len(embedding)} dimensions")
                    print(f"First 5 values: {embedding[:5]}")
                else:
                    print("❌ Failed to generate embedding")
            else:
                print("❌ Cannot proceed with invalid URL")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()


async def main():
    """Main test function"""
    print("Welcome to the Simple Image Download Test!")
    print("This test uses reliable public image URLs.")
    print()
    
    await test_image_download()
    
    print("=" * 50)
    print("🎉 Test completed!")
    print("\nIf all tests passed, you can now test with your own image URLs.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}") 