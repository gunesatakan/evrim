from organs.base_organ import BaseOrgan
from .logic_vacuole import VacuoleLogic
from .view_vacuole import draw_vacuole

class Vacuole(BaseOrgan):
    def __init__(self, size=1.0):
        # Merkez organ, offset yok
        super().__init__(attachment_angle=0, offset_distance=0)
        self.logic = VacuoleLogic(size)

    def draw(self, screen, parent):
        draw_vacuole(screen, parent.pos, parent.radius, parent.direction, self.logic.area)

    def grow(self):
        self.logic.grow()
