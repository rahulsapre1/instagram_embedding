Instagram Profile Embedder + Qdrant Vector Search

This project creates a single semantic vector for each Instagram profile using:

Profile picture
Bio
12 post images
12 post captions
It uses jina-clip-v2 to embed both images and text, combines them with weighted averaging, and stores the vectors and metadata in Qdrant Cloud for similarity search.

Project Structure:

instagram_embedding/
├── main.py               # Main entry point for embedding + uploading
├── embedder.py           # Handles downloading and embedding
├── qdrant_utils.py       # Sets up Qdrant collection and handles vector storage
├── image_utils.py        # (Optional) Extra image handling functions
├── data/                 # (Optional) Local image cache
├── requirements.txt      # All dependencies
└── README.txt            # This file
Features:

Download and process remote images and text
Uses jina-clip-v2 for multi-modal embeddings
Weighted averaging of profile + post content
Store in Qdrant Cloud (free tier)
Query similar Instagram profiles
Requirements:

Python 3.10 (tested with Apple M1)
No CUDA required (runs on CPU)
Qdrant Cloud (free tier works)
Installation:

Clone the repo:
git clone https://github.com/yourusername/instagram-embedder.git
cd instagram-embedder
Create and activate a virtual environment:
brew install pyenv
pyenv install 3.10.13
pyenv virtualenv 3.10.13 insta-embed-env
pyenv activate insta-embed-env
Install dependencies:
pip install -r requirements.txt
Set up Qdrant Cloud:
Create a Qdrant Cloud account: https://cloud.qdrant.io
Create a cluster and copy:
Cluster URL
API Key
Set environment variables (or edit qdrant_utils.py):
export QDRANT_API_KEY=your-api-key
export QDRANT_HOST=https://your-cluster.cloud.qdrant.io
How It Works:

The embedding process includes:

Profile picture → image embedding
Bio → text embedding
12 post images → image embeddings
12 post captions → text embeddings
Each component has a default weight:

bio: 2
profile_pic: 2
caption: 1
post_image: 1
All vectors are averaged using these weights to form a single 512-dimensional vector per profile.