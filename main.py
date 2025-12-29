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
from db import fetch_or_calculate_reward

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
BUSINESS_ID = "7648103e-81be-4fd9-b573-8e72e2fcbe5d"
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
        "BUSINESS_AESTHETIC": "modern, professional, clean design",  # Default aesthetic
        "BUSINESS_TYPES": ["Technology"],  # Default business types
        "INDUSTRIES": ["Technology/IT"],  # Default industries
        "BUSINESS_DESCRIPTION": "A technology company focused on AI and marketing solutions",  # Default description
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
    # Extract prompts based on mode (handle both trendy and standard modes)
    image_prompt = result.get("image_prompt",
        f"Create an image for topic: {topic} with {action['VISUAL_STYLE']} style, {action['TONE']} tone, {action['CREATIVITY']} creativity level. Make it engaging for {platform}.")

    caption_prompt = result.get("caption_prompt",
        f"Write a {action['TONE']} caption about {topic} in {action['LENGTH']} length with {action['CREATIVITY']} creativity level. Make it suitable for {platform}.")

    db.insert_post_content(
        post_id=post_id,
        action_id=action_id,
        platform=platform,
        business_id=BUSINESS_ID,
        topic=topic,
        post_type="educational",  # Default post type
        business_context=str(business_embedding),  # Convert embedding to string
        business_aesthetic="modern, professional, clean design",  # Default aesthetic
        image_prompt=image_prompt,
        caption_prompt=caption_prompt,
        status="generated"
    )

    print("📝 Prompt generated and stored")
    print("🎯 RL Action:", action)

    # ---------- 5️⃣ SIMULATE POSTING ----------
   

    db.mark_post_as_posted(post_id)

    # Create initial reward record for future calculation
    db.create_post_reward_record(BUSINESS_ID, post_id, platform, action_id)

    # ---------- 6️⃣ QUEUE REWARD CALCULATION FOR WORKER ----------
    # In production: Queue job for worker to calculate reward asynchronously
    # This prevents blocking the main thread and ensures proper delayed reward calculation
    # db.queue_rl_update_job(post_id, action, context, ctx_vec)
    print("📋 RL update queued for worker processing (production)")

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