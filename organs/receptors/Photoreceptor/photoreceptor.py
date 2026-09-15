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

    def isik_oku(self, parent, dt=None):
        """Gozun bulundugu noktada, baktigi yone gore isik olcumu.

        Doner: (gozun disa bakan ekseni, olcum). Isigin geldigi yon ortamin
        fizigidir (siddetin arttigi taraf); hucreye verilmez, yalnizca bu
        gozun ne kadar isik topladigini belirler.
        """
        from systems import isik
        konum = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        eksen = konum - parent.pos
        if eksen.length_squared() > 1e-12:
            eksen = eksen.normalize()
        else:
            eksen = parent.direction.rotate_rad(self.attachment_angle)
        siddet, gelis = isik.siddet_ve_yon(konum.x, konum.y)
        if siddet <= 0.0:
            return eksen, 0.0
        cos_teta = eksen.dot(gelis) if gelis.length_squared() > 1e-12 else 0.0
        return eksen, self.logic.olc(siddet, cos_teta, dt)
