import pygame
import math
from organs.base_organ import BaseOrgan
from .logic_photoreceptor import PhotoreceptorLogic
from .view_photoreceptor import draw_photoreceptor, draw_vision_cone

class Photoreceptor(BaseOrgan):
    def __init__(self, attachment_angle=0, range=50, angle=0.75, base_hue=0.0):
        super().__init__(attachment_angle, offset_distance=0.8)
        self.logic = PhotoreceptorLogic(range, angle)
        self.base_hue = base_hue

    def draw(self, screen, parent):
        """Gözü ve görüş konisini bütünleşik olarak çizer."""
        # 1. Konumu ve açıları hesapla
        pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        outward_dir = (pos - parent.pos).normalize() if (pos - parent.pos).length() > 0 else parent.direction
        base_angle_rad = math.atan2(outward_dir.y, outward_dir.x)

        # 2. Görüş Konisini Çiz (Arka katman)
        draw_vision_cone(screen, pos, base_angle_rad, self.logic.angle,
                        self.logic.range, parent.color)

        # 3. Gözün Kendisini Çiz (Ön katman)
        draw_photoreceptor(screen, pos, self.logic.color_level, self.base_hue, parent.radius,
                          neon_level=self.logic.neon_level)

    def grow(self, upgrade_type='range'):
        self.logic.grow(upgrade_type)
