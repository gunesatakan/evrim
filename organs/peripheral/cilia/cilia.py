import math
import pygame
from organs.peripheral.base_motor import BaseMotorOrgan
from .logic_cilia import CiliaLogic
from .view_cilia import draw_cilia


class Cilia(BaseMotorOrgan):
    def __init__(self, attachment_angle=0, length=10.0, base_direction=None):
        """
        attachment_angle: Hücre zarında pozisyon (radyan)
        length: Cilia uzunluğu
        base_direction: Temel itme yönü (hücre lokal koordinatı, radyan)
                        None = π (geriye iter → organizma ileri gider)
                        Kürek mantığı: Nerede olursa olsun, suyu geriye iterek
                        gemiyi ileri götürür.
        """
        super().__init__(attachment_angle, offset_distance=1.0)

        # Teğet itme: Cilia bulunduğu noktadan TEĞET yönde iter
        # Bu, kürek takımı gibi çalışır - yan taraftaki kürekler suyu geriye iter
        # optimal_front_angle bu sayede doğru hesaplanır
        if base_direction is None:
            base_direction = attachment_angle + math.pi/2  # Teğet yön

        # Senkronize kürek: Tüm cilia'lar AYNI FAZDA çalışır
        # Kürek takımı gibi - hep birlikte çek, hep birlikte geri dön
        phase_offset = 0.0

        self.logic = CiliaLogic(length, base_direction, phase_offset=phase_offset)

    def get_thrust_direction(self):
        """
        Cilia'nın itme yönünü döndür.

        Cilia teğet yönde iter: attachment_angle + π/2
        current_thrust_angle stroke fazı dahil anlık yönü verir.
        """
        return self.logic.current_thrust_angle

    def set_optimal_direction(self, direction):
        """
        Organizma tarafından çağrılır - optimal itme yönünü ayarla.
        Koordineli teğet modelde tüm cilia'lar aynı yöne iter.
        """
        self.logic.set_base_direction(direction)

    def update(self, dt, parent):
        """Her frame çağrılır - vuruş döngüsünü günceller"""
        self.logic.update(dt)

    def draw(self, screen, parent):
        pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        outward_dir = (pos - parent.pos).normalize() if (pos - parent.pos).length() > 0 else parent.direction
        calcium_boost = parent.membrane.logic.calcium_boost if hasattr(parent, 'membrane') else 1.0

        # Vuruş fazına göre görsel ofset
        stroke_offset = self.logic.get_stroke_visual_offset()
        power_boost = self.logic.power_boost  # Pozisyon bazlı güç
        stroke_phase = self.logic.stroke_phase  # Animasyon fazı

        # İtme yönünü global koordinata çevir
        # current_thrust_angle lokal koordinatta, parent.direction'a göre döndür
        parent_heading = math.atan2(parent.direction.y, parent.direction.x)
        global_thrust_angle = parent_heading + self.logic.current_thrust_angle
        thrust_dir = pygame.math.Vector2(math.cos(global_thrust_angle), math.sin(global_thrust_angle))

        # Keskin dönüşte düşük güçlü taraf TERSİNE kürek çeker (görsel)
        # power_boost < 0.7: Dönüş yönünün tersi → kürek İLERİYE gider
        # power_boost > 0.7: Normal → kürek GERİYE gider
        reverse_stroke = power_boost < 0.7

        draw_cilia(screen, pos, outward_dir, self.logic.length, parent.color,
                   parent.shutdown, calcium_boost, stroke_offset,
                   self.logic.is_power_stroke, power_boost, stroke_phase,
                   self.logic.extension, thrust_dir, reverse_stroke)

    def grow(self):
        self.logic.grow()
