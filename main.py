from policy import select_action
from reward import compute_reward
from db_ops import insert_action, insert_reward, update_preference
from baseline import RewardBaseline

baseline_tracker = RewardBaseline()
LR = 0.05

# ---- CONTEXT (from runtime) ----
context = {
    "platform": "instagram",
    "time_bucket": "evening",
    "day_of_week": 4
}

topic = "AI marketing"
business_id = "YOUR_BUSINESS_UUID"

# ---- SELECT ACTION ----
action = select_action(context)

# ---- POST (LLM + image gen happens here) ----
post_id = "ig_123456"

# ---- SNAPSHOT METRICS (from DB/API) ----
metrics = {
    "saves": 2,
    "shares": 1,
    "comments": 2,
    "likes": 80,
    "followers": 1800
}

deleted = False
days = None

# ---- REWARD ----
reward = compute_reward(context["platform"], metrics, deleted, days)
baseline = baseline_tracker.update(reward)

# ---- DB WRITES ----
action_id = insert_action(post_id, context, action, topic, business_id)
insert_reward(action_id, reward, baseline, deleted, days)

delta = LR * (reward - baseline)

for dim, val in action.items():
    update_preference(context, dim, val, delta)

print("RL step complete.")
