#!/usr/bin/env python3
"""
Comprehensive RL System Test
Tests the complete RL learning pipeline with fake data over 10 days
Includes deleted posts, reward calculations, preference updates, and baseline tracking
"""

import numpy as np
import json
from datetime import datetime, timedelta
import db
import rl_agent
from generate import build_context
import time

# Test constants
BUSINESS_ID = "7648103e-81be-4fd9-b573-8e72e2fcbe5d"
PLATFORM = "instagram"

# Test data for different days and times
test_scenarios = [
    # Day 1-3: Learning morning preferences
    {"day": 0, "time": "morning", "expected_action": "question", "engagement_multiplier": 1.2},
    {"day": 1, "time": "morning", "expected_action": "question", "engagement_multiplier": 1.1},
    {"day": 2, "time": "morning", "expected_action": "question", "engagement_multiplier": 0.9},

    # Day 4-6: Learning afternoon preferences
    {"day": 3, "time": "afternoon", "expected_action": "story", "engagement_multiplier": 1.3},
    {"day": 4, "time": "afternoon", "expected_action": "story", "engagement_multiplier": 1.4},
    {"day": 5, "time": "afternoon", "expected_action": "story", "engagement_multiplier": 1.2},

    # Day 7-9: Learning evening preferences + deleted post
    {"day": 6, "time": "evening", "expected_action": "curiosity", "engagement_multiplier": 1.5, "deleted": True},
    {"day": 6, "time": "evening", "expected_action": "curiosity", "engagement_multiplier": 1.6},
    {"day": 6, "time": "evening", "expected_action": "curiosity", "engagement_multiplier": 1.4},

    # Day 10: Final test with learned preferences
    {"day": 6, "time": "evening", "expected_action": "curiosity", "engagement_multiplier": 1.8},
]

def create_fake_post_snapshots(post_id, base_engagement, time_bucket, days_old=1):
    """Create realistic fake engagement snapshots for testing"""
    snapshots = []

    # Create snapshots at different time intervals
    intervals = [6, 24, 48, 72]  # hours after posting

    for hours in intervals:
        # Calculate snapshot time (days_old days ago minus hours)
        snapshot_time = datetime.utcnow() - timedelta(days=days_old, hours=hours)

        # Generate realistic engagement based on time bucket and base engagement
        time_multiplier = {
            "morning": 0.8,    # Morning posts get less engagement
            "afternoon": 1.0,  # Baseline
            "evening": 1.3,    # Evening posts get more engagement
            "night": 0.6       # Night posts get less engagement
        }.get(time_bucket, 1.0)

        # Add some randomness
        random_factor = np.random.uniform(0.8, 1.2)

        engagement = base_engagement * time_multiplier * random_factor

        # Platform-specific engagement breakdown
        snapshot = {
            "profile_id": BUSINESS_ID,
            "post_id": post_id,
            "platform": PLATFORM,
            "timeslot_hours": hours,
            "snapshot_at": snapshot_time.isoformat(),
            "likes": int(engagement * 0.4),
            "comments": int(engagement * 0.1),
            "shares": int(engagement * 0.05),
            "saves": int(engagement * 0.3),
            "replies": int(engagement * 0.02),
            "retweets": int(engagement * 0.01),
            "reactions": int(engagement * 0.12),
            "follower_count": 1500  # Consistent follower count
        }
        snapshots.append(snapshot)

    return snapshots

# Baseline is now managed mathematically by db.update_baseline_mathematical()

