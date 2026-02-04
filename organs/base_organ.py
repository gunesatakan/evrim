import pygame
import math

class BaseOrgan:
    def __init__(self, attachment_angle=0, offset_distance=0.8):
        """
        Args:
            attachment_angle (float): Vücut merkezine göre takılma açısı (radyan). 0 = Ön.
            offset_distance (float): Vücut yarıçapına göre dışarıda olma oranı (0.0 - 1.0).
        """
        self.attachment_angle = attachment_angle
        self.offset_distance = offset_distance

    def get_absolute_position(self, parent_pos, parent_direction, parent_radius):
        """Organın dünyadaki tam koordinatını hesaplar."""
        # Ebeveynin baktığı ana açı
        parent_angle = math.atan2(parent_direction.y, parent_direction.x)
        # Organın vücut üzerindeki açısı
        total_angle = parent_angle + self.attachment_angle
        
        # Koordinat hesapla
        offset = pygame.math.Vector2(
            math.cos(total_angle), 
            math.sin(total_angle)
        ) * (parent_radius * self.offset_distance)
        
        return parent_pos + offset

    def draw(self, screen, parent):
        """Alt sınıflar tarafından override edilecek."""
        pass

    def update(self, dt, parent):
        """Alt sınıflar tarafından override edilecek."""
        pass
