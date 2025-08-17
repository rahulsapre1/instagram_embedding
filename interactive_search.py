"""
Interactive memory-aware search interface using Google Gemini 2.5.
This interface sits between the user and the existing CLI program,
allowing incremental query building through conversation.
"""
import os
import sys
import json
import asyncio
import subprocess
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Import hybrid search components
try:
    from query_embedding.hybrid_search import HybridSearchEngine
except ImportError:
    HybridSearchEngine = None

# Load environment variables
load_dotenv()

@dataclass
class SearchContext:
    """Maintains search context and history."""
    base_query: str = ""
    filters: Dict[str, Any] = None
    conversation_history: List[Dict[str, str]] = None
    last_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.conversation_history is None:
            self.conversation_history = []
    
    def add_conversation(self, role: str, content: str):
        """Add a conversation turn to history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_filters(self, new_filters: Dict[str, Any]):
        """Update search filters."""
        self.filters.update(new_filters)
    
    def get_filter_summary(self) -> str:
        """Get a human-readable summary of current filters."""
        if not self.filters:
            return "No filters applied"
        
        summaries = []
        if "follower_category" in self.filters:
            summaries.append(f"Follower category: {self.filters['follower_category']}")
        if "account_type" in self.filters:
            summaries.append(f"Account type: {self.filters['account_type']}")
        if "min_followers" in self.filters:
            summaries.append(f"Min followers: {self.filters['min_followers']:,}")
        if "max_followers" in self.filters:
            summaries.append(f"Max followers: {self.filters['max_followers']:,}")
        
        return ", ".join(summaries)

class GeminiSearchInterface:
    """Interactive search interface using Google Gemini 2.5."""
    
    def __init__(self):
        """Initialize the Gemini interface."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        # Initialize Gemini model
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.model = genai.GenerativeModel(model_name)
        
        # Search context
        self.context = SearchContext()
        
        # System prompt for Gemini
        self.system_prompt = """You are an intelligent search assistant for an Instagram profile database. Your role is to help users build search queries incrementally through conversation.

AVAILABLE SEARCH FILTERS:
- follower_category: nano (1K-10K), micro (10K-100K), macro (100K-1M), mega (1M+)
- account_type: human, brand
- min_followers: minimum follower count
- max_followers: maximum follower count
- limit: maximum results (default: 20)
- threshold: minimum similarity score (default: 0.0)

SEARCH BEHAVIOR:
- Build queries incrementally based on user conversation
- Remember context and previous search criteria
- Suggest refinements based on user needs
- Keep final CLI commands short and focused
- Use natural language to understand user intent

RESPONSE FORMAT:
Always respond with a JSON object containing:
{
    "action": "search" | "refine" | "clarify" | "help",
    "query": "the search query to execute",
    "filters": {filter object},
    "explanation": "explanation of what you're doing",
    "suggestions": ["suggestions for next steps"]
}

Keep responses conversational but focused on building effective search queries."""

    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and return search action."""
        # Add user input to conversation history
        self.context.add_conversation("user", user_input)
        
        # Build conversation context for Gemini
        conversation_context = self._build_conversation_context()
        
        try:
            # Generate response using Gemini
            response = await self._generate_gemini_response(conversation_context)
            
            # Parse Gemini response
            parsed_response = self._parse_gemini_response(response)
            
            # Add assistant response to conversation history
            self.context.add_conversation("assistant", response)
            
            return parsed_response
            
        except Exception as e:
            return {
                "action": "error",
                "query": "",
                "filters": {},
                "explanation": f"Error processing input: {str(e)}",
                "suggestions": ["Try rephrasing your request", "Check your internet connection"]
            }
    
    def _build_conversation_context(self) -> str:
        """Build conversation context for Gemini."""
        context_parts = [self.system_prompt]
        
        # Add current search context
        if self.context.base_query:
            context_parts.append(f"\nCURRENT SEARCH: {self.context.base_query}")
        
        if self.context.filters:
            context_parts.append(f"CURRENT FILTERS: {self.context.get_filter_summary()}")
        
        # Add recent conversation history (last 5 turns)
        recent_history = self.context.conversation_history[-10:]
        if recent_history:
            context_parts.append("\nRECENT CONVERSATION:")
            for turn in recent_history:
                role = "User" if turn["role"] == "user" else "Assistant"
                context_parts.append(f"{role}: {turn['content']}")
        
        return "\n".join(context_parts)
    
    async def _generate_gemini_response(self, context: str) -> str:
        """Generate response using Gemini."""
        prompt = f"{context}\n\nUser: {self.context.conversation_history[-1]['content']}\n\nAssistant:"
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def _parse_gemini_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response to extract structured data."""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["action", "query", "filters", "explanation", "suggestions"]
                if all(field in parsed for field in required_fields):
                    return parsed
            
            # Fallback parsing
            return {
                "action": "search",
                "query": response.strip(),
                "filters": {},
                "explanation": "Parsed response as search query",
                "suggestions": ["Refine your search", "Add filters", "Ask for help"]
            }
            
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as search query
            return {
                "action": "search",
                "query": response.strip(),
                "filters": {},
                "explanation": "Treated response as search query",
                "suggestions": ["Refine your search", "Add filters", "Ask for help"]
            }
    
    def execute_search(self, query: str, filters: Dict[str, Any]) -> str:
        """Execute the search using the existing CLI program."""
        try:
            # Build CLI command - use sys.executable to get the current Python interpreter
            python_cmd = sys.executable
            cmd_parts = [python_cmd, "-m", "query_embedding.main", query]
            
            # Add filters
            if filters.get("follower_category"):
                cmd_parts.extend(["--follower-category", filters["follower_category"]])
            if filters.get("account_type"):
                cmd_parts.extend(["--account-type", filters["account_type"]])
            if filters.get("min_followers"):
                cmd_parts.extend(["--min-followers", str(filters["min_followers"])])
            if filters.get("max_followers"):
                cmd_parts.extend(["--max-followers", str(filters["max_followers"])])
            if filters.get("limit"):
                cmd_parts.extend(["--limit", str(filters["limit"])])
            if filters.get("threshold"):
                cmd_parts.extend(["--threshold", str(filters["threshold"])])
            
            # Execute command
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error executing search: {result.stderr}"
                
        except Exception as e:
            return f"Error executing search: {str(e)}"
    
    async def execute_hybrid_search(self, image_url: str, text_query: str, filters: Dict[str, Any]) -> str:
        """Execute hybrid image + text search."""
        if HybridSearchEngine is None:
            return "Error: Hybrid search components not available. Please install required dependencies."
        
        try:
            # Initialize hybrid search engine
            hybrid_engine = HybridSearchEngine()
            
            # Validate image URL first
            is_valid = await hybrid_engine.validate_image_url(image_url)
            if not is_valid:
                return f"Error: Invalid or inaccessible image URL: {image_url}\nPlease provide a valid image URL and try again."
            
            # Perform hybrid search
            results, weights = await hybrid_engine.search(image_url, text_query)
            
            # Format results in the same style as CLI output
            formatted_results = self._format_hybrid_results(results, weights, image_url, text_query)
            
            return formatted_results
            
        except Exception as e:
            return f"Error executing hybrid search: {str(e)}"
    
    def _format_hybrid_results(self, results: List, weights: Dict[str, float], 
                              image_url: str, text_query: str) -> str:
        """Format hybrid search results to match CLI output style."""
        output = []
        output.append("🔍 HYBRID SEARCH RESULTS")
        output.append("=" * 60)
        output.append(f"Image URL: {image_url}")
        output.append(f"Text Query: {text_query}")
        output.append(f"Weights: Image={weights['image_weight']:.1f}, Text={weights['text_weight']:.1f}")
        output.append("=" * 60)
        output.append("")
        
        if not results:
            output.append("No results found.")
            return "\n".join(output)
        
        # Header
        output.append(f"{'Username':<20} {'Full Name':<25} {'Followers':<12} {'Category':<10} {'Account Type':<12} {'Score':<8}")
        output.append("-" * 90)
        
        # Results
        for i, result in enumerate(results[:20], 1):  # Limit to 20 results
            payload = result.payload
            output.append(
                f"{payload.get('username', 'N/A'):<20} "
                f"{payload.get('full_name', 'N/A'):<25} "
                f"{payload.get('follower_count', 0):<12,} "
                f"{payload.get('influencer_type', 'N/A').capitalize():<10} "
                f"{payload.get('account_type', 'N/A'):<12} "
                f"{result.score:<8.3f}"
            )
        
        output.append("")
        output.append(f"Found {len(results)} results")
        return "\n".join(output)
    
    def update_context(self, action: str, query: str, filters: Dict[str, Any]):
        """Update search context based on action."""
        if action == "search":
            self.context.base_query = query
            self.context.update_filters(filters)
        elif action == "refine":
            self.context.update_filters(filters)
    
    def get_context_summary(self) -> str:
        """Get a summary of current search context."""
        summary = []
        
        if self.context.base_query:
            summary.append(f"Current search: {self.context.base_query}")
        
        if self.context.filters:
            summary.append(f"Active filters: {self.context.get_filter_summary()}")
        
        if self.context.conversation_history:
            summary.append(f"Conversation turns: {len(self.context.conversation_history)}")
        
        return " | ".join(summary) if summary else "No active search context"

