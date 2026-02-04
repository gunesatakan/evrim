import math
from systems.protein_systems.enzymes.digestion_enzymes.digestion_enzymes import DigestionEnzymes
import game_settings

class CytoplasmLogic:
    def __init__(self, size=1.0):
        self.size = size
        self.enzyme = DigestionEnzymes()
        self.food_queue = []
        self.FOOD_AREA = game_settings.FOOD_AREA 

    @property
    def radius(self):
        return self.size * 10 

    @property
    def total_area(self):
        return math.pi * (self.radius ** 2)

    @property
    def current_food_load(self):
        count = len(self.food_queue)
        if self.enzyme.current_food:
            count += 1
        return count * self.FOOD_AREA

    def can_fit_food(self, total_organ_area):
        return (self.current_food_load + total_organ_area + self.FOOD_AREA) <= self.total_area

    def add_food(self, food, total_organ_area):
        if self.can_fit_food(total_organ_area):
            self.food_queue.append(food)
            return True
        return False

    def update(self, dt):
        return self.enzyme.process(dt, self.food_queue)

    def grow_enzyme(self):
        self.enzyme.grow()

    def update_stats(self, delta_size=0):
        self.size += delta_size

    def grow(self):
        self.size += game_settings.GROW_BODY