from supabase_client import supabase
from datetime import datetime

def insert_action(post_id, context, action, topic, business_id):
    res = supabase.table("rl_actions").insert({
        "post_id": post_id,
        "platform": context["platform"],
        "hook_type": action["hook_type"],
        "hook_length": action["hook_length"],
        "tone": action["tone"],
        "creativity": action["creativity"],
        "text_in_image": action["text_in_image"],
        "visual_style": action["visual_style"],
        "hook_length_pair": action["hook_length_pair"],
        "time_bucket": context["time_bucket"],
        "day_of_week": context["day_of_week"],
        "topic": topic,
        "business_id": business_id
    }).execute()

    return res.data[0]["id"]


def insert_reward(action_id, reward, baseline, deleted=False, days=None):
    supabase.table("rl_rewards").insert({
        "action_id": action_id,
        "reward_value": reward,
        "baseline": baseline,
        "deleted": deleted,
        "days_to_delete": days,
        "reward_window": "24h"
    }).execute()


def update_preference(ctx, dimension, value, delta):
    res = supabase.table("rl_preferences") \
        .select("id, preference_score, num_samples") \
        .eq("platform", ctx["platform"]) \
        .eq("time_bucket", ctx["time_bucket"]) \
        .eq("day_of_week", ctx["day_of_week"]) \
        .eq("dimension", dimension) \
        .eq("action_value", value) \
        .execute()

    if res.data:
        row = res.data[0]
        supabase.table("rl_preferences").update({
            "preference_score": row["preference_score"] + delta,
            "num_samples": row["num_samples"] + 1,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", row["id"]).execute()
    else:
        supabase.table("rl_preferences").insert({
            "platform": ctx["platform"],
            "time_bucket": ctx["time_bucket"],
            "day_of_week": ctx["day_of_week"],
            "dimension": dimension,
            "action_value": value,
            "preference_score": delta,
            "num_samples": 1
        }).execute()
