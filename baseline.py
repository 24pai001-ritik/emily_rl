class RewardBaseline:
    def __init__(self, alpha=0.1):
        self.value = 0.0
        self.alpha = alpha

    def update(self, reward):
        self.value = (1 - self.alpha)*self.value + self.alpha*reward
        return self.value
