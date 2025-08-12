# Instagram Profile Embedding Pipeline

A robust pipeline for generating and storing vector embeddings of Instagram profiles using CLIP model and Qdrant vector database. The system processes profile pictures, post images, captions, and bios to create comprehensive profile embeddings that can be used for semantic search.

## Features

- Multi-modal embedding generation using Jina CLIP model
- Efficient batch processing of profiles
- Automatic image downloading and caching
- Vector storage and search using Qdrant
- Profile data fetching from Supabase
- Weighted combination of different profile components
- Progress tracking and detailed logging
- Skip-existing functionality for incremental updates

## Architecture

The pipeline consists of several components:

1. **Supabase Integration** (`supabase_utils.py`)
   - Fetches profile data in batches
   - Extracts posts, captions, and bio information
   - Handles pagination and error recovery

2. **Image Processing** (`image_utils.py`)
   - Downloads profile pictures and post images
   - Implements caching to avoid redundant downloads
   - Handles various image formats and errors

3. **Embedding Generation** (`embedder.py`)
   - Uses Jina CLIP model for both image and text embedding
   - Processes images and text in efficient batches
   - Combines multiple embeddings with weighted averaging
   - Reduces embedding dimension while preserving information

4. **Vector Storage** (`qdrant_utils.py`)
   - Manages Qdrant collection creation and updates
   - Stores profile embeddings with metadata
   - Handles vector similarity search
   - Implements existence checking for incremental updates

5. **Main Pipeline** (`main.py`)
   - Orchestrates the entire embedding process
   - Implements batch processing and error handling
   - Provides progress tracking and logging
   - Supports single-profile testing

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_service_role_key

   # Qdrant Configuration
   QDRANT_HOST=http://localhost:6333
   QDRANT_API_KEY=  # Leave empty for local development
   VECTOR_DIM=128

   # Processing Configuration
   BATCH_SIZE=32

   # Model Configuration
   MODEL_NAME="jinaai/jina-clip-v2"

   # Embedding Weights
   PROFILE_PIC_WEIGHT=2
   POST_IMAGE_WEIGHT=1
   CAPTION_WEIGHT=1
   BIO_WEIGHT=3

   # Logging Configuration
   LOG_LEVEL=INFO
   ```

4. Start Qdrant:
   ```bash
   docker-compose up -d
   ```

## Usage

### Running the Full Pipeline

Process all profiles from Supabase:
```bash
python -m instagram_embedding.main
```

### Testing Single Profile

Test the pipeline with a specific profile:
```python
from instagram_embedding.main import InstagramEmbeddingPipeline
import asyncio

async def test():
    pipeline = InstagramEmbeddingPipeline()
    await pipeline.test_single_profile(profile_id=12345)

asyncio.run(test())
```

### Batch Processing

The pipeline processes profiles in batches (default 32) to optimize performance. You can modify the batch size in `.env` or when running the pipeline:

```python
await pipeline.run_pipeline(batch_size=64)
```

### Skip Existing Profiles

The pipeline can skip profiles that are already in Qdrant:

```python
await pipeline.run_pipeline(skip_existing=True)
```

## Vector Embedding Details

The pipeline generates embeddings as follows:

1. **Profile Picture**: Weight = 2.0
   - Single image embedding

2. **Post Images**: Weight = 1.0
   - Multiple image embeddings averaged

3. **Captions**: Weight = 1.0
   - Text embeddings from post captions

4. **Bio**: Weight = 3.0
   - Text embedding from profile bio

These components are combined using weighted averaging to create a single 128-dimensional vector per profile.

## Performance Considerations

- Uses batched processing to optimize memory usage
- Implements image caching to avoid redundant downloads
- Supports asynchronous operations for better throughput
- Reduces CLIP's 1024D output to 128D for efficient storage
- Handles rate limiting and network errors gracefully

## Error Handling

The pipeline includes comprehensive error handling:
- Network connectivity issues
- Invalid or missing images
- Database connection problems
- Rate limiting
- Memory constraints

Errors are logged and the pipeline attempts to continue processing remaining profiles.

## Monitoring Progress

The pipeline provides detailed progress information:
- Overall progress bar
- Per-batch success/skip counts
- Detailed logging of each step
- Error reporting and statistics

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.