class InteractiveSearchSession:
    """Manages an interactive search session."""
    
    def __init__(self):
        """Initialize the search session."""
        try:
            self.interface = GeminiSearchInterface()
            print("✅ Gemini Search Interface initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini interface: {e}")
            sys.exit(1)
    
    async def run(self):
        """Run the interactive search session."""
        print("\n🤖 Welcome to the Interactive Instagram Profile Search!")
        print("=" * 60)
        print("I can help you search for Instagram profiles through conversation.")
        print("Just tell me what you're looking for, and I'll build the search for you.")
        print("\nType 'help' for assistance, 'context' to see current search state, or 'quit' to exit.")
        print("=" * 60)
        
        while True:
            try:
                # Get user input
                try:
                    user_input = input("\n🔍 You: ").strip()
                except EOFError:
                    print("\n\n👋 End of input reached. Goodbye!")
                    break
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thanks for using the Interactive Search! Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if user_input.lower() == 'context':
                    self._show_context()
                    continue
                
                if not user_input:
                    continue
                
                # Check for IMAGE: keyword for hybrid search
                if user_input.upper().startswith("IMAGE:"):
                    await self._handle_hybrid_search(user_input)
                    continue
                
                # Process user input
                print("\n🤔 Processing your request...")
                response = await self.interface.process_user_input(user_input)
                
                # Display response
                self._display_response(response)
                
                # Execute search if requested
                if response["action"] == "search":
                    print(f"\n🔍 Executing search: {response['query']}")
                    if response['filters']:
                        print(f"📊 Filters: {response['filters']}")
                    
                    search_results = self.interface.execute_search(
                        response["query"], 
                        response["filters"]
                    )
                    
                    print("\n📋 Search Results:")
                    print("-" * 40)
                    print(search_results)
                    
                    # Update context
                    self.interface.update_context(
                        response["action"],
                        response["query"],
                        response["filters"]
                    )
                
                # Show suggestions
                if response.get("suggestions"):
                    print(f"\n💡 Suggestions:")
                    for suggestion in response["suggestions"]:
                        print(f"  • {suggestion}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                break
    
    def _display_response(self, response: Dict[str, Any]):
        """Display the Gemini response."""
        print(f"\n🤖 Assistant: {response['explanation']}")
    
    async def _handle_hybrid_search(self, user_input: str):
        """Handle hybrid image + text search requests."""
        try:
            # Parse IMAGE: URL query format
            # Format: IMAGE: https://example.com/image.jpg find similar profiles
            match = re.match(r'IMAGE:\s*(https?://[^\s]+)\s*(.*)', user_input, re.IGNORECASE)
            
            if not match:
                print("\n❌ Invalid IMAGE: format. Use: IMAGE: <URL> <query>")
                print("Example: IMAGE: https://example.com/image.jpg find similar profiles")
                return
            
            image_url = match.group(1).strip()
            text_query = match.group(2).strip()
            
            if not text_query:
                print("\n❌ Please provide a text query along with the image URL.")
                print("Example: IMAGE: City Circle Tram Melbourne find similar profiles")
                return
            
            print(f"\n🖼️  Processing hybrid search...")
            print(f"Image URL: {image_url}")
            print(f"Text Query: {text_query}")
            print("\n🤖 Analyzing query intent and generating weights...")
            
            # Execute hybrid search
            search_results = await self.interface.execute_hybrid_search(
                image_url, text_query, {}
            )
            
            print("\n📋 Hybrid Search Results:")
            print("-" * 40)
            print(search_results)
            
            # Add to conversation history
            self.interface.context.add_conversation("user", f"IMAGE: {image_url} {text_query}")
            self.interface.context.add_conversation("assistant", f"Executed hybrid search with image and text query")
            
        except Exception as e:
            print(f"\n❌ Error in hybrid search: {str(e)}")
            print("Please check your image URL and try again.")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
📚 HELP - Interactive Instagram Profile Search

🔍 SEARCHING:
• Just describe what you're looking for in natural language
• I'll build the search query and apply appropriate filters
• Examples: "Find food bloggers in Sydney", "Show me brand accounts with over 100K followers"

🖼️  HYBRID IMAGE + TEXT SEARCH:
• Use IMAGE: keyword followed by URL and query
• Format: IMAGE: <URL> <query>
• Examples: 
  - IMAGE: https://example.com/image.jpg find similar profiles
  - IMAGE: https://example.com/photo.png search for travel accounts
• I'll automatically analyze query intent and assign weights
• Supports pure text (0.0), pure image (1.0), and mixed weights

🎯 FILTERS:
• Follower categories: nano (1K-10K), micro (10K-100K), macro (100K-1M), mega (1M+)
• Account types: human, brand
• Follower ranges: specify min/max follower counts
• Results: limit number of results and set similarity threshold

💬 CONVERSATION:
• Build searches incrementally through conversation
• I remember context and previous search criteria
• Ask me to refine or modify your search
• Use "context" to see current search state

📝 COMMANDS:
• help - Show this help message
• context - Show current search context
• quit/exit/bye - Exit the program
        """
        print(help_text)
    
    def _show_context(self):
        """Show current search context."""
        context_summary = self.interface.get_context_summary()
        print(f"\n📊 Current Search Context:")
        print("-" * 40)
        print(context_summary)
        
        if self.interface.context.conversation_history:
            print(f"\n💬 Recent Conversation:")
            recent = self.interface.context.conversation_history[-5:]
            for turn in recent:
                role = "You" if turn["role"] == "user" else "Assistant"
                print(f"  {role}: {turn['content'][:100]}{'...' if len(turn['content']) > 100 else ''}")

async def main():
    """Main entry point."""
    session = InteractiveSearchSession()
    await session.run()

if __name__ == "__main__":
    asyncio.run(main()) 