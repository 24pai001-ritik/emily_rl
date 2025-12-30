# db.py
import os
import math
import numpy as np
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Reward weights for different time periods (higher weight = more important)
REWARD_WEIGHTS = {     # at alpha = 0.35
    6:   0.396,
    24:  0.258,
    48:  0.168,
    72:  0.109,
    168: 0.071
}

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise ValueError(f"Failed to create Supabase client: {e}")

def calculate_platform_engagement(platform: str, metrics: dict) -> float:
    """
    Calculate platform-specific engagement score.
    Shared utility function used by both reward calculation methods.
    """
    if platform == "instagram":
        # Instagram values SAVES the most
        return (
            3.0 * metrics.get("saves", 0) +
            2.0 * metrics.get("shares", 0) +
            1.0 * metrics.get("comments", 0) +
            0.3 * metrics.get("likes", 0)
        )
    elif platform == "x":
        # X values REPLIES the most
        return (
            3.0 * metrics.get("replies", 0) +
            2.0 * metrics.get("retweets", 0) +
            1.0 * metrics.get("likes", 0)
        )
    elif platform == "linkedin":
        # LinkedIn values COMMENTS + SHARES
        return (
            3.0 * metrics.get("comments", 0) +
            2.0 * metrics.get("shares", 0) +
            1.0 * metrics.get("likes", 0)
        )
    elif platform == "facebook":
        # Facebook values COMMENTS + SHARES
        return (
            3.0 * metrics.get("comments", 0) +
            2.0 * metrics.get("shares", 0) +
            1.0 * metrics.get("reactions", 0)
        )
    else:
        raise ValueError(f"Unsupported platform: {platform}")

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
    print(f"Updating preference: {platform} | {time_bucket} | Day {day} | {dimension}={value} | delta={delta:.6f}")
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
                    new_score = current_score + delta

                    print(f"   📊 Existing preference: {current_score:.4f} → {new_score:.4f} (samples: {current_samples} → {current_samples + 1})")
                    supabase.table("rl_preferences").update({
                        "preference_score": new_score,
                        "num_samples": current_samples + 1,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", row["id"]).execute()
                    return  # Success
            else:
                # Insert new preference - use upsert for safety
                print(f"   🆕 Creating new preference entry with score: {delta:.4f}")
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

def create_post_reward_record(profile_id, post_id, platform, action_id=None):
    """Create initial post reward record when post is published"""
    try:
        # Set post_created_at to now and eligible_at to 24 hours from now
        post_created_at = datetime.utcnow()
        eligible_at = post_created_at + timedelta(hours=24)

        reward_data = {
            "profile_id": profile_id,
            "post_id": post_id,
            "platform": platform,
            "reward_status": "pending",
            "post_created_at": post_created_at.isoformat(),
            "eligible_at": eligible_at.isoformat(),
            "reward_value": None
        }

        # TODO: Add action_id when column is available in schema
        # For now, action_id will be found from post_contents during reward calculation
        # if action_id:
        #     reward_data["action_id"] = action_id

        supabase.table("post_rewards").insert(reward_data).execute()
        print(f"reward data inserted successfully")
        print(f"reward data: {reward_data}")
    except Exception as e:
        print(f"Error creating post reward record for {post_id}: {e}")
        raise
def insert_action(post_id, platform, context, action):
    try:
        res = supabase.table("rl_actions").insert({
            "post_id": post_id,
            "platform": platform,
            "hook_type": action.get("HOOK_TYPE"),
            "hook_length": action.get("LENGTH"),  # Changed from LENGTH to hook_length
            "tone": action.get("TONE"),
            "creativity": action.get("CREATIVITY"),
            "text_in_image": action.get("TEXT_IN_IMAGE"),
            "visual_style": action.get("VISUAL_STYLE"),
            "time_bucket": context.get("time_bucket"),
            "day_of_week": context.get("day_of_week"),
            "topic": None,  # Will be set from main.py
            "business_id": None  # Will be set from main.py
        }).execute()

        if res.data and len(res.data) > 0 and "id" in res.data[0]:
            return res.data[0]["id"]
        else:
            raise ValueError("Failed to insert action - no ID returned")
    except Exception as e:
        print(f"Error inserting action for post_id {post_id}: {e}")
        raise
def insert_post_snapshot(post_id, platform, metrics, profile_id=None, timeslot_hours=24):
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

        # Prepare data according to schema
        snapshot_data = {
            "profile_id": profile_id or "7648103e-81be-4fd9-b573-8e72e2fcbe5d",  # Default business ID
            "post_id": post_id,
            "platform": platform,
            "timeslot_hours": timeslot_hours,
            "snapshot_at": datetime.utcnow().isoformat(),
            **processed_metrics
        }

        supabase.table("post_snapshots").insert(snapshot_data).execute()
    except Exception as e:
        print(f"Error inserting post snapshot for post_id {post_id}: {e}")
        raise

def update_baseline_ema(previous_baseline: float, current_reward: float, beta: float) -> float:
    """
    Reinforcement Learning utility for updating reward baseline using exponential moving average.

    PURPOSE: Normalizes rewards for stable RL learning by maintaining a running average of past rewards.

    FORMULA: b_{t+1} = (1 - β) · b_t + β · R_t

    Args:
        previous_baseline: b_t (current baseline value)
        current_reward: R_t (latest reward from post engagement)
        beta: β (baseline learning rate, typically 0.1, controls adaptation speed)

    Returns:
        updated_baseline: b_{t+1} (new baseline for next reward calculation)

    Example:
        update_baseline_ema(0.45, 0.72, 0.1) → 0.477
    """
    return (1 - beta) * previous_baseline + beta * current_reward

# Global baseline storage for mathematical baseline updates
_platform_baselines = {}

def get_platform_baseline(platform: str, default: float = 0.0) -> float:
    """Get current baseline for a platform"""
    return _platform_baselines.get(platform, default)

def set_platform_baseline(platform: str, baseline: float):
    """Set baseline for a platform"""
    _platform_baselines[platform] = baseline

def update_baseline_mathematical(platform: str, current_reward: float, beta: float = 0.1) -> float:
    """
    Pure mathematical baseline update using exponential moving average.

    Formula: b_{t+1} = (1 - β) · b_t + β · R_t

    This is the ONLY correct way for RL baseline calculation.
    """
    previous_baseline = get_platform_baseline(platform, 0.0)
    new_baseline = update_baseline_ema(previous_baseline, current_reward, beta)

    # Store the updated baseline
    set_platform_baseline(platform, new_baseline)

    print(f"📊 Mathematical baseline update for {platform}: {previous_baseline:.4f} → {new_baseline:.4f} (reward: {current_reward:.4f}, beta: {beta})")

    return new_baseline
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
                # profile_embedding can be returned as a list/array or string from Supabase
                embedding_data = row["profile_embedding"]

                if isinstance(embedding_data, list):
                    return np.array(embedding_data, dtype=np.float32)
                elif isinstance(embedding_data, str):
                    # Parse string representation of vector (e.g., "[1.0, 2.0, 3.0]" or "1.0,2.0,3.0")
                    try:
                        # Remove brackets if present and split by comma
                        cleaned_str = embedding_data.strip('[]')
                        values = [float(x.strip()) for x in cleaned_str.split(',')]
                        return np.array(values, dtype=np.float32)
                    except (ValueError, AttributeError) as parse_error:
                        print(f"Error parsing embedding string: {parse_error}")
                        return None
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

def get_profile_business_data(profile_id):
    """Fetch business-related data from profiles table"""
    try:
        res = supabase.table("profiles").select(
            "business_name, business_type, industry, business_description, brand_voice, brand_tone"
        ).eq("id", profile_id).execute()

        if res.data and len(res.data) > 0:
            profile = res.data[0]

            # Provide defaults if fields are None
            return {
                "business_name": profile.get("business_name", "Business"),
                "business_types": profile.get("business_type", ["General"]),
                "industries": profile.get("industry", ["General"]),
                "business_description": profile.get("business_description", "A business focused on growth and success"),
                "brand_voice": profile.get("brand_voice", "Professional and approachable"),
                "brand_tone": profile.get("brand_tone", "Friendly and informative")
            }

        return {
            "business_name": "Business",
            "business_types": ["General"],
            "industries": ["General"],
            "business_description": "A business focused on growth and success",
            "brand_voice": "Professional and approachable",
            "brand_tone": "Friendly and informative"
        }
    except Exception as e:
        print(f"Error fetching profile business data for {profile_id}: {e}")
        return {
            "business_name": "Business",
            "business_types": ["General"],
            "industries": ["General"],
            "business_description": "A business focused on growth and success",
            "brand_voice": "Professional and approachable",
            "brand_tone": "Friendly and informative"
        }

def get_profile_scheduling_prefs(profile_id):
    """Fetch user's preferred scheduling day and time from profiles table"""
    try:
        res = supabase.table("profiles").select(
            "day_of_week, time_bucket"
        ).eq("id", profile_id).execute()

        if res.data and len(res.data) > 0:
            profile = res.data[0]
            return {
                "day_of_week": profile.get("day_of_week"),
                "time_bucket": profile.get("time_bucket")
            }

        # Fallback defaults if no data found
        return {
            "day_of_week": 3,  # Thursday
            "time_bucket": "evening"
        }
    except Exception as e:
        print(f"Error fetching profile scheduling preferences for {profile_id}: {e}")
        return {
            "day_of_week": 3,  # Thursday
            "time_bucket": "evening"
        }


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



def get_post_reward(profile_id: str, post_id: str, platform: str):
    try:
        res = (
            supabase.table("post_rewards")
            .select("*")
            .eq("profile_id", profile_id)
            .eq("post_id", post_id)
            .eq("platform", platform)
            .single()
            .execute()
        )
        return res.data
    except Exception as e:
        print(f"Error fetching reward record: {e}")
        return None
def get_post_snapshots(profile_id: str, post_id: str, platform: str):
    res = (
        supabase.table("post_snapshots")
        .select("timeslot_hours, likes, comments, shares, saves, replies, retweets, reactions")
        .eq("profile_id", profile_id)
        .eq("post_id", post_id)
        .eq("platform", platform)
        .execute()
    )
    return res.data
def calculate_reward_from_snapshots(snapshots: list, platform: str, post_id: str = None) -> float:
    reward = 0.0
    print(f"🔢 Calculating reward for {platform} with {len(snapshots)} snapshots")

    # Check if post is deleted for penalty calculation
    deleted = False
    days_since_post = None

    if post_id:
        try:
            # Check post status in post_contents table
            post_result = supabase.table("post_contents").select("status, created_at").eq("post_id", post_id).eq("platform", platform).execute()
            if post_result.data and len(post_result.data) > 0:
                post_data = post_result.data[0]
                if post_data.get("status") == "deleted":
                    deleted = True
                    # Calculate days since post creation for penalty scaling
                    if post_data.get("created_at"):
                        created_at = datetime.fromisoformat(post_data["created_at"].replace('Z', '+00:00'))
                        current_time = datetime.utcnow()
                        if created_at.tzinfo is not None:
                            created_at = created_at.replace(tzinfo=None)
                        days_since_post = (current_time - created_at).days
                        print(f"   🗑️  Post is deleted ({days_since_post} days ago), applying penalty")
        except Exception as e:
            print(f"   ⚠️  Could not check post deletion status: {e}")

    for snap in snapshots:
        t = snap["timeslot_hours"]
        weight = REWARD_WEIGHTS.get(t)

        if not weight:
            continue

        # Platform-specific engagement calculation using shared utility
        engagement = calculate_platform_engagement(platform, snap)

        # Apply time-based weighting
        weighted_engagement = weight * engagement
        reward += weighted_engagement
        print(f"   📊 {t}h snapshot: {engagement:.2f} engagement × {weight} weight = {weighted_engagement:.4f}")

    # Apply normalization (log normalization with tanh bounding)
    followers = max(snapshots[0].get("follower_count", 1), 1) if snapshots else 1
    raw_score = math.log(1 + reward) / math.log(1 + followers)
    final_reward = math.tanh(raw_score)

    # -------------------------
    # 3️⃣ Delete penalty (human negative feedback)
    # -------------------------
    if deleted:
        # Deleted post = very strong negative signal
        if days_since_post is None or days_since_post == 0:
            penalty = 1.5  # Immediate deletion = maximum penalty
        else:
            # exponential decay penalty (stronger than before)
            penalty = 1.2 * math.exp(-days_since_post / 2.0)

        print(f"   💥 Applying deletion penalty: -{penalty:.4f} (days_since_post: {days_since_post})")
        final_reward -= penalty

        # Ensure reward doesn't go below -1
        final_reward = max(final_reward, -1.0)

    print(f"   📈 Total reward: {reward:.4f}, Followers: {followers}, Raw score: {raw_score:.4f}, Final reward: {final_reward:.4f}")

    return final_reward
def fetch_or_calculate_reward(profile_id: str, post_id: str, platform: str):
    print(f"🎯 Fetching/calculating reward for post {post_id} on {platform}")
    reward_row = get_post_reward(profile_id, post_id, platform)

    # Handle case where reward record doesn't exist yet
    if reward_row is None:
        print(f"   📝 Reward record doesn't exist yet for {post_id}")
        return {
            "status": "pending",
            "reward": None
        }

    # 1️⃣ Already calculated → return immediately
    if reward_row.get("reward_status") == "calculated":
        existing_reward = reward_row.get("reward_value")
        print(f"   ✅ Reward already calculated: {existing_reward}")
        return {
            "status": "calculated",
            "reward": existing_reward
        }

    # 2️⃣ Check eligibility status (handle multiple valid states)
    status = reward_row.get("reward_status", "pending")
    if status == "pending":
        eligible_at = reward_row.get("eligible_at")
        if eligible_at:
            # Handle timezone-aware vs timezone-naive datetime comparison
            try:
                # Parse the eligible_at datetime and make it timezone-naive for comparison
                if eligible_at.endswith('Z'):
                    eligible_dt = datetime.fromisoformat(eligible_at[:-1])
                else:
                    eligible_dt = datetime.fromisoformat(eligible_at)
                # If it's timezone-aware, convert to naive UTC
                if eligible_dt.tzinfo is not None:
                    eligible_dt = eligible_dt.replace(tzinfo=None)

                current_dt = datetime.utcnow()
                if current_dt < eligible_dt:
                    print(f"   ⏳ Reward not yet eligible (eligible at: {eligible_at})")
                    return {
                        "status": "pending",
                        "reward": None
                    }
            except (ValueError, AttributeError) as e:
                # If parsing fails, assume it's not eligible
                print(f"   ⏳ Could not parse eligible_at: {eligible_at} (error: {e})")
                return {
                    "status": "pending",
                    "reward": None
                }

    # 3️⃣ Eligible or eligible status → calculate ONCE
    print(f"   Calculating reward (status: {status})")
    snapshots = get_post_snapshots(profile_id, post_id, platform)

    if not snapshots:
        # No snapshots available yet
        print(f"   📊 No snapshots available yet for {post_id}")
        return {
            "status": "pending",
            "reward": None
        }

    reward_value = calculate_reward_from_snapshots(snapshots, platform, post_id)

    try:
        print(f"   💾 Updating reward record with calculated value: {reward_value}")
        supabase.table("post_rewards").update({
            "reward_status": "calculated",
            "reward_value": reward_value,
            "calculated_at": datetime.utcnow().isoformat()
        }).eq("id", reward_row["id"]).execute()

        # Also store final reward in rl_rewards table
        print(f"   📊 Storing reward in rl_rewards table")
        action_id = reward_row.get("action_id")

        # If action_id not in reward record, try to find it from post_contents
        if not action_id:
            try:
                post_content = supabase.table("post_contents").select("action_id").eq("post_id", reward_row["post_id"]).eq("platform", platform).execute()
                if post_content.data and len(post_content.data) > 0:
                    action_id = post_content.data[0].get("action_id")
                    print(f"   🔗 Found action_id from post_contents: {action_id}")
            except Exception as e:
                print(f"   ⚠️  Could not find action_id: {e}")

        if not action_id:
            print(f"   ⚠️  Warning: No action_id found, skipping rl_rewards insert")
        else:
            # Calculate and update platform baseline using pure mathematics
            current_baseline = update_baseline_mathematical(platform, reward_value, beta=0.1)

            supabase.table("rl_rewards").insert({
                "action_id": action_id,  # Link to rl_actions record
                "platform": platform,
                "reward_value": reward_value,
                "baseline": current_baseline,  # Now using actual calculated baseline
                "deleted": False,
                "days_to_delete": None,
                "reward_window": "24h"
            }).execute()
        print(f"   ✅ Reward calculation completed successfully")

    except Exception as e:
        print(f"Error updating reward: {e}")
        return {
            "status": "error",
            "reward": None
        }

    return {
        "status": "calculated",
        "reward": reward_value
    }