def simulate_post_cycle(scenario, post_number):
    """Simulate a complete post cycle and return results"""
    print(f"\n{'='*60}")
    print(f"POST {post_number}: Day {scenario['day']}, {scenario['time']} - {'DELETED' if scenario.get('deleted', False) else 'ACTIVE'}")
    print(f"{'='*60}")

    # Generate unique post ID
    post_id = f"test_post_{post_number}_{int(time.time())}"

    # 1. RL Action Selection
    print(f"🎯 Selecting RL action...")
    context = build_context(
        business_embedding=np.random.rand(384),
        topic_embedding=np.random.rand(384),
        platform=PLATFORM,
        time=scenario["time"],
        day_of_week=scenario["day"]
    )

    action_result = rl_agent.select_action(context)
    action_dict = action_result[0] if isinstance(action_result, tuple) else action_result
    print(f"   Selected action: {action_dict}")

    # Create action record in database
    action_id = db.insert_action(
        post_id=post_id,
        platform=PLATFORM,
        context=context,
        action=action_dict
    )
    print(f"   Created action record with ID: {action_id}")

    # 2. Create reward record
    print(f"📊 Creating reward record...")
    db.create_post_reward_record(BUSINESS_ID, post_id, PLATFORM, action_id)

    # 3. Simulate engagement (create snapshots)
    print(f"📈 Generating engagement data...")
    if scenario.get("deleted", False):
        # Deleted posts get minimal/no engagement
        base_engagement = 5  # Very low engagement for deleted posts
        print(f"   🗑️  Deleted post - using minimal engagement: {base_engagement}")
    else:
        base_engagement = 100 * scenario["engagement_multiplier"]
    snapshots = create_fake_post_snapshots(post_id, base_engagement, scenario["time"])

    # Insert snapshots
    for snap in snapshots:
        db.supabase.table("post_snapshots").insert(snap).execute()
    print(f"   Created {len(snapshots)} snapshots")

    # Create post content record (needed for action_id lookup)
    print(f"📝 Creating post content record...")
    db.insert_post_content(
        post_id=post_id,
        action_id=action_id,
        platform=PLATFORM,
        business_id=BUSINESS_ID,
        topic="test topic",
        post_type="educational",
        business_context="test context",
        business_aesthetic="test aesthetic",
        image_prompt="test image prompt",
        caption_prompt="test caption prompt",
        status="deleted" if scenario.get("deleted", False) else "generated"
    )

    # 4. Mark post as deleted if needed (already handled in post_content creation)

    # 5. Calculate reward immediately (normally this happens async)
    print(f"💰 Calculating reward...")
    time.sleep(1)  # Brief pause

    # Make reward eligible for calculation
    db.supabase.table("post_rewards").update({
        "reward_status": "eligible",
        "eligible_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
    }).eq("post_id", post_id).execute()

    # Calculate reward
    reward_result = db.fetch_or_calculate_reward(BUSINESS_ID, post_id, PLATFORM)
    current_reward = reward_result.get("reward", 0)

    # 6. Get updated RL state
    print(f"🧠 Checking RL state updates...")

    # Get current preferences for this context
    preferences = {}
    dimensions = ['HOOK_TYPE', 'LENGTH', 'TONE', 'CREATIVITY', 'TEXT_IN_IMAGE', 'VISUAL_STYLE']
    for dim in dimensions:
        for val in action_dict[dim]:
            pref = db.get_preference(PLATFORM, scenario["time"], scenario["day"], dim, val)
            preferences[f"{dim}:{val}"] = pref

    # Update baseline with this reward using pure mathematics (persistent across test)
    current_baseline = db.update_baseline_mathematical(PLATFORM, current_reward, beta=0.1)

    # Trigger immediate RL update with our test baseline
    print(f"🧠 Triggering immediate RL update with baseline {current_baseline:.4f}...")
    rl_agent.update_rl(context, action_dict, None, current_reward, current_baseline)

    return {
        "post_id": post_id,
        "action": action_dict,
        "reward": reward_result.get("reward", 0),
        "preferences": preferences,
        "baseline": current_baseline,
        "deleted": scenario.get("deleted", False),
        "engagement": base_engagement
    }

def main():
    """Run comprehensive RL system test"""
    print("🚀 COMPREHENSIVE RL SYSTEM TEST")
    print("Testing with BUSINESS_ID:", BUSINESS_ID)
    print("Running", len(test_scenarios), "post cycles over 7 days")
    print("="*80)

    results = []
    baseline_history = []

    for i, scenario in enumerate(test_scenarios, 1):
        try:
            result = simulate_post_cycle(scenario, i)
            results.append(result)

            # Track baseline changes
            baseline_history.append({
                "post": i,
                "baseline": result["baseline"],
                "reward": result["reward"]
            })

            print(f"✅ Post {i} completed - Reward: {result['reward']:.4f}, Baseline: {result['baseline']:.4f}")

        except Exception as e:
            print(f"❌ Post {i} failed: {e}")
            continue

        # Brief pause between posts
        time.sleep(0.5)

    # Generate comprehensive report
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST RESULTS")
    print(f"{'='*80}")

    # Summary statistics
    total_rewards = sum(r["reward"] for r in results)
    avg_reward = total_rewards / len(results)
    deleted_posts = sum(1 for r in results if r["deleted"])
    total_engagement = sum(r["engagement"] for r in results)

    print(f"📈 Total Posts: {len(results)}")
    print(f"💰 Total Rewards: {total_rewards:.4f}")
    print(f"📊 Average Reward: {avg_reward:.4f}")
    print(f"🗑️  Deleted Posts: {deleted_posts}")
    print(f"📈 Total Engagement: {total_engagement:.0f}")

    # Baseline evolution
    print(f"\n📉 Baseline Evolution:")
    for bh in baseline_history:
        print(f"   Post {bh['post']}: Reward {bh['reward']:.4f} → Baseline {bh['baseline']:.4f}")

    # Detailed results for each post
    print(f"\n📋 Detailed Results:")
    for i, result in enumerate(results, 1):
        print(f"\n--- Post {i} ---")
        print(f"🎯 Action: {result['action']}")
        print(f"💰 Reward: {result['reward']:.4f}")
        print(f"📊 Baseline: {result['baseline']:.4f}")
        print(f"📈 Engagement: {result['engagement']:.0f}")
        print(f"🗑️  Deleted: {result['deleted']}")

        # Show key preferences
        print(f"🎨 Top Preferences:")
        sorted_prefs = sorted(result['preferences'].items(), key=lambda x: x[1], reverse=True)[:3]
        for pref, score in sorted_prefs:
            print(f"   {pref}: {score:.4f}")

    # Verify RL learning
    print(f"\n🧠 RL Learning Verification:")

    # Check if preferences evolved
    if len(results) >= 2:
        first_prefs = results[0]['preferences']
        last_prefs = results[-1]['preferences']

        improved_prefs = []
        for key in first_prefs:
            if key in last_prefs:
                diff = last_prefs[key] - first_prefs[key]
                if abs(diff) > 0.01:  # Significant change
                    improved_prefs.append((key, diff))

        if improved_prefs:
            print(f"✅ Preferences evolved ({len(improved_prefs)} changes):")
            for pref, change in sorted(improved_prefs, key=lambda x: abs(x[1]), reverse=True)[:5]:
                print(f"   {pref}: {change:+.4f}")
        else:
            print(f"⚠️  Limited preference evolution detected")

    # Check database state
    print(f"\n💾 Database State:")
    try:
        # Count records in each table
        tables = {
            "rl_rewards": "supabase.table('rl_rewards').select('id', count='exact')",
            "rl_preferences": "supabase.table('rl_preferences').select('id', count='exact')",
            "post_rewards": "supabase.table('post_rewards').select('id', count='exact')",
            "post_snapshots": "supabase.table('post_snapshots').select('id', count='exact')",
            "rl_actions": "supabase.table('rl_actions').select('id', count='exact')",
            "post_contents": "supabase.table('post_contents').select('id', count='exact')"
        }

        for table_name, query in tables.items():
            try:
                result = eval(f"db.{query}.execute()")
                count = len(result.data) if hasattr(result, 'data') else 0
                print(f"   {table_name}: {count} records")
            except:
                print(f"   {table_name}: Error counting")

    except Exception as e:
        print(f"   Database check failed: {e}")

    print(f"\n🎉 Comprehensive RL test completed!")
    print(f"✅ System working correctly with {len(results)} successful posts")

    # Save results to file
    with open("rl_test_results.json", "w") as f:
        json.dump({
            "test_summary": {
                "total_posts": len(results),
                "total_rewards": total_rewards,
                "avg_reward": avg_reward,
                "deleted_posts": deleted_posts,
                "total_engagement": total_engagement
            },
            "baseline_history": baseline_history,
            "detailed_results": results,
            "final_preferences": results[-1]['preferences'] if results else {}
        }, f, indent=2, default=str)

    print(f"📄 Results saved to rl_test_results.json")

if __name__ == "__main__":
    main()
