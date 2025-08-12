"""
Demo script for the interactive search interface.
This shows how the interface works without requiring actual API keys.
"""
import os
import sys
import json
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interactive_search import SearchContext, InteractiveSearchSession

class MockGeminiInterface:
    """Mock Gemini interface for demonstration purposes."""
    
    def __init__(self):
        self.context = SearchContext()
        
        # Pre-defined responses for demo
        self.demo_responses = {
            "Find food bloggers in Sydney": {
                "action": "search",
                "query": "food bloggers in Sydney",
                "filters": {},
                "explanation": "I'll search for food bloggers in Sydney. Let me execute that search for you.",
                "suggestions": ["Refine your search", "Add filters", "Ask for help"]
            },
            "Only show me ones with over 10K followers": {
                "action": "refine",
                "query": "food bloggers in Sydney",
                "filters": {"min_followers": 10000},
                "explanation": "I'll refine your search to show only food bloggers in Sydney with over 10K followers.",
                "suggestions": ["Add more filters", "Change follower range", "Search for different content"]
            },
            "Only human accounts": {
                "action": "refine",
                "query": "food bloggers in Sydney",
                "filters": {"min_followers": 10000, "account_type": "human"},
                "explanation": "I'll refine to show only human food bloggers in Sydney with over 10K followers.",
                "suggestions": ["Show results", "Add location filters", "Search for different content"]
            },
            "Show me brand accounts in Melbourne": {
                "action": "search",
                "query": "brand accounts in Melbourne",
                "filters": {"account_type": "brand"},
                "explanation": "I'll search for brand accounts in Melbourne.",
                "suggestions": ["Add follower filters", "Refine location", "Search for different content"]
            },
            "Only ones with over 100K followers": {
                "action": "refine",
                "query": "brand accounts in Melbourne",
                "filters": {"account_type": "brand", "min_followers": 100000},
                "explanation": "I'll refine to show only brand accounts in Melbourne with over 100K followers.",
                "suggestions": ["Show results", "Add more filters", "Search for different content"]
            }
        }
    
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and return mock response."""
        # Add to conversation history
        self.context.add_conversation("user", user_input)
        
        # Find matching demo response
        for key, response in self.demo_responses.items():
            if key.lower() in user_input.lower():
                # Add assistant response to history
                self.context.add_conversation("assistant", response["explanation"])
                return response
        
        # Default response for unrecognized input
        default_response = {
            "action": "search",
            "query": user_input,
            "filters": {},
            "explanation": f"I'll search for: {user_input}",
            "suggestions": ["Refine your search", "Add filters", "Ask for help"]
        }
        
        self.context.add_conversation("assistant", default_response["explanation"])
        return default_response
    
    def execute_search(self, query: str, filters: Dict[str, Any]) -> str:
        """Mock search execution."""
        filter_str = ", ".join([f"{k}: {v}" for k, v in filters.items()]) if filters else "None"
        
        mock_results = f"""
🔍 Mock Search Results for: {query}
📊 Filters: {filter_str}

┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ Rank ┃ Username               ┃ Full Name               ┃ Followers ┃ Category ┃ Type    ┃ Score ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ 1    │ sydney_foodie          │ Sydney Food Adventures  │ 45,200    │ Micro    │ human   │ 0.892 │
│ 2    │ melbourne_eats         │ Melbourne Food Guide    │ 38,700    │ Micro    │ human   │ 0.845 │
│ 3    │ aussie_kitchen         │ Australian Kitchen      │ 67,300    │ Micro    │ human   │ 0.823 │
│ 4    │ foodie_down_under      │ Foodie Down Under      │ 89,100    │ Micro    │ human   │ 0.798 │
│ 5    │ sydney_bites           │ Sydney Bites            │ 23,400    │ Nano     │ human   │ 0.776 │
└──────┴────────────────────────┴─────────────────────────┴───────────┴──────────┴─────────┴───────┘

Note: These are mock results for demonstration purposes.
        """
        
        return mock_results
    
    def update_context(self, action: str, query: str, filters: Dict[str, Any]):
        """Update search context."""
        if action == "search":
            self.context.base_query = query
            self.context.update_filters(filters)
        elif action == "refine":
            self.context.update_filters(filters)
    
    def get_context_summary(self) -> str:
        """Get context summary."""
        return self.context.get_filter_summary()

class DemoInteractiveSearchSession:
    """Demo version of the interactive search session."""
    
    def __init__(self):
        """Initialize the demo session."""
        self.interface = MockGeminiInterface()
        print("✅ Demo Interactive Search Interface initialized!")
    
    async def run(self):
        """Run the demo session."""
        print("\n🤖 Welcome to the Demo Interactive Instagram Profile Search!")
        print("=" * 70)
        print("This is a demonstration of how the interactive search interface works.")
        print("I'll show you how to build search queries through conversation.")
        print("\n💡 Try these example queries:")
        print("  • 'Find food bloggers in Sydney'")
        print("  • 'Only show me ones with over 10K followers'")
        print("  • 'Only human accounts'")
        print("  • 'Show me brand accounts in Melbourne'")
        print("  • 'Only ones with over 100K followers'")
        print("\nType 'help' for assistance, 'context' to see current search state, or 'quit' to exit.")
        print("=" * 70)
        
        while True:
            try:
                # Get user input
                try:
                    user_input = input("\n🔍 You: ").strip()
                except EOFError:
                    print("\n\n👋 End of input reached. Goodbye!")
                    break
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thanks for trying the demo! Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if user_input.lower() == 'context':
                    self._show_context()
                    continue
                
                if not user_input:
                    continue
                
                # Process user input
                print("\n🤔 Processing your request...")
                response = await self.interface.process_user_input(user_input)
                
                # Display response
                self._display_response(response)
                
                # Execute search if requested
                if response["action"] in ["search", "refine"]:
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
                print("\n\n👋 Demo interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again or type 'help' for assistance.")
                break
    
    def _display_response(self, response: Dict[str, Any]):
        """Display the response."""
        print(f"\n🤖 Assistant: {response['explanation']}")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
📚 HELP - Demo Interactive Instagram Profile Search

🔍 SEARCHING:
• Just describe what you're looking for in natural language
• I'll build the search query and apply appropriate filters
• Examples: "Find food bloggers in Sydney", "Show me brand accounts with over 100K followers"

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

💡 DEMO FEATURES:
• This is a demonstration with mock responses
• Real implementation uses Google Gemini 2.5
• Mock results show the expected output format
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
    session = DemoInteractiveSearchSession()
    await session.run()

if __name__ == "__main__":
    asyncio.run(main()) 