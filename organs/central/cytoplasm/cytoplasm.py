from organs.base_organ import BaseOrgan
from .logic_cytoplasm import CytoplasmLogic
from .view_cytoplasm import draw_cytoplasm

class Cytoplasm(BaseOrgan):
    def __init__(self, size=1.0):
        # Merkez organ olduğu için offset ve angle 0
        super().__init__(attachment_angle=0, offset_distance=0)
        self.logic = CytoplasmLogic(size)

    def draw(self, screen, parent):
        draw_cytoplasm(screen, parent.pos, parent.radius, parent.color)

    def grow(self):
        self.logic.grow()
