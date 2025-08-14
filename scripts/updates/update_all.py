"""
Script to update all profile data with follower counts and account types.
"""
import os
from typing import List, Dict, Any
from tqdm import tqdm
from qdrant_client import QdrantClient
from rich.console import Console
from rich.table import Table

from query_embedding.supabase_utils import SupabaseClient
from query_embedding.account_classifier import AccountTypeClassifier
from query_embedding.follower_utils import FollowerCountConverter

def update_all(batch_size: int = 100):
    """Update all profile data in batches."""
    console = Console()
    
    # Initialize clients
    console.print("[bold]Initializing clients...[/bold]")
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_HOST", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30.0
    )
    supabase = SupabaseClient()
    classifier = AccountTypeClassifier()
    
    # Get total count
    collection_info = qdrant.get_collection("instagram_profiles")
    total_points = collection_info.points_count
    console.print(f"\n[bold]Total profiles to update: {total_points}[/bold]")
    
    # Process in batches
    offset = None
    processed = 0
    
    with tqdm(total=total_points, desc="Processing profiles") as pbar:
        while processed < total_points:
            # Get batch of profiles
            profiles = qdrant.scroll(
                collection_name="instagram_profiles",
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )[0]
            
            if not profiles:
                break
                
            # Extract usernames and embeddings
            usernames = [p.payload["username"] for p in profiles]
            embeddings = {p.payload["username"]: p.vector for p in profiles}
            
            # Fetch follower counts
            profile_data = supabase.fetch_profile_data(usernames)
            
            # Classify account types
            account_types = classifier.classify_accounts(embeddings)
            
            # Update records
            for profile in profiles:
                username = profile.payload["username"]
                
                # Get follower data
                follower_data = profile_data.get(username, {})
                follower_count = follower_data.get("follower_count")
                follower_category = follower_data.get("follower_category")
                
                # Get account type
                account_type = account_types.get(username)
                
                # Update payload
                new_payload = {
                    **profile.payload,
                    "follower_count": follower_count,
                    "follower_category": follower_category,
                    "account_type": account_type
                }
                
                # Update record
                try:
                    qdrant.set_payload(
                        collection_name="instagram_profiles",
                        payload=new_payload,
                        points=[profile.id]
                    )
                except Exception as e:
                    console.print(f"[red]Error updating profile {username}: {str(e)}[/red]")
                    continue
            
            # Update progress
            processed += len(profiles)
            pbar.update(len(profiles))
            
            # Get offset for next batch
            offset = profiles[-1].id
            
            # Show sample of updated data every 1000 profiles
            if processed % 1000 == 0:
                console.print(f"\n[bold]Sample of updated profiles (at {processed:,}):[/bold]")
                table = Table(show_header=True)
                table.add_column("Username")
                table.add_column("Follower Count")
                table.add_column("Category")
                table.add_column("Account Type")
                
                for profile in profiles[:5]:  # Show first 5 from batch
                    table.add_row(
                        profile.payload["username"],
                        str(profile.payload.get("follower_count", "N/A")),
                        profile.payload.get("follower_category", "N/A"),
                        profile.payload.get("account_type", "N/A")
                    )
                console.print(table)
    
    console.print("\n[bold green]Update completed![/bold green]")

if __name__ == "__main__":
    update_all()