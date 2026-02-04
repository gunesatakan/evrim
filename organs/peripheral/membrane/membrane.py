from organs.base_organ import BaseOrgan
from .logic_membrane import MembraneLogic
from .view_membrane import draw_calcium_aura

class Membrane(BaseOrgan):
    def __init__(self):
        super().__init__(attachment_angle=0, offset_distance=0)
        self.logic = MembraneLogic()

    def update(self, dt, parent, urgency_signal):
        # Sinyali doğrudan uygula
        self.logic.set_calcium_signal(urgency_signal)

    def draw(self, screen, parent):
        draw_calcium_aura(screen, parent.pos, parent.radius, self.logic.calcium_boost)

    def grow(self):
        self.logic.grow_etc()
