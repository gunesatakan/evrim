import game_settings

class RibosomeLogic:
    def __init__(self, production_speed=None):
        self.base_production_time = production_speed if production_speed else game_settings.RIBOSOME_TIME
        self.area = game_settings.RIBOSOME_AREA
        self.current_task = None
        self.production_timer = 0.0
        self.queue = []

    @property
    def base_energy_cost(self):
        """Uretim hizi = ribozom sayisi; maliyet 1/sure ile orantili."""
        return game_settings.COST_RIBOSOME / max(0.001, self.base_production_time)

    def add_task(self, resource):
        self.queue.append(resource)

    def grow(self):
        self.base_production_time = max(1.0, self.base_production_time - game_settings.GROW_RIBOSOME)

    def update(self, dt):
        if self.current_task is None and self.queue:
            self.current_task = self.queue.pop(0)
            self.production_timer = 0.0
        if self.current_task:
            self.production_timer += dt
            if self.production_timer >= self.base_production_time:
                finished_product = self.current_task
                self.current_task = None
                self.production_timer = 0.0
                return finished_product
        return None

    @property
    def is_busy(self):
        return self.current_task is not None