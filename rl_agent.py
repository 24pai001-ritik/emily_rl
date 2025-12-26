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
    ctx_vec = build_context_vector(context)
    advantage = reward - baseline
 
    for dim, val in action.items():

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
        theta[(dim, val)] += lr_theta * advantage * ctx_vec

#---Computing Reward---


def compute_reward(
    platform: str,
    metrics: dict,
    deleted: bool = False,
    days_since_post: int | None = None
) -> float:
    """
    Platform-aware, normalized, bounded reward function
    """

    # -------------------------
    # 1️⃣ Platform-wise engagement
    # -------------------------

    if platform == "instagram":
        # Instagram values SAVES the most
        engagement = (
            3.0 * metrics.get("saves", 0) +
            2.0 * metrics.get("shares", 0) +
            1.0 * metrics.get("comments", 0) +
            0.3 * metrics.get("likes", 0)
        )

    elif platform == "x":
        # X values REPLIES the most
        engagement = (
            3.0 * metrics.get("replies", 0) +
            2.0 * metrics.get("retweets", 0) +
            1.0 * metrics.get("likes", 0)
        )

    elif platform == "linkedin":
        # LinkedIn values COMMENTS + SHARES
        engagement = (
            3.0 * metrics.get("comments", 0) +
            2.0 * metrics.get("shares", 0) +
            1.0 * metrics.get("likes", 0)
        )

    elif platform == "facebook":
        # Facebook values COMMENTS + SHARES
        engagement = (
            3.0 * metrics.get("comments", 0) +
            2.0 * metrics.get("shares", 0) +
            1.0 * metrics.get("reactions", 0)
        )

    else:
        raise ValueError(f"Unsupported platform: {platform}")

    followers = max(metrics.get("followers", 1), 1)

    # -------------------------
    # 2️⃣ Normalization + bounding
    # -------------------------

    raw_score = math.log(1 + engagement) / math.log(1 + followers)
    reward = math.tanh(raw_score)

    # -------------------------
    # 3️⃣ Delete penalty (human negative feedback)
    # -------------------------

    if deleted:
        # Early delete = strong negative signal
        if days_since_post is None:
            penalty = 0.7
        else:
            # exponential decay penalty
            penalty = 0.7 * math.exp(-days_since_post / 3.0)

        reward -= penalty

    return float(reward)