"""
Script to classify Instagram profiles using OpenAI and store results in Supabase.
"""
import os
from typing import Dict, List
from dotenv import load_dotenv
from instagram_embedding.supabase_utils import SupabaseClient
from query_embedding.openai_classifier import OpenAIClassifier
from tqdm import tqdm

def fetch_profiles_batch(supabase: SupabaseClient, start: int = 0, batch_size: int = 10) -> List[Dict]:
    """Fetch a batch of profiles from Supabase."""
    try:
        # Fetch profiles that don't have account_type set yet or have empty account_type
        result = supabase.client.table('ig_profile_merged_v0_1') \
            .select('*') \
            .or_('account_type.is.null,account_type.eq.') \
            .range(start, start + batch_size - 1) \
            .execute()
        
        # Filter out profiles that already have human/brand classification
        filtered_data = [
            profile for profile in (result.data or [])
            if not profile.get('account_type') or profile['account_type'] not in ['human', 'brand']
        ]
        
        return filtered_data
    except Exception as e:
        print(f"Error fetching profiles: {str(e)}")
        return []

def prepare_profile_for_classification(profile: Dict) -> Dict:
    """Prepare profile data for classification."""
    # Get captions (filter out None values)
    captions = []
    for i in range(12):  # We have caption_0 through caption_11
        caption = profile.get(f'caption_{i}')
        if caption:
            captions.append(caption)
    
    return {
        'username': str(profile.get('user_id')),  # Use user_id as username since we don't have username
        'user_id': profile.get('user_id'),
        'full_name': profile.get('full_name'),
        'bio': profile.get('bio'),
        'recent_posts': captions[:11] if captions else [],  # Only use first 3 captions for classification
        'is_private': False  # We don't have this information in the table
    }

def store_profile_classification(supabase: SupabaseClient, user_id: int, classification: Dict) -> bool:
    """Store profile classification in Supabase."""
    if not user_id:
        return False
        
    try:
        # Update only the account_type field
        data = {'account_type': classification.get('classification', 'unknown')}
        result = supabase.client.table('ig_profile_merged_v0_1') \
            .update(data) \
            .eq('user_id', user_id) \
            .execute()
        return True if result.data else False
    except Exception as e:
        print(f"Error storing classification for user {user_id}: {str(e)}")
        return False

def get_total_unclassified_count(supabase: SupabaseClient) -> int:
    """Get total count of unclassified profiles."""
    try:
        result = supabase.client.table('ig_profile_merged_v0_1') \
            .select('*', count='exact') \
            .is_('account_type', 'null') \
            .execute()
        return result.count if result.count is not None else 0
    except Exception as e:
        print(f"Error getting total count: {str(e)}")
        return 0

def main(batch_size: int = 10, start_from: int = 0, max_retries: int = 3):
    """Main function to process profiles."""
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    supabase = SupabaseClient()
    classifier = OpenAIClassifier()
    
    # Get total count of unclassified profiles
    total_points = get_total_unclassified_count(supabase)
    if total_points == 0:
        print("No unclassified profiles found")
        return
        
    print(f"\n🔍 Processing {total_points} unclassified profiles in batches of {batch_size}")
    print(f"Starting from offset: {start_from}")
    
    # Process in batches
    processed = 0
    failed = 0
    retry_count = 0
    
    with tqdm(total=total_points, desc="Classifying profiles", initial=start_from) as pbar:
        current_start = start_from
        while current_start < total_points:
            try:
                # Fetch batch
                profiles = fetch_profiles_batch(supabase, current_start, batch_size)
                if not profiles:
                    if retry_count < max_retries:
                        print(f"\nNo profiles found, retrying... (attempt {retry_count + 1}/{max_retries})")
                        retry_count += 1
                        continue
                    else:
                        print("\nNo more profiles to process")
                        break
                    
                retry_count = 0  # Reset retry count on successful fetch
                
                # Prepare profiles for classification
                profiles_to_classify = []
                for profile in profiles:
                    try:
                        profile_data = prepare_profile_for_classification(profile)
                        profiles_to_classify.append(profile_data)
                    except Exception as e:
                        print(f"\nError preparing profile {profile.get('user_id')}: {str(e)}")
                        failed += 1
                        
                # Classify batch
                if profiles_to_classify:
                    try:
                        classifications = classifier.batch_classify(profiles_to_classify)
                        
                        # Store results
                        for profile, classification in zip(profiles_to_classify, classifications):
                            try:
                                if store_profile_classification(supabase, profile['user_id'], classification):
                                    processed += 1
                                else:
                                    failed += 1
                            except Exception as e:
                                print(f"\nError storing classification for user {profile.get('user_id')}: {str(e)}")
                                failed += 1
                                
                        # Only increment start if batch was successful
                        current_start += len(profiles)
                        # Update progress
                        pbar.update(len(profiles))
                        
                    except KeyboardInterrupt:
                        print(f"\n\n⚠️  Processing interrupted at offset {current_start}")
                        print(f"To continue, run the script with: python classify_and_store_profiles.py {current_start}")
                        return
                        
                    except Exception as e:
                        print(f"\nError classifying batch: {str(e)}")
                        if retry_count < max_retries:
                            print(f"Retrying batch... (attempt {retry_count + 1}/{max_retries})")
                            retry_count += 1
                            continue
                        else:
                            print("Max retries reached, skipping batch")
                            failed += len(profiles_to_classify)
                            current_start += len(profiles)
                            pbar.update(len(profiles))
                        
            except Exception as e:
                print(f"\nError processing batch: {str(e)}")
                if retry_count < max_retries:
                    print(f"Retrying batch... (attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                else:
                    print("Max retries reached, skipping batch")
                    failed += batch_size
                    current_start += batch_size
                    pbar.update(batch_size)
    
    print(f"\n✅ Successfully processed {processed} profiles")
    if failed > 0:
        print(f"⚠️  Failed to process {failed} profiles")
    print("\n✨ Done!")

if __name__ == "__main__":
    import sys
    start_from = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(start_from=start_from)