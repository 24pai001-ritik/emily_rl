# rl_agent.py
import math
import random
import numpy as np
import db
from collections import defaultdict

# ---------------- ACTION SPACE ----------------

ACTION_SPACE = {
    "HOOK_TYPE": [
        "question hook",
        "bold claim hook",
        "relatable pain hook",
        "trendy topic hook",
        "curiosity gap hook"
    ],
    "LENGTH": ["short", "medium"],
    "TONE": ["casual", "formal", "humourous", "educational"],
    "CREATIVITY": ["safe", "balanced", "experimental"],
    "TEXT_IN_IMAGE": ["text in image", "no text in image"],
    "VISUAL_STYLE": ["abstract", "human figure"]
}

# ---------------- THETA STORE ----------------
# theta per (dimension, value)
EMBEDDING_DIM = 768  # 384 business + 384 topic

theta = defaultdict(lambda: np.zeros(EMBEDDING_DIM, dtype=np.float32))


# ---------------- UTILS ----------------

def softmax(scores):
    max_s = max(scores)
    exp = [math.exp(s - max_s) for s in scores]
    total = sum(exp)
    return [e / total for e in exp]


def build_context_vector(context):
    """
    Continuous context for generalization
    """
    return np.concatenate([
        context["business_embedding"],
        context["topic_embedding"]
    ])


# ---------------- ACTION SELECTION ----------------

def select_action(context):
    """
    context = {
      platform,
      time_bucket,
      day_of_week,
      business_embedding (384),
      topic_embedding (384)
    }
    """

    ctx_vec = build_context_vector(context)

    action = {}

    for dim, values in ACTION_SPACE.items():

        scores = []
        for v in values:
            # discrete preference
            H = db.get_preference(
                context["platform"],
                context["time_bucket"],
                context["day_of_week"],
                dim,
                v
            )

            # continuous contribution
            score = H + np.dot(theta[(dim, v)], ctx_vec)
            scores.append(score)

        probs = softmax(scores)
        action[dim] = random.choices(values, probs)[0]

    return action, ctx_vec


# ---------------- LEARNING UPDATE ----------------

def update_rl(context, action, ctx_vec, reward, baseline,
              lr_discrete=0.05, lr_theta=0.01):
    print(f"🧠 Updating RL: reward={reward:.4f}, baseline={baseline:.4f}, advantage={reward - baseline:.4f}")
    ctx_vec = build_context_vector(context)
    advantage = reward - baseline

    for dim, val in action.items():
        print(f"   🎯 Updating action dimension: {dim}={val}")

        # 1️⃣ Discrete update (Supabase)
        db.update_preference(
            context["platform"],
            context["time_bucket"],
            context["day_of_week"],
            dim,
            val,
            lr_discrete * advantage
        )

        # 2️⃣ Continuous update (theta)
        theta_update = lr_theta * advantage * ctx_vec
        theta[(dim, val)] += theta_update
        print(f"   📈 Theta update magnitude: {np.linalg.norm(theta_update):.6f}")

<<<<<<< HEAD
=======
#---Computing Reward---
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5

