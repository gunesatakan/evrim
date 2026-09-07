import game_settings
import math

class PhotoreceptorLogic:
    def __init__(self, range=None, angle=None):
        self.range = range if range is not None else game_settings.VISION_RANGE_BASE
        self.angle = angle if angle is not None else game_settings.VISION_ANGLE_BASE
        self._update_visual_levels()

    def _update_visual_levels(self):
        """Renk ve neon seviyelerini hesapla (scale'den etkilenmez)"""
        # Renk seviyesi: range'den (0.0=Kırmızı, 1.0=Mor)
        self.color_level = min(max(0, (self.range - 25) / 175.0), 1.0)
        # Neon seviyesi: angle'dan (0.0=Mat, 1.0=Neon)
        angle_deg = math.degrees(self.angle)
        self.neon_level = min(1.0, max(0.0, (angle_deg - 10) / 90.0))

    @property
    def base_energy_cost(self):
        """Taranan gorme alaniyla orantili."""
        return self.range * self.angle * game_settings.COST_PHOTORECEPTOR

    def update_stats(self, delta_range=0, delta_angle=0):
        self.range += delta_range
        self.angle += delta_angle
        self._update_visual_levels()

    def grow(self, type='range'):
        if type == 'range':
            self.range += game_settings.GROW_VISION_RANGE
        elif type == 'angle':
            self.angle += game_settings.GROW_VISION_ANGLE
        self._update_visual_levels()
