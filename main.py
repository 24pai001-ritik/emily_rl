# main.py
"""
MAIN ORCHESTRATOR

Flow:
1. Decide topic + post type
2. Generate prompts (via generate.py + RL)
3. Store content (post_contents)
4. (Simulate) post publishing
5. Collect metrics (simulated for now)
6. Compute reward
7. Update RL
"""

import uuid
import time
import random
from datetime import datetime
import numpy as np
#from campaign import topic,date,time,platform

import db
from rl_agent import update_rl, compute_reward
from generate import generate_prompts

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
 
PLATFORM = "instagram"
BUSINESS_ID = "550e8400-e29b-41d4-a716-446655440000"
FOLLOWERS = 1816

# -------------------------------------------------
# SIMPLE HELPERS (later replace with real systems)
# -------------------------------------------------

# make campaign topic selection

# def decide_post_type() -> str:
    # return "educational post"





# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------

def run_one_post(topic, platform, date, time):
    print(f"\n🚀 Starting new post cycle for {platform} at {date} {time}")

    # ---------- 1️⃣ BUSINESS CONTEXT ----------
    


    # embeddings (replace with real embedding service)
    # Get business embedding from profiles table
    business_embedding = db.get_profile_embedding_with_fallback(BUSINESS_ID)
    topic_embedding = np.random.rand(384).astype("float32")  # Keep random for now or implement topic embeddings

    # ---------- 2️⃣ GENERATE PROMPTS (RL INSIDE) ----------
    inputs = {
        "BUSINESS_CONTEXT": business_embedding,
        "TOPIC": topic,
        "PLATFORM": platform,
        "DATE": date,
        "TIME": time
    }

    result = generate_prompts(
        inputs,
        business_embedding,
        topic_embedding,
        platform,
        date,
        time
    )

    # Extract values based on mode
    action = result["action"]
    context = result["context"]
    ctx_vec = result["ctx_vec"]
    mode = result["mode"]
    prompt_text = result.get("grok_prompt") or result.get("prompt", "") or result.get("image_prompt", "")

    # ---------- 3️⃣ STORE RL ACTION ----------
    post_id = f"{platform}_{uuid.uuid4().hex[:8]}"

    action_id = db.insert_action(
        post_id=post_id,
        platform=platform,
        context=context,
        action=action
    )

    # ---------- 4️⃣ STORE POST CONTENT ----------
    db.insert_post_content(
        post_id=post_id,
        action_id=action_id,
        platform=platform,
        business_id=BUSINESS_ID,
        topic=topic,
        # post_type=post_type,
        image_prompt=result["image_prompt"],
        caption_prompt="(caption prompt generated later)",
        status="generated"
    )

    print("📝 Prompt generated and stored")
    print("🎯 RL Action:", action)

    # ---------- 5️⃣ SIMULATE POSTING ----------
   

    db.mark_post_as_posted(post_id)

    # ---------- 6️⃣ COLLECT METRICS ----------
    metrics = db.get_real_platform_metrics(post_id, platform)
    print("📊 Metrics:", metrics)

    # ---------- 7️⃣ STORE SNAPSHOT ----------
    db.insert_post_snapshot(
        post_id=post_id,
        platform=platform,
        metrics=metrics
    )

    # ---------- 8️⃣ COMPUTE & STORE REWARD ----------
    reward = compute_reward(
    platform=platform,
    metrics=metrics,
    deleted=False,
    days_since_post=None
    )


    baseline = db.update_and_get_baseline(
        platform=platform,
        reward=reward
    )

    db.insert_reward(
        action_id=action_id,  # Changed from post_id to action_id
        reward=reward,
        baseline=baseline,
        platform=platform
    )

    print(f"🏆 Reward={reward:.3f}, Baseline={baseline:.3f}")

    # ---------- 9️⃣ RL LEARNING ----------
    update_rl(
        context=context,
        action=action,
        reward=reward,
        baseline=baseline, 
        ctx_vec=ctx_vec,
        lr_discrete=0.05,
        lr_theta=0.01
    )

    print("🧠 RL updated successfully")


# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":
    # Example usage: topic, platform, date, time
    run_one_post(
        topic="AI for marketing",
        platform="instagram",
        date="2024-12-26",
        time="evening"
    )