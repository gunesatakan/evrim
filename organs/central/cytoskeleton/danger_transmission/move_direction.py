import pygame
import interactions.reflexes
import interactions.escapes
import interactions.reactions

class MoveDirection:
    @staticmethod
    def calculate_threat_escape(self_pos, threat, memory_data=None):
        """
        Tehditten kaçış yönünü belirler.
        Memory varsa: Rotaya DIK kaçış (Bilinçli).
        Memory yoksa: Konuma ZIT kaçış (İlkel).
        """
        if memory_data:
            p1, p2 = memory_data
            route_vec = p2 - p1
            # Eğer rota vektörü çok kısaysa (henüz hareket etmediyse) yine de zıt kaç
            if route_vec.length() < 1.0: 
                return interactions.reflexes.get_auditory_reflex_direction(self_pos, threat.pos)
            
            route_dir = route_vec.normalize()
            perp1 = pygame.math.Vector2(-route_dir.y, route_dir.x)
            perp2 = pygame.math.Vector2(route_dir.y, -route_dir.x)
            
            # Tehdit rotasına göre hangi taraftayız?
            # Referans noktası olarak tehdidin o anki konumu (threat.pos) daha güvenli
            to_self = self_pos - threat.pos
            if to_self.dot(perp1) > to_self.dot(perp2):
                return perp1
            else:
                return perp2
        else:
            # Hafıza yok -> ZIT YÖNE KAÇ
            return interactions.reflexes.get_auditory_reflex_direction(self_pos, threat.pos)

    @staticmethod
    def calculate_trail_avoid(self_pos, trail_memory):
        start, end = trail_memory
        return interactions.escapes.get_trail_escape_direction(start, end)

    @staticmethod
    def calculate_food_approach(self_pos, food):
        to_food = food.pos - self_pos
        if to_food.length() > 0:
            return to_food.normalize()
        return pygame.math.Vector2(0, 0)

    @staticmethod
    def calculate_wall_avoidance(self_pos, wall_data):
        """
        Duvar kaçınma yönünü hesaplar.
        Tehdit değil, sadece mantıksız bir yön olarak işaretler.
        """
        return interactions.reactions.get_wall_avoidance_direction(self_pos, wall_data)