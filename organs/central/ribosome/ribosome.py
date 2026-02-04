from organs.base_organ import BaseOrgan
from .logic_ribosome import RibosomeLogic
from .view_ribosome import draw_ribosome

class Ribosome(BaseOrgan):
    def __init__(self, production_speed=10.0):
        # Merkez organ, offset yok (sitoplazma içinde yüzer)
        super().__init__(attachment_angle=0, offset_distance=0)
        self.logic = RibosomeLogic(production_speed)

    def draw(self, screen, parent):
        draw_ribosome(screen, parent.pos, parent.radius, self.logic.is_busy)

    def grow(self):
        self.logic.grow()
