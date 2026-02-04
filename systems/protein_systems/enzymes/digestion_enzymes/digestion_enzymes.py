import game_settings

class DigestionEnzymes:
    def __init__(self, efficiency=1.0):
        self.efficiency = efficiency
        self.base_digestion_time = game_settings.DIGESTION_TIME
        self.current_food = None
        self.progress = 0.0

    def grow(self):
        self.base_digestion_time = max(1.0, self.base_digestion_time - game_settings.GROW_DIGESTION)

    def process(self, dt, food_queue):
        if self.current_food is None and food_queue:
            self.current_food = food_queue.pop(0)
            self.progress = 0.0
        if self.current_food:
            self.progress += dt * self.efficiency
            if self.progress >= self.base_digestion_time:
                digested_item = self.current_food
                self.current_food = None
                self.progress = 0.0
                return digested_item
        return None