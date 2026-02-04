import pygame
from organs.base_organ import BaseOrgan
from .danger_transmission.danger_transmission import DangerTransmission

class Cytoskeleton(BaseOrgan):
    def __init__(self):
        super().__init__(attachment_angle=0, offset_distance=0)
        self.logic = DangerTransmission()

    def update(self, dt, parent, nearby_threats, memory_system, scent_direction):
        """
        Sinyalleri işler ve parent'ın yönünü ve görsel vektörlerini günceller.

        scent_direction: Kokunun yoğunlaştığı yön (Vector2) veya None
        """
        new_dir, vec_type, vec_value = self.logic.process_signals(
            dt,
            parent,  # organism'i gönder (interoception için)
            nearby_threats,
            memory_system,
            scent_direction
        )
        
        # Kararı Organism'e uygula - HAREKET yönü
        if new_dir:
            # ESCAPE durumunda smoothing yapma - direkt takip et!
            if vec_type == 'ESCAPE':
                parent.target_movement = new_dir
            else:
                import math
                # Mevcut hareket yönü ile yeni hedef arasındaki açı farkını hesapla
                current_move = parent.target_movement if parent.target_movement else parent.direction
                cur_angle = math.atan2(current_move.y, current_move.x)
                new_angle = math.atan2(new_dir.y, new_dir.x)
                angle_diff = abs((new_angle - cur_angle + math.pi) % (2 * math.pi) - math.pi)

                # Eğer hedef çok arkadaysa (>120°), smoothing yapma
                if angle_diff > math.radians(120):
                    parent.target_movement = new_dir
                else:
                    # Normal durumda smooth geçiş
                    lerp_factor = 0.3
                    smoothed = current_move.lerp(new_dir, lerp_factor)
                    if smoothed.length() > 0:
                        parent.target_movement = smoothed.normalize()
                    else:
                        parent.target_movement = new_dir

        # Görselleştirme verilerini uygula
        parent.current_calm_escape_vector = None
        parent.current_trail_escape_vector = None
        parent.current_wall_avoid_vector = None

        if vec_type == 'ESCAPE':
            parent.current_calm_escape_vector = vec_value
        elif vec_type == 'TRAIL':
            parent.current_trail_escape_vector = vec_value
        elif vec_type == 'WALL_AVOID':
            parent.current_wall_avoid_vector = vec_value

    def draw(self, screen, parent):
        pass

    def grow(self):
        pass