"""
CLI tool for searching Instagram profiles using natural language queries.
"""
import sys
import argparse
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from query_embedding.embedder import QueryEmbedder
from query_embedding.qdrant_utils import QdrantSearcher

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
    table.add_column("Private", width=8)
    table.add_column("Score", justify="right")

    # Add rows
    for i, profile in enumerate(profiles, 1):
        table.add_row(
            str(i),
            profile["username"],
            profile["full_name"] or "N/A",
            "🔒" if profile["is_private"] else "🔓",
            f"{profile['similarity_score']}%"
        )

    # Display table
    console.print("\n[bold]Top Matching Profiles:[/bold]\n")
    console.print(table)

    # Display detailed information for top 3 matches
    console.print("\n[bold]Top 3 Profiles Details:[/bold]\n")
    for i, profile in enumerate(profiles[:3], 1):
        text = Text()
        text.append(f"\n[{i}] ", style="dim")
        text.append(profile["username"], style="cyan bold")
        text.append(f" ({profile['similarity_score']}% match)\n", style="yellow")
        text.append("└─ Full Name: ", style="dim")
        text.append(f"{profile['full_name'] or 'N/A'}\n", style="green")
        text.append("└─ Profile URL: ", style="dim")
        text.append(f"https://instagram.com/{profile['username']}\n", style="blue underline")
        text.append("└─ Private Account: ", style="dim")
        text.append(f"{'Yes' if profile['is_private'] else 'No'}\n", style="red" if profile["is_private"] else "green")
        console.print(text)

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Search Instagram profiles using natural language queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m query_embedding.main "food bloggers in melbourne"
  python -m query_embedding.main "photographers who post about nature"
  python -m query_embedding.main "fitness influencers who share workout tips"
        """
    )
    parser.add_argument(
        "query",
        help="Natural language query to search for similar profiles"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results to return (default: 20)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score (0-1) for matches (default: 0.0)"
    )
    args = parser.parse_args()

    try:
        # Initialize components
        console.print("[bold]Initializing search components...[/bold]")
        embedder = QueryEmbedder()
        searcher = QdrantSearcher(top_k=args.limit, score_threshold=args.threshold)

        # Generate query embedding
        console.print(f"\n[bold]Processing query:[/bold] {args.query}")
        query_vector = embedder.embed_query(args.query)

        # Search for similar profiles
        console.print("\n[bold]Searching for matching profiles...[/bold]")
        results = searcher.search_profiles(query_vector)

        # Display results
        format_results(results)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()