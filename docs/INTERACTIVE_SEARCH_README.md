# Interactive Instagram Profile Search

A memory-aware, conversational interface for searching Instagram profiles using Google Gemini 2.5.

## 🚀 Features

- **Conversational Search**: Build search queries through natural language conversation
- **Memory-Aware**: Remembers context and previous search criteria across the session
- **Incremental Refinement**: Add filters and modify searches through conversation
- **Smart Suggestions**: AI-powered recommendations for next steps
- **Session History**: Track conversation and search context throughout the session

## 🛠️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

**Required:**
- `GOOGLE_API_KEY`: Your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

**Optional:**
- `SUPABASE_URL` & `SUPABASE_KEY`: For additional profile data
- `QDRANT_HOST` & `QDRANT_PORT`: For vector database connection

### 3. Get Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Add it to your `.env` file

## 🎯 Usage

### Start Interactive Search
```bash
python interactive_search.py
```

### Example Conversation Flow

```
🔍 You: I'm looking for food bloggers in Sydney
🤖 Assistant: I'll search for food bloggers in Sydney. Let me execute that search for you.

🔍 Executing search: food bloggers in Sydney
📊 Filters: {}

📋 Search Results:
[Search results displayed here]

💡 Suggestions:
  • Refine your search
  • Add filters
  • Ask for help

🔍 You: Only show me ones with over 10K followers
🤖 Assistant: I'll refine your search to show only food bloggers in Sydney with over 10K followers.

🔍 Executing search: food bloggers in Sydney
📊 Filters: {'min_followers': 10000}

📋 Search Results:
[Filtered results displayed here]
```

### Available Commands

- **`help`** - Show help information
- **`context`** - Display current search context and conversation history
- **`quit`/`exit`/`bye`** - Exit the program

## 🔧 How It Works

### 1. **Conversation Processing**
- User input is processed by Google Gemini 2.5
- The AI understands natural language and converts it to search parameters
- Context is maintained across the conversation

### 2. **Search Building**
- Queries are built incrementally based on user conversation
- Filters are applied automatically based on user intent
- The system remembers previous search criteria

### 3. **CLI Integration**
- Final search commands are kept short and focused
- Uses the existing `query_embedding.main` module
- Maintains compatibility with existing search functionality

### 4. **Context Management**
- **Search Context**: Current query and active filters
- **Conversation History**: Recent conversation turns
- **Session State**: Persistent across the entire session

## 🎨 Search Filters

The interface supports all existing CLI filters:

- **Follower Categories**: `nano` (1K-10K), `micro` (10K-100K), `macro` (100K-1M), `mega` (1M+)
- **Account Types**: `human`, `brand`
- **Follower Ranges**: `min_followers`, `max_followers`
- **Results Control**: `limit`, `threshold`

## 💡 Best Practices

### For Users
- **Be Specific**: "Find food bloggers in Sydney" vs "Find bloggers"
- **Build Incrementally**: Start broad, then add filters
- **Use Natural Language**: "Only show me ones with over 10K followers"
- **Check Context**: Use `context` command to see current state

### For Developers
- **Extend Filters**: Add new filter types in the `SearchContext` class
- **Modify Prompts**: Adjust the system prompt in `GeminiSearchInterface`
- **Add Actions**: Implement new action types beyond search/refine

## 🔍 Example Use Cases

### Marketing Campaigns
```
🔍 You: I need influencers for a Sydney food festival
🤖 Assistant: I'll search for food influencers in Sydney for your festival campaign.

🔍 You: Only human accounts with 10K-100K followers
🤖 Assistant: I'll refine to show only human food influencers in Sydney with 10K-100K followers.
```

### Brand Research
```
🔍 You: Show me brand accounts in Melbourne
🤖 Assistant: I'll search for brand accounts in Melbourne.

🔍 You: Only ones with over 100K followers
🤖 Assistant: I'll refine to show only brand accounts in Melbourne with over 100K followers.
```

### Content Creator Discovery
```
🔍 You: Find travel vloggers in Australia
🤖 Assistant: I'll search for travel vloggers in Australia.

🔍 You: Only nano and micro influencers
🤖 Assistant: I'll refine to show only nano and micro travel vloggers in Australia.
```

## 🚨 Troubleshooting

### Common Issues

1. **"GOOGLE_API_KEY environment variable is required"**
   - Check your `.env` file has the correct API key
   - Ensure the file is in the project root directory

2. **"Failed to initialize Gemini interface"**
   - Verify your API key is valid
   - Check internet connection
   - Ensure you have the latest `google-generativeai` package

3. **Search results not showing**
   - Check if Qdrant is running
   - Verify your database has profiles
   - Check the search query format

### Debug Commands
- Use `context` to see current search state
- Check conversation history for errors
- Verify filters are being applied correctly

## 🔮 Future Enhancements

- **Multi-modal Search**: Support for image-based queries
- **Advanced Filtering**: Date ranges, engagement metrics
- **Export Results**: Save search results to files
- **Batch Operations**: Process multiple searches
- **Integration**: Connect with other social media platforms

## 📚 Technical Details

### Architecture
- **Frontend**: Interactive CLI interface
- **AI Layer**: Google Gemini 2.5 for natural language processing
- **Search Engine**: Existing CLI program integration
- **Data Layer**: Qdrant vector database + Supabase

### Key Classes
- `SearchContext`: Manages search state and history
- `GeminiSearchInterface`: Handles AI interactions and search execution
- `InteractiveSearchSession`: Manages the user session

### Data Flow
1. User input → Gemini processing → Structured response
2. Response parsing → Search execution → Results display
3. Context update → Conversation history → Next iteration

## 🤝 Contributing

To extend the interactive search:

1. **Add New Filters**: Modify `SearchContext.get_filter_summary()`
2. **Extend Actions**: Add new action types in the system prompt
3. **Improve Parsing**: Enhance `_parse_gemini_response()` method
4. **Add Commands**: Implement new commands in `InteractiveSearchSession`

## 📄 License

This project is part of the Instagram Profile Search system. See the main README for license information. 