#!/usr/bin/env python3
"""Test reward calculation directly (without async jobs)"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db

def create_test_post_and_metrics():
    """Create a test post and metrics directly"""
    print("🏗️ Creating test post and metrics...")

    import uuid
    business_id = "7648103e-81be-4fd9-b573-8e72e2fcbe5d"
    post_id = f"test_direct_{uuid.uuid4().hex[:8]}"
    platform = "instagram"

    # Create reward record first (this is normally done in main.py)
    db.create_post_reward_record(business_id, post_id, platform)
    print("✅ Reward record created")

    # Create test metrics
    metrics = {
        "likes": 150,
        "comments": 25,
        "shares": 8,
        "saves": 45,
        "follower_count": 10000
    }

    # Insert metrics snapshot
    db.insert_post_snapshot(
        post_id=post_id,
        platform=platform,
        metrics=metrics,
        profile_id=business_id,
        timeslot_hours=24
    )
    print("✅ Test metrics created")

    # Make reward eligible immediately
    past_time = datetime.utcnow() - timedelta(hours=25)
    db.supabase.table("post_rewards").update({
        "eligible_at": past_time.isoformat(),
        "reward_status": "pending"  # Reset to pending
    }).eq("post_id", post_id).execute()
    print("✅ Reward made eligible")

    return business_id, post_id, platform

def test_direct_reward_calculation(business_id, post_id, platform):
    """Test reward calculation directly"""
    print(f"\n🧮 Testing direct reward calculation for {post_id}...")

    try:
        result = db.fetch_or_calculate_reward(business_id, post_id, platform)
        print(f"📊 Reward calculation result: {result}")

        if result["status"] == "calculated":
            reward_value = result["reward"]
            print(f"🎯 Reward calculated successfully: {reward_value:.4f}")
            return True, reward_value
        else:
            print(f"❌ Reward calculation failed: {result}")
            return False, None

    except Exception as e:
        print(f"❌ Direct reward calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_baseline_calculation(platform, reward_value):
    """Test baseline calculation"""
    print(f"\n📊 Testing baseline calculation for {platform}...")

    try:
        baseline = db.update_and_get_baseline(platform, reward_value)
        print(f"📈 Baseline calculated: {baseline:.4f}")
        return True, baseline

    except Exception as e:
        print(f"❌ Baseline calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    print("🧪 DIRECT REWARD CALCULATION TEST")
    print("=" * 45)

    # Create test data
    business_id, post_id, platform = create_test_post_and_metrics()

    # Test reward calculation
    reward_success, reward_value = test_direct_reward_calculation(business_id, post_id, platform)

    # Test baseline calculation
    baseline_success, baseline = test_baseline_calculation(platform, reward_value) if reward_success else (False, None)

    print("\n" + "=" * 45)
    print("🎯 DIRECT TEST RESULTS")
    print("=" * 45)

    if reward_success and baseline_success:
        print("🎉 ALL DIRECT TESTS PASSED!")
        print(f"✅ Reward calculation: {reward_value:.4f}")
        print(f"✅ Baseline calculation: {baseline:.4f}")
    else:
        print("❌ SOME DIRECT TESTS FAILED")
        print(f"✅ Reward calculation: {'SUCCESS' if reward_success else 'FAILED'}")
        print(f"✅ Baseline calculation: {'SUCCESS' if baseline_success else 'FAILED'}")

    exit(0 if (reward_success and baseline_success) else 1)
