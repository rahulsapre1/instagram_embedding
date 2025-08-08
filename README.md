# Instagram Profile Classifier

A hybrid classification system that uses CLIP embeddings and Gemini 2.5 Flash-Lite to classify Instagram profiles as either human accounts or brand accounts.

## Features

- **Hybrid Classification**: Combines two powerful approaches:
  - CLIP embeddings for visual and textual understanding
  - Gemini 2.5 Flash-Lite for natural language analysis
- **Profile Analysis**: Analyzes multiple aspects of Instagram profiles:
  - Profile pictures and post images
  - Bio text and captions
  - Account metrics (followers, etc.)
- **Vector Database**: Uses Qdrant for efficient storage and retrieval of profile embeddings
- **Rate Limiting**: Built-in rate limiting for Gemini API (10 RPM, 250000 TPM, 1000 RPD)
- **Batch Processing**: Support for processing multiple profiles in batches
- **Progress Tracking**: Saves progress and provides detailed statistics

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd instagram_embedding
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Qdrant Configuration
QDRANT_API_KEY=your_qdrant_key
QDRANT_HOST=http://localhost:6333
VECTOR_DIM=128

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp
```

## Usage

### Single Profile Lookup
To look up information about a specific profile:

```bash
python -m query_embedding.get_profile
```

### Batch Classification
To run classification on multiple profiles:

```bash
python -m query_embedding.batch_classify
```

### Test Classification
To test the hybrid classifier on a sample of profiles:

```bash
python -m query_embedding.test_hybrid_classifier
```

## Architecture

### Components

1. **Account Classifier** (`account_classifier.py`):
   - Implements hybrid classification using CLIP and Gemini
   - Handles rate limiting and error recovery

2. **Embedder** (`embedder.py`):
   - Generates CLIP embeddings for text and images
   - Handles dimension reduction and normalization

3. **Qdrant Utils** (`qdrant_utils.py`):
   - Manages vector database operations
   - Handles search and filtering

4. **Supabase Utils** (`supabase_utils.py`):
   - Fetches profile data from Supabase
   - Handles data transformation

### Classification Process

1. **Data Collection**:
   - Fetch profile data from Supabase
   - Extract text content (bio, captions)
   - Download profile images

2. **Feature Extraction**:
   - Generate CLIP embeddings for text and images
   - Combine embeddings with appropriate weights

3. **Classification**:
   - Run CLIP-based classification
   - Run Gemini-based classification
   - Compare results and determine final classification

4. **Storage**:
   - Store embeddings and classification results in Qdrant
   - Update profile metadata

## Rate Limits

- **Gemini API**:
  - 10 requests per minute
  - 250,000 tokens per minute
  - 1,000 requests per day

## Error Handling

- Automatic retry on API failures
- Progress saving on interruption
- Batch failure recovery
- Rate limit management

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

[Your License Here]