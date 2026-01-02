"""
TEST FILE – ATSN RL SYSTEM DEMO
Purpose: Show end-to-end flow without frontend or real APIs
"""

import numpy as np
from main import run_one_post
import time

def demo_single_post():
    print("\n==============================")
    print("🚀 ATSN RL DEMO – SINGLE POST")
    print("==============================")

    # Fake topic embedding (normally from LLM / trend engine)
    topic_embedding = np.random.rand(384).astype("float32")

    run_one_post(
        topic_embedding=topic_embedding,
        platform="instagram",
        date="2025-01-01",
        time="evening"
    )

    print("\n⏳ Waiting for async RL jobs...")
    time.sleep(5)

    print("\n✅ Demo completed")
    print("Check DB tables:")
    print("- post_contents")
    print("- rl_actions")
    print("- post_rewards")
    print("- rl_preferences")
    print("- rl_baselines")

if __name__ == "__main__":
    demo_single_post()
