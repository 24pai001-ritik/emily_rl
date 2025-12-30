#!/usr/bin/env python3
"""
RL Progression Test - Shows RL learning over multiple posts
"""

import numpy as np
import json
import db
import rl_agent
from generate import build_context
import time

BUSINESS_ID = "7648103e-81be-4fd9-b573-8e72e2fcbe5d"
PLATFORM = "instagram"

def run_single_post_test(post_num, time_bucket, day_of_week, expected_reward_range=(0.3, 0.8)):
    """Run a single post test and return results"""
    print(f"\n{'='*50}")
    print(f"POST {post_num}: {time_bucket} on day {day_of_week}")
    print(f"{'='*50}")

    # Generate unique post ID
    post_id = f"progression_test_{post_num}_{int(time.time())}"

    # 1. Get RL action
    context = build_context(
        business_embedding=np.random.rand(384),
        topic_embedding=np.random.rand(384),
        platform=PLATFORM,
        time=time_bucket,
        day_of_week=day_of_week
    )

    action = rl_agent.select_action(context)
    print(f"🎯 RL Action: {action}")

    # 2. Create reward record
    db.create_post_reward_record(BUSINESS_ID, post_id, PLATFORM)

    # 3. Create fake snapshots with realistic engagement
    base_engagement = np.random.uniform(50, 200)  # Random engagement
    snapshots = [
        {
            "profile_id": BUSINESS_ID,
            "post_id": post_id,
            "platform": PLATFORM,
            "timeslot_hours": 6,
            "snapshot_at": "2024-12-30T10:00:00Z",
            "likes": int(base_engagement * 0.4),
            "comments": int(base_engagement * 0.1),
            "shares": int(base_engagement * 0.05),
            "saves": int(base_engagement * 0.3),
            "replies": 0,
            "retweets": 0,
            "reactions": int(base_engagement * 0.15),
            "follower_count": 1500
        },
        {
            "profile_id": BUSINESS_ID,
            "post_id": post_id,
            "platform": PLATFORM,
            "timeslot_hours": 24,
            "snapshot_at": "2024-12-30T16:00:00Z",
            "likes": int(base_engagement * 0.8),
            "comments": int(base_engagement * 0.2),
            "shares": int(base_engagement * 0.1),
            "saves": int(base_engagement * 0.5),
            "replies": 0,
            "retweets": 0,
            "reactions": int(base_engagement * 0.3),
            "follower_count": 1500
        }
    ]

    for snap in snapshots:
        db.supabase.table("post_snapshots").insert(snap).execute()

    # 4. Calculate reward (make it eligible first)
    db.supabase.table("post_rewards").update({
        "reward_status": "eligible",
        "eligible_at": "2024-12-29T10:00:00Z"  # Past time
    }).eq("post_id", post_id).execute()

    reward_result = db.fetch_or_calculate_reward(BUSINESS_ID, post_id, PLATFORM)
    reward_value = reward_result.get("reward", 0)

    # 5. Get updated RL state
    preferences = {}
    for dim, val in action.items():
        pref = db.get_preference(PLATFORM, time_bucket, day_of_week, dim, val)
        preferences[f"{dim}:{val}"] = pref

    baseline = db.update_and_get_baseline(PLATFORM, reward)

    print(f"💰 Reward: {reward_value:.4f}")
    print(f"📊 Baseline: {baseline:.4f}")
    print(f"📈 Engagement: {base_engagement:.0f}")

    return {
        "post_id": post_id,
        "action": action,
        "reward": reward_value,
        "baseline": baseline,
        "engagement": base_engagement,
        "preferences": preferences
    }

def main():
    """Run progression test showing RL learning"""
    print("🚀 RL PROGRESSION TEST")
    print("Testing RL learning over multiple posts")
    print("="*60)

    results = []

    # Test scenarios that should show learning progression
    scenarios = [
        {"time": "morning", "day": 1, "description": "Monday morning"},
        {"time": "morning", "day": 1, "description": "Monday morning #2"},
        {"time": "afternoon", "day": 2, "description": "Tuesday afternoon"},
        {"time": "afternoon", "day": 2, "description": "Tuesday afternoon #2"},
        {"time": "evening", "day": 3, "description": "Wednesday evening"},
        {"time": "evening", "day": 3, "description": "Wednesday evening #2"},
        {"time": "night", "day": 4, "description": "Thursday night"},
        {"time": "night", "day": 4, "description": "Thursday night #2"},
    ]

    for i, scenario in enumerate(scenarios, 1):
        try:
            result = run_single_post_test(i, scenario["time"], scenario["day"])
            result["description"] = scenario["description"]
            results.append(result)
            print(f"✅ Post {i} completed")
        except Exception as e:
            print(f"❌ Post {i} failed: {e}")
            continue

    # Generate progression report
    print(f"\n{'='*60}")
    print("📊 RL LEARNING PROGRESSION REPORT")
    print(f"{'='*60}")

    # Show reward progression
    print("💰 Reward Progression:")
    for i, result in enumerate(results, 1):
        print(f"   Post {i} ({result['description']}): {result['reward']:.4f}")

    # Show baseline evolution
    print("\n📉 Baseline Evolution:")
    for i, result in enumerate(results, 1):
        print(f"   Post {i}: {result['baseline']:.4f}")

    # Show preference learning for key dimensions
    print("\n🎨 Preference Learning (HOOK_TYPE):")
    hook_prefs = {}
    for result in results:
        for key, pref in result['preferences'].items():
            if key.startswith('HOOK_TYPE:'):
                hook_type = key.split(':')[1]
                if hook_type not in hook_prefs:
                    hook_prefs[hook_type] = []
                hook_prefs[hook_type].append(pref)

    for hook_type, pref_values in hook_prefs.items():
        if len(pref_values) > 1:
            improvement = pref_values[-1] - pref_values[0]
            print(f"   {hook_type}: {pref_values[0]:.4f} → {pref_values[-1]:.4f} ({improvement:+.4f})")

    # Show final RL state
    if results:
        final_result = results[-1]
        print("\n🏆 Final RL State:")
        print(f"   Latest Reward: {final_result['reward']:.4f}")
        print(f"   Final Baseline: {final_result['baseline']:.4f}")

        print(f"   Top Preferences:")
        sorted_prefs = sorted(final_result['preferences'].items(), key=lambda x: x[1], reverse=True)[:5]
        for pref, score in sorted_prefs:
            print(f"      {pref}: {score:.4f}")

    # Save detailed results
    with open("rl_progression_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to rl_progression_results.json")
    print("🎉 RL progression test completed!")

if __name__ == "__main__":
    main()
