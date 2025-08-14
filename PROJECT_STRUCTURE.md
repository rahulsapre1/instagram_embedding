# Instagram Embedding Project Structure

## Overview
This project provides an Instagram profile embedding and search system with an interactive AI-powered interface.

## Directory Structure

```
instagram_embedding/
├── 📁 instagram_embedding/          # Core embedding system
│   ├── embedder.py                  # Profile embedding logic
│   ├── image_utils.py               # Image processing utilities
│   ├── main.py                      # Main embedding application
│   ├── qdrant_utils.py              # Vector database operations
│   ├── supabase_utils.py            # Database utilities
│   └── tests/                       # Core system tests
├── 📁 query_embedding/              # Search and classification system
│   ├── account_classifier.py        # Account type classification
│   ├── batch_classify.py            # Batch classification
│   ├── embedder.py                  # Query embedding
│   ├── follower_utils.py            # Follower count utilities
│   ├── get_profile.py               # Individual profile retrieval
│   ├── main.py                      # CLI search interface
│   ├── openai_classifier.py         # OpenAI-based classification
│   ├── qdrant_utils.py              # Search utilities
│   ├── reclassify.py                # Profile reclassification
│   ├── supabase_utils.py            # Database access
│   └── tests/                       # Search system tests
├── 📁 scripts/                      # Utility and maintenance scripts
│   ├── 📁 debug/                    # Debugging and investigation scripts
│   │   ├── check_*.py               # Various check scripts
│   │   ├── analyze_*.py             # Data analysis scripts
│   │   ├── debug_*.py               # Debugging utilities
│   │   ├── find_*.py                # Search and discovery scripts
│   │   └── show_*.py                # Display scripts
│   ├── 📁 updates/                  # Data update and maintenance scripts
│   │   ├── update_*.py              # Various update scripts
│   │   ├── classify_*.py            # Classification scripts
│   │   ├── remove_*.py              # Data cleanup scripts
│   │   └── print_*.py               # Data output scripts
│   ├── 📁 tests/                    # Testing and validation scripts
│   │   └── test_*.py                # Various test scripts
│   ├── 📁 demo/                     # Demonstration scripts
│   │   └── demo_*.py                # Demo and example scripts
│   └── README.md                    # Scripts directory documentation
├── 📁 data/                         # Data files and logs
│   ├── 📁 temp/                     # Temporary and working files
│   │   ├── classification_progress.txt
│   │   ├── progress.txt
│   │   ├── user_ids.txt
│   │   └── TODO.txt
│   ├── 📁 logs/                     # Log files (ready for future use)
│   └── README.md                    # Data directory documentation
├── 📁 docs/                         # Documentation and templates
│   ├── .env.template                # Environment variables template
│   ├── INTERACTIVE_SEARCH_README.md # Interactive search guide
│   └── README.md                    # Documentation directory guide
├── 📁 venv/                         # Virtual environment (can be recreated)
├── 📁 .venv/                        # Alternative virtual environment
├── interactive_search.py             # Main interactive search interface
├── requirements.txt                  # Python dependencies
├── .env                             # Environment configuration
├── .env.example                     # Environment variables example
├── docker-compose.yml               # Container configuration
├── .gitignore                       # Git ignore rules
├── README.md                        # Main project documentation
└── PROJECT_STRUCTURE.md             # This file
```

## Core Components

### 1. **Instagram Embedding System** (`instagram_embedding/`)
- **Purpose**: Core system for creating and storing profile embeddings
- **Key Files**: `embedder.py`, `qdrant_utils.py`, `main.py`
- **Functionality**: Profile processing, embedding generation, vector storage

### 2. **Query Embedding System** (`query_embedding/`)
- **Purpose**: Search, classification, and profile management
- **Key Files**: `main.py`, `account_classifier.py`, `batch_classify.py`
- **Functionality**: Vector search, profile classification, data retrieval

### 3. **Interactive Search Interface** (`interactive_search.py`)
- **Purpose**: AI-powered conversational search interface
- **Technology**: Google Gemini 2.5
- **Functionality**: Natural language queries, context awareness, search building

## Scripts Organization

### **Debug Scripts** (`scripts/debug/`)
- One-time debugging and investigation tools
- Data analysis and system understanding scripts
- **Note**: Not part of core functionality, kept for reference

### **Update Scripts** (`scripts/updates/`)
- Data maintenance and modification tools
- One-time data update operations
- **Note**: Not part of core functionality, kept for reference

### **Test Scripts** (`scripts/tests/`)
- Testing and validation utilities
- **Note**: Not part of core functionality, kept for reference

### **Demo Scripts** (`scripts/demo/`)
- Demonstration and example tools
- **Note**: Not part of core functionality, kept for reference

## Data Organization

### **Temporary Files** (`data/temp/`)
- Progress tracking files
- Development notes
- **Note**: Can be safely deleted, will be regenerated as needed

### **Log Files** (`data/logs/`)
- System operation logs
- **Note**: Currently empty, ready for future use

## Configuration Files

- **`.env`**: Active environment configuration (contains sensitive data)
- **`.env.example`**: Template for environment setup
- **`requirements.txt`**: Python package dependencies
- **`docker-compose.yml`**: Container orchestration

## Usage

1. **Core System**: Use `instagram_embedding/` for profile embedding
2. **Search System**: Use `query_embedding/` for profile search and classification
3. **Interactive Interface**: Use `interactive_search.py` for conversational search
4. **Maintenance**: Use scripts in `scripts/` directory for specific tasks
5. **Configuration**: Copy `.env.example` to `.env` and fill in your values

## Notes

- **Scripts**: Most scripts in `scripts/` are one-time use tools, not part of core functionality
- **Temporary Files**: Files in `data/temp/` can be safely deleted
- **Virtual Environments**: `venv/` and `.venv/` can be recreated using `requirements.txt`
- **Core Functionality**: The main application consists of the three core directories and `interactive_search.py` 