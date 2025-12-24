import math
import numpy as np

def delete_penalty(days, gamma_max=0.7, tau=3):
    return gamma_max * math.exp(-days / tau)

def compute_reward(platform, metrics, deleted=False, days_since_post=None):

    if platform == "instagram":
        engagement = (
            3*metrics["saves"] +
            2*metrics["shares"] +
            metrics["comments"] +
            0.3*metrics["likes"]
        )
        followers = metrics["followers"]

    elif platform == "x":
        engagement = (
            3*metrics["replies"] +
            2*metrics["retweets"] +
            metrics["likes"]
        )
        followers = metrics["followers"]

    elif platform == "facebook":
        engagement = (
            2*metrics["shares"] +
            3*metrics["comments"] +
            metrics["reactions"]
        )
        followers = metrics["followers"]

    elif platform == "linkedin":
        engagement = (
            3*metrics["comments"] +
            2*metrics["shares"] +
            metrics["likes"]
        )
        followers = metrics["followers"]

    raw = np.log(1 + engagement) / np.log(1 + followers)
    reward = math.tanh(raw)

    if deleted:
        reward -= delete_penalty(days_since_post or 0)

    return reward
