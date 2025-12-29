# db.py
import os
import numpy as np
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise ValueError(f"Failed to create Supabase client: {e}")

# ---------- PREFERENCES ----------

def get_preference(platform, time_bucket, day, dimension, value):
    try:
        res = supabase.table("rl_preferences") \
            .select("preference_score") \
            .eq("platform", platform) \
            .eq("time_bucket", time_bucket) \
            .eq("day_of_week", day) \
            .eq("dimension", dimension) \
            .eq("action_value", value) \
            .execute()

        if res.data and len(res.data) > 0 and "preference_score" in res.data[0]:
            return float(res.data[0]["preference_score"])
        return 0.0
    except Exception as e:
        print(f"Error getting preference for {platform}, {dimension}={value}: {e}")
        return 0.0


def update_preference(platform, time_bucket, day, dimension, value, delta):
    """
    Update preference scores with increment operations.

    NOTE: This implementation still has a potential race condition between
    SELECT and UPDATE operations. For production systems, consider:

    1. Using database triggers for atomic increments
    2. Creating a stored procedure for this operation
    3. Using PostgreSQL's ON CONFLICT DO UPDATE with increment logic
    4. Implementing optimistic locking with version columns

    Current implementation includes error handling and retry logic as mitigation.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = supabase.table("rl_preferences") \
                .select("id, preference_score, num_samples") \
                .eq("platform", platform) \
                .eq("time_bucket", time_bucket) \
                .eq("day_of_week", day) \
                .eq("dimension", dimension) \
                .eq("action_value", value) \
                .execute()

            if res.data and len(res.data) > 0:
                row = res.data[0]
                if "id" in row and "preference_score" in row and "num_samples" in row:
                    current_score = float(row["preference_score"])
                    current_samples = int(row["num_samples"])

                    supabase.table("rl_preferences").update({
                        "preference_score": current_score + delta,
                        "num_samples": current_samples + 1,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", row["id"]).execute()
                    return  # Success
            else:
                # Insert new preference - use upsert for safety
                try:
                    supabase.table("rl_preferences").upsert({
                        "platform": platform,
                        "time_bucket": time_bucket,
                        "day_of_week": day,
                        "dimension": dimension,
                        "action_value": value,
                        "preference_score": delta,
                        "num_samples": 1
                    }).execute()
                    return  # Success
                except Exception as insert_error:
                    # If upsert fails, the row might have been inserted by another process
                    # Try update instead
                    if attempt < max_retries - 1:  # Don't retry on last attempt
                        continue
                    raise insert_error

            # If we get here, something unexpected happened
            if attempt == max_retries - 1:
                raise ValueError("Failed to update preference after all retries")

        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                print(f"Error updating preference for {platform}, {dimension}={value} after {max_retries} attempts: {e}")
                raise
            else:
                print(f"Attempt {attempt + 1} failed, retrying: {e}")
                continue
def insert_post_content(
    post_id,
    action_id,
    platform,
    business_id,
    topic,
    post_type,
    business_context,
    business_aesthetic,
    image_prompt,
    caption_prompt,
    generated_caption=None,
    generated_image_url=None,
    status="generated"
):
    try:
        supabase.table("post_contents").insert({
            "post_id": post_id,
            "action_id": action_id,
            "platform": platform,
            "business_id": business_id,
            "topic": topic,
            "post_type": post_type,
            "business_context": business_context,
            "business_aesthetic": business_aesthetic,
            "image_prompt": image_prompt,
            "caption_prompt": caption_prompt,
            "generated_caption": generated_caption,
            "generated_image_url": generated_image_url,
            "status": status
        }).execute()
    except Exception as e:
        print(f"Error inserting post content for post_id {post_id}: {e}")
        raise
def mark_post_as_posted(post_id):
    try:
        supabase.table("post_contents").update({
            "status": "posted",
            "posted_at": datetime.utcnow().isoformat()
        }).eq("post_id", post_id).execute()
    except Exception as e:
        print(f"Error marking post {post_id} as posted: {e}")
        raise
def insert_action(post_id, platform, context, action):
    try:
        res = supabase.table("rl_actions").insert({
            "post_id": post_id,
            "platform": platform,
            "time_bucket": context.get("time_bucket"),
            "day_of_week": context.get("day_of_week"),
            "action": action
        }).execute()

        if res.data and len(res.data) > 0 and "id" in res.data[0]:
            return res.data[0]["id"]
        else:
            raise ValueError("Failed to insert action - no ID returned")    
    except Exception as e:
        print(f"Error inserting action for post_id {post_id}: {e}")
        raise
def insert_post_snapshot(post_id, platform, metrics):
    try:
        # Ensure metrics values are properly typed
        processed_metrics = {}
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                processed_metrics[key] = value
            elif isinstance(value, str) and value.isdigit():
                processed_metrics[key] = int(value)
            else:
                processed_metrics[key] = value  # Keep as-is for strings/other types

        supabase.table("post_snapshots").insert({
            "post_id": post_id,
            "platform": platform,
            **processed_metrics
        }).execute()
    except Exception as e:
        print(f"Error inserting post snapshot for post_id {post_id}: {e}")
        raise
def insert_reward(post_id, reward, baseline):
    try:
        # Ensure numeric types
        reward = float(reward) if reward is not None else None
        baseline = float(baseline) if baseline is not None else None

        supabase.table("rl_rewards").insert({
            "post_id": post_id,
            "reward": reward,
            "baseline": baseline
        }).execute()
    except Exception as e:
        print(f"Error inserting reward for post_id {post_id}: {e}")
        raise
def update_and_get_baseline(platform, reward, alpha=0.1):
    try:
        res = supabase.table("rl_baselines") \
            .select("value") \
            .eq("platform", platform) \
            .execute()

        if res.data and len(res.data) > 0 and "value" in res.data[0]:
            baseline = float(res.data[0]["value"])
            new_baseline = baseline + alpha * (reward - baseline)

            supabase.table("rl_baselines").update({
                "value": new_baseline,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("platform", platform).execute()

            return new_baseline
        else:
            # Insert new baseline
            supabase.table("rl_baselines").insert({
                "platform": platform,
                "value": reward
            }).execute()
            return reward
    except Exception as e:
        print(f"Error updating baseline for platform {platform}: {e}")
        return reward
def get_profile_embedding(profile_id):
    """Retrieve profile embedding from profiles table"""
    try:
        res = supabase.table("profiles") \
            .select("profile_embedding") \
            .eq("id", profile_id) \
            .execute()
        
        if res.data and len(res.data) > 0:
            row = res.data[0]
            if "profile_embedding" in row and row["profile_embedding"] is not None:
                # profile_embedding should be returned as a list/array from Supabase
                embedding_data = row["profile_embedding"]
                
                if isinstance(embedding_data, list):
                    return np.array(embedding_data, dtype=np.float32)
                else:
                    print(f"Unexpected embedding format: {type(embedding_data)}")
                    return None
        
        return None
    except Exception as e:
        print(f"Error retrieving profile embedding for {profile_id}: {e}")
        return None


def get_profile_embedding_with_fallback(profile_id):
    """Get profile embedding with fallback to random"""
    embedding = get_profile_embedding(profile_id)

    if embedding is not None:
        return embedding

    # Fallback to random embedding if not found in database
    print(f"Profile embedding not found for {profile_id}, using random embedding")
    return np.random.rand(384).astype("float32")


def get_post_metrics(post_id, platform):
    """Fetch real metrics for a post from database"""
    try:
        res = supabase.table("post_snapshots") \
            .select("*") \
            .eq("post_id", post_id) \
            .eq("platform", platform) \
            .execute()

        if res.data and len(res.data) > 0:
            # Return the metrics dict, excluding metadata fields
            row = res.data[0]
            metrics = {k: v for k, v in row.items()
                      if k not in ['post_id', 'platform', 'created_at', 'id']}
            return metrics
        return None
    except Exception as e:
        print(f"Error fetching metrics for post {post_id}: {e}")
        return None


def get_real_platform_metrics(post_id, platform):
    """Get real metrics from database or API"""
    # Option 1: Fetch from your database
    metrics = get_post_metrics(post_id, platform)
    if metrics:
        return metrics

    # Option 2: Call social media API if not in DB yet
    # return call_instagram_api(post_id) or call_twitter_api(post_id)

    # Option 3: Return zeros if no data (for very new posts)
    return {"likes": 0, "comments": 0, "shares": 0, "saves": 0, "replies": 0, "retweets": 0, "reactions": 0, "followers": 0}