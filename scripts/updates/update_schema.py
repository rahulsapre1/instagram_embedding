"""
Script to update Qdrant collection schema.
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType, Distance, VectorParams
from rich.console import Console
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_schema():
    """Update Qdrant collection schema to include new fields."""
    console = Console()
    
    # Initialize client
    client = QdrantClient(
        url=os.getenv("QDRANT_HOST", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    
    # Get current schema
    console.print("\n[bold]Current Schema:[/bold]")
    collection_info = client.get_collection("instagram_profiles")
    console.print(collection_info.payload_schema)
    
    # Define fields to index
    fields = [
        # Existing fields are already indexed
        
        # New fields
        ("follower_count", PayloadSchemaType.INTEGER),
        ("follower_category", PayloadSchemaType.KEYWORD),
        ("account_type", PayloadSchemaType.KEYWORD),
        ("full_name", PayloadSchemaType.KEYWORD),
        ("is_private", PayloadSchemaType.KEYWORD)
    ]
    
    # Create indexes for each field
    console.print("\n[bold]Creating indexes...[/bold]")
    for field_name, field_type in fields:
        try:
            console.print(f"Creating index for {field_name}...")
            client.create_payload_index(
                collection_name="instagram_profiles",
                field_name=field_name,
                field_type=field_type
            )
        except Exception as e:
            console.print(f"[red]Error creating index for {field_name}: {str(e)}[/red]")
    
    # Verify update
    console.print("\n[bold]Updated Schema:[/bold]")
    updated_info = client.get_collection("instagram_profiles")
    console.print(updated_info.payload_schema)
    
    console.print("\n[bold green]Schema update complete![/bold green]")

if __name__ == "__main__":
    update_schema()