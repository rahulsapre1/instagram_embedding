"""
Script to inspect the payload data stored with vectors in Qdrant.
"""
import os
from qdrant_client import QdrantClient
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def inspect_payload():
    """Inspect payload data stored with vectors."""
    console = Console()
    
    # Initialize Qdrant client
    client = QdrantClient(
        url=os.getenv("QDRANT_HOST", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    
    # Get collection info
    console.print("\n[bold]Collection Info:[/bold]")
    collection_info = client.get_collection("instagram_profiles")
    console.print(collection_info)
    
    # Get a few sample points with different scroll parameters
    console.print("\n[bold]Sample Profiles (First 3):[/bold]")
    results = client.scroll(
        collection_name="instagram_profiles",
        limit=3,
        with_payload=True,
        with_vectors=False
    )[0]
    
    # Try another scroll with offset
    console.print("\n[bold]Sample Profiles (Next 3):[/bold]")
    more_results = client.scroll(
        collection_name="instagram_profiles",
        limit=3,
        offset=3,
        with_payload=True,
        with_vectors=False
    )[0]
    
    results.extend(more_results)
    
    # Create table
    table = Table(title="Sample Profile Payloads")
    table.add_column("Username", style="cyan")
    table.add_column("Full Name", style="green")
    table.add_column("Account Type", style="yellow")
    table.add_column("Follower Count", style="blue")
    table.add_column("Follower Category", style="magenta")
    
    # Display payload fields for results
    for result in results:
        payload = result.payload
        table.add_row(
            payload.get("username", "N/A"),
            payload.get("full_name", "N/A"),
            payload.get("account_type", "N/A"),
            str(payload.get("follower_count", "N/A")),
            payload.get("follower_category", "N/A")
        )
        
    console.print(table)
    
    # Print raw payload for debugging
    console.print("\n[bold]Raw payload examples:[/bold]")
    for i, result in enumerate(results, 1):
        console.print(f"\nProfile {i}:")
        console.print(result.payload)

if __name__ == "__main__":
    inspect_payload()