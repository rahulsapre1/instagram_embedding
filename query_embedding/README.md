# Query Embedding Tool

A command-line tool for searching Instagram profiles using natural language queries. This tool converts your natural language query into a vector embedding using the same model used to embed Instagram profiles, then finds the most similar profiles using vector similarity search.

## Installation

1. Make sure you have Python 3.8+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure you have a `.env` file with the following variables:
   ```
   QDRANT_HOST=http://localhost:6333
   QDRANT_API_KEY=  # Leave empty for local development
   MODEL_NAME="jinaai/jina-clip-v2"
   LOG_LEVEL=INFO
   ```

## Usage

```bash
# Basic usage
python -m query_embedding.main "your natural language query here"

# Example queries
python -m query_embedding.main "food bloggers in melbourne"
python -m query_embedding.main "photographers who post about nature"
python -m query_embedding.main "fitness influencers who share workout tips"

# Limit number of results
python -m query_embedding.main "travel bloggers" --limit 10

# Set minimum similarity threshold (0-1)
python -m query_embedding.main "tech reviewers" --threshold 0.5
```

## Output Format

The tool displays results in two formats:

1. A summary table showing:
   - Rank
   - Username
   - Full Name
   - Private Account Status
   - Similarity Score

2. Detailed information for the top 3 matches, including:
   - Username
   - Full Name
   - Profile URL
   - Private Account Status
   - Similarity Score

## Dependencies

- transformers
- torch
- numpy
- qdrant-client
- python-dotenv
- rich (for formatted output)

## Notes

- The tool uses the Jina CLIP model for generating embeddings
- Searches are performed against the "instagram_profiles" collection in Qdrant
- Results are ranked by cosine similarity
- The tool returns up to 20 results by default
- Similarity scores are displayed as percentages