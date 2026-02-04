from organs.base_organ import BaseOrgan
from .logic_mechanoreceptor import MechanoreceptorLogic
from .view_mechanoreceptor import draw_mechanoreceptor_sausage

class Mechanoreceptor(BaseOrgan):
    def __init__(self, attachment_angle=0, size=1.0):
        super().__init__(attachment_angle, offset_distance=1.0)
        self.logic = MechanoreceptorLogic(size)

    def draw(self, screen, parent):
        # Sosis çizimi
        draw_mechanoreceptor_sausage(
            screen, 
            parent.pos, 
            parent.radius, 
            self.attachment_angle, 
            parent.direction,
            self.logic.size
        )

    def grow(self):
        self.logic.grow()

    def is_hearing(self, parent, target_pos, target_radius=0):
        """Bu kulak (kendi konumundan) hedefi duyuyor mu?"""
        my_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        dist = my_pos.distance_to(target_pos)
        # Hedefin kenarı duyma alanına girdi mi?
        # target_radius dahil: Düşmanın kenarı ses alanına girdiğinde algıla
        return dist <= self.logic.sensitivity + target_radius