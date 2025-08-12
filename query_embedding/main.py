"""
CLI tool for searching Instagram profiles using natural language queries.
"""
import sys
import argparse
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .embedder import QueryEmbedder
from .qdrant_utils import QdrantSearcher
from .follower_utils import FollowerCountConverter

console = Console()

def format_results(profiles: List[Dict[str, Any]]) -> None:
    """Format and display search results using rich tables."""
    if not profiles:
        console.print(Panel("No matching profiles found", style="yellow"))
        return

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Username", style="cyan")
    table.add_column("Full Name", style="green")
    table.add_column("Followers", style="yellow")
    table.add_column("Category", style="blue")
    table.add_column("Type", style="red")
    table.add_column("Score", justify="right")

    # Add rows
    for i, profile in enumerate(profiles, 1):
        payload = profile.payload
        table.add_row(
            str(i),
            payload.get("username", "N/A"),
            payload.get("full_name", "N/A"),
            f"{payload.get('follower_count', 0):,}",
            payload.get("influencer_type", "N/A").capitalize(),
            payload.get("account_type", "N/A"),
            f"{profile.score:.3f}"
        )

    console.print(table)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Search Instagram profiles using natural language.")
    parser.add_argument("query", help="Natural language query")
    
    # Follower count filters
    follower_group = parser.add_mutually_exclusive_group()
    follower_group.add_argument(
        "--follower-category",
        choices=["nano", "micro", "macro", "mega"],
        help="Filter by follower category (nano: 1K-10K, micro: 10K-100K, macro: 100K-1M, mega: 1M+)"
    )
    follower_group.add_argument(
        "--min-followers",
        type=int,
        help="Minimum follower count"
    )
    follower_group.add_argument(
        "--max-followers",
        type=int,
        help="Maximum follower count"
    )
    
    # Account type filter
    parser.add_argument(
        "--account-type",
        choices=["human", "brand"],
        help="Filter by account type"
    )
    
    # Search parameters
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results to return"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score threshold"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Initialize searcher
    searcher = QdrantSearcher(top_k=args.limit, score_threshold=args.threshold)
    
    # Build filters
    filters = {}
    
    # Handle follower count filters
    if args.follower_category:
        # Category ranges
        ranges = {
            "nano": (1_000, 10_000),
            "micro": (10_000, 100_000),
            "macro": (100_000, 1_000_000),
            "mega": (1_000_000, None)
        }
        min_followers, max_followers = ranges[args.follower_category]
        filters["follower_count"] = (min_followers, max_followers)
    elif args.min_followers is not None:
        filters["follower_count"] = (args.min_followers, None)
    elif args.max_followers is not None:
        filters["follower_count"] = (0, args.max_followers)
    
    # Handle account type filter
    if args.account_type:
        filters["account_type"] = args.account_type
    
    try:
        # Perform search
        results = searcher.search(args.query, filters=filters)
        format_results(results)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()