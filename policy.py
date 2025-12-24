import math
import random
from action_space import ACTION_SPACE
from supabase_client import supabase

def get_pref_score(ctx, dimension, value):
    res = supabase.table("rl_preferences") \
        .select("preference_score") \
        .eq("platform", ctx["platform"]) \
        .eq("time_bucket", ctx["time_bucket"]) \
        .eq("day_of_week", ctx["day_of_week"]) \
        .eq("dimension", dimension) \
        .eq("action_value", value) \
        .execute()

    if res.data:
        return res.data[0]["preference_score"]
    return 0.0


def softmax_select(ctx, dimension, values, temperature=1.0):
    scores = []
    for v in values:
        scores.append(get_pref_score(ctx, dimension, v) / temperature)

    max_s = max(scores)
    exp_scores = [math.exp(s - max_s) for s in scores]
    probs = [e / sum(exp_scores) for e in exp_scores]

    return random.choices(values, weights=probs, k=1)[0]


def select_action(context):
    action = {}
    for dim, values in ACTION_SPACE.items():
        action[dim] = softmax_select(context, dim, values)

    action["hook_length_pair"] = f"{action['hook_type']}_{action['hook_length']}"
    return action
