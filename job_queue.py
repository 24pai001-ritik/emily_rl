# job_queue.py - Simple job system for RL learning

import asyncio
import time
import threading
from queue import Queue
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

# Indian Standard Time (IST) - Asia/Kolkata
IST = pytz.timezone("Asia/Kolkata")
import db
import rl_agent

# Thread-safe job queue (replace with Redis/Celery for production)
job_queue = Queue()
job_results = {}  # Store job results by job_id
running_jobs = set()  # Track running job IDs

class Job:
    def __init__(self, job_type: str, job_id: str, payload: Dict[str, Any]):
        self.job_type = job_type  # "reward_calculation" or "rl_update"
        self.job_id = job_id
        self.payload = payload
        self.created_at = datetime.now(IST)
        self.status = "queued"

async def process_reward_calculation_job(job: Job) -> Dict[str, Any]:
    """Process reward calculation job"""
    try:
        payload = job.payload
        profile_id = payload["profile_id"]
        post_id = payload["post_id"]
        platform = payload["platform"]

        print(f"Processing reward calculation for {post_id} on {platform}")

        # Calculate reward
        result = db.fetch_or_calculate_reward(profile_id, post_id, platform)

        # Debug: Print result
        print(f"🔍 Reward calculation result: {result}")

        if result["status"] == "calculated":
            # Queue RL update job
            rl_job = Job(
                job_type="rl_update",
                job_id=f"rl_{post_id}_{int(time.time())}",
                payload={
                    "profile_id": profile_id,
                    "post_id": post_id,
                    "platform": platform,
                    "reward_value": result["reward"]
                }
            )
            job_queue.put(rl_job)
            print(f"📋 Queued RL update job for {post_id}")

        return result

    except Exception as e:
        print(f"❌ Error in reward calculation job: {e}")
        return {"status": "error", "error": str(e)}

async def process_rl_update_job(job: Job) -> Dict[str, Any]:
    """Process RL update job"""
    try:
        payload = job.payload
        profile_id = payload["profile_id"]
        post_id = payload["post_id"]
        platform = payload["platform"]
        reward_value = payload["reward_value"]

        print(f"🧠 Processing RL update for {post_id} (reward: {reward_value:.4f})")

        # Get action and context from database
        # This assumes the action and context are stored during posting
        action_data = get_action_and_context_from_db(post_id, platform)

        if not action_data:
            print(f"⚠️  No action data found for {post_id}, skipping RL update")
            return {"status": "skipped", "reason": "no_action_data"}

        action = action_data["action"]
        context = action_data["context"]
        ctx_vec = action_data["ctx_vec"]

        # Get current baseline using pure mathematical update
        current_baseline = db.update_baseline_mathematical(platform, reward_value, beta=0.1)

        # Update RL
        rl_agent.update_rl(
            context=context,
            action=action,
            ctx_vec=ctx_vec,
            reward=reward_value,
            baseline=current_baseline
        )

        print(f"✅ RL update completed for {post_id}")
        return {"status": "completed", "baseline": current_baseline}

    except Exception as e:
        print(f"❌ Error in RL update job: {e}")
        return {"status": "error", "error": str(e)}

def get_action_and_context_from_db(post_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """Get action and context data from database for RL update"""
    try:
        # Get action data from rl_actions table
        action_result = db.supabase.table("rl_actions").select("*").eq("post_id", post_id).eq("platform", platform).execute()

        if not action_result.data:
            return None

        action_row = action_result.data[0]

        # Reconstruct action dict
        action = {
            "HOOK_TYPE": action_row.get("hook_type"),
            "LENGTH": action_row.get("hook_length"),
            "TONE": action_row.get("tone"),
            "CREATIVITY": action_row.get("creativity"),
            "TEXT_IN_IMAGE": action_row.get("text_in_image"),
            "VISUAL_STYLE": action_row.get("visual_style")
        }

        # Reconstruct context (this is simplified - in production you'd store the full context)
        context = {
            "platform": platform,
            "time_bucket": action_row.get("time_bucket"),
            "day_of_week": action_row.get("day_of_week"),
            "business_embedding": db.get_profile_embedding_with_fallback("7648103e-81be-4fd9-b573-8e72e2fcbe5d"),  # Default business ID
            "topic_embedding": db.get_profile_embedding_with_fallback("7648103e-81be-4fd9-b573-8e72e2fcbe5d")  # Placeholder
        }

        # Reconstruct context vector
        from rl_agent import build_context_vector
        ctx_vec = build_context_vector(context)

        return {
            "action": action,
            "context": context,
            "ctx_vec": ctx_vec
        }

    except Exception as e:
        print(f"❌ Error retrieving action data for {post_id}: {e}")
        return None

def job_worker():
    """Main job processing worker (synchronous)"""
    print("🚀 Starting RL job worker...")

    while True:
        try:
            print("Job worker waiting for jobs...")
            job = job_queue.get()  # Blocking get
            print(f"📥 Job worker received job: {job.job_id}")
            job.status = "running"
            running_jobs.add(job.job_id)

            print(f"📋 Processing job {job.job_id} ({job.job_type})")

            # Create new event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                if job.job_type == "reward_calculation":
                    result = loop.run_until_complete(process_reward_calculation_job(job))
                elif job.job_type == "rl_update":
                    result = loop.run_until_complete(process_rl_update_job(job))
                else:
                    result = {"status": "error", "error": f"Unknown job type: {job.job_type}"}

                # Debug: Print job completion
                print(f"✅ Job {job.job_id} completed with result: {result}")

                job_results[job.job_id] = result
            finally:
                loop.close()

            running_jobs.remove(job.job_id)

        except Exception as e:
            print(f"❌ Job worker error: {e}")
            time.sleep(1)  # Brief pause on error

def queue_reward_calculation_job(profile_id: str, post_id: str, platform: str) -> str:
    """Queue a reward calculation job"""
    job_id = f"reward_{post_id}_{int(time.time())}"
    job = Job(
        job_type="reward_calculation",
        job_id=job_id,
        payload={
            "profile_id": profile_id,
            "post_id": post_id,
            "platform": platform
        }
    )

    job_queue.put(job)
    print(f"📋 Queued reward calculation job: {job_id}")
    print(f"📊 Current queue size: {job_queue.qsize()}")
    return job_id

def start_job_worker():
    """Start the job worker in a background thread"""
    def run_worker():
        asyncio.run(job_worker())

    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    print("RL job worker started in background thread")

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a job"""
    return job_results.get(job_id)


# Start worker when module is imported
start_job_worker()
