# Hybrid Image + Text Search Feature

## Overview

The Hybrid Search feature combines image and text embeddings to find Instagram profiles that match both visual and textual criteria. This feature uses Google Gemini AI to intelligently assign weights between image and text search based on query intent.

## Features

- **🖼️ Image Processing**: Download and process images from URLs
- **🧠 Intelligent Weighting**: AI-powered weight assignment (0.0 to 1.0 in 0.1 increments)
- **🔍 Combined Search**: Single hybrid vector combining image and text embeddings
- **📱 CLI Integration**: Seamlessly integrated into the interactive search interface
- **🔄 Error Handling**: Robust error handling for invalid URLs and processing failures

## Usage

### Interactive Search Interface

Use the `IMAGE:` keyword followed by a URL and query:

```
🔍 You: IMAGE: https://example.com/image.jpg find similar profiles
```

**Format**: `IMAGE: <URL> <query>`

**Examples**:
- `IMAGE: https://example.com/photo.jpg find similar profiles`
- `IMAGE: https://example.com/image.png search for travel accounts`
- `IMAGE: https://example.com/photo.jpg profiles with similar style`

### Weight Assignment

The system automatically assigns weights based on query intent:

- **High Image Weight (0.7-1.0)**: "similar", "matching", "style", "look", "appearance", "like this"
- **Medium Image Weight (0.4-0.6)**: "with similar", "style and", "appearance of"
- **Low Image Weight (0.0-0.3)**: "profiles", "accounts", "people", "search for", "find"

**Examples**:
- "find similar profiles" → Image: 0.8, Text: 0.2
- "search for travel accounts" → Image: 0.2, Text: 0.8
- "profiles with similar style" → Image: 0.6, Text: 0.4

## Architecture

### Core Components

1. **`HybridSearchEngine`** (`query_embedding/hybrid_search.py`)
   - Main orchestrator for hybrid search
   - Combines image and text embeddings with weights
   - Interfaces with Qdrant for vector search

2. **`WeightAnalyzer`** (`query_embedding/weight_analyzer.py`)
   - Uses Google Gemini to analyze query intent
   - Assigns weights based on natural language understanding
   - Includes fallback logic for API failures

3. **`ImageProcessor`** (`query_embedding/image_processor.py`)
   - Downloads images from URLs
   - Generates embeddings using existing Instagram image processing
   - Validates image URLs and handles errors

### Data Flow

```
User Input: IMAGE: <URL> <query>
    ↓
1. Parse URL and query
    ↓
2. Validate image URL
    ↓
3. Analyze query intent → Get weights
    ↓
4. Download and process image → Generate embedding
    ↓
5. Generate text embedding
    ↓
6. Create hybrid vector (weighted combination)
    ↓
7. Search Qdrant database
    ↓
8. Format and return results
```

## Error Handling

### URL Validation
- Checks if URL is accessible (HTTP 200)
- Validates content type is image
- Provides clear error messages for invalid URLs

### Processing Failures
- Graceful fallback for image download failures
- Weight analyzer fallback to keyword-based assignment
- Comprehensive error logging and user feedback

### Common Issues
- **Invalid URL**: "Error: Invalid or inaccessible image URL"
- **Processing Error**: "Error: Failed to process image from URL"
- **API Failure**: Falls back to keyword-based weight assignment

## Testing

### Basic Test
```bash
python scripts/demo/test_basic_hybrid.py
```

### Full Demo
```bash
python scripts/demo/hybrid_search_demo.py
```

### Interactive Testing
```bash
python interactive_search.py
# Then use: IMAGE: <URL> <query>
```

## Demo URL

The system includes a test image for demonstration:
```
https://seniorsinmelbourne.com.au/wp-content/uploads/2024/03/City_Circle_Tram_Melbourne-25.jpg
```

This Melbourne tram image can be used to test the hybrid search functionality.

## Dependencies

### Required
- `google-generativeai` - For Gemini AI integration
- `Pillow` - For image processing
- `requests` - For HTTP requests
- `aiohttp` - For async HTTP requests (optional, falls back to requests)

### Environment Variables
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Required for weight analysis
- `GEMINI_MODEL` - Optional, defaults to "gemini-2.5-flash"

## Output Format

Results maintain the same format as regular text search:

```
🔍 HYBRID SEARCH RESULTS
============================================================
Image URL: https://example.com/image.jpg
Text Query: find similar profiles
Weights: Image=0.8, Text=0.2
============================================================

Username             Full Name                Followers    Category   Account Type  Score   
---------------------------------------------------------------------------------------
user1               John Doe                 15,000       Micro      Human        0.892
user2               Jane Smith               25,000       Micro      Human        0.845
user3               Travel Blog              45,000       Macro      Brand        0.823

Found 3 results
```

## Limitations

- **Image Size**: No size limits, but very large images may take longer to process
- **URL Accessibility**: Images must be publicly accessible via HTTP/HTTPS
- **API Dependencies**: Requires Google Gemini API key for optimal weight assignment
- **Processing Time**: Image download and embedding generation adds latency

## Future Enhancements

- **Batch Processing**: Support for multiple images
- **Image Caching**: Cache processed images to avoid re-downloading
- **Advanced Weighting**: More sophisticated weight assignment algorithms
- **Image Preprocessing**: Automatic image optimization and enhancement
- **Multi-modal Search**: Support for video and other media types

## Troubleshooting

### Common Issues

1. **"Hybrid search components not available"**
   - Check that all required modules are installed
   - Verify import paths are correct

2. **"Invalid or inaccessible image URL"**
   - Ensure URL is publicly accessible
   - Check if URL returns an actual image file
   - Verify URL format is correct

3. **"Failed to process image"**
   - Check image format compatibility
   - Ensure sufficient memory for image processing
   - Verify image is not corrupted

4. **"Weight analyzer failed"**
   - Check GEMINI_API_KEY environment variable
   - Verify internet connectivity
   - Check Gemini API quota and limits

### Debug Mode

Enable detailed logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## Support

For issues or questions about the hybrid search feature:
1. Check the error messages for specific guidance
2. Run the basic test script to verify setup
3. Review the demo script for usage examples
4. Check environment variables and API keys 