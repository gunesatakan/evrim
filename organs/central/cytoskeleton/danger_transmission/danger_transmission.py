import pygame
import random
from .move_direction import MoveDirection
import game_settings
from systems.signaling.behavioral_state import BehavioralState
from entities.entity import WIDTH, HEIGHT
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor

class DangerTransmission:
    def __init__(self):
        self.area = game_settings.CYTOSKELETON_AREA # Kapladığı alan
        self.target_direction = pygame.math.Vector2(1, 0)
        self.wander_timer = 0

        # Kaçış yönü kilidi - oscillasyonu önlemek için
        self.escape_lock_timer = 0
        self.locked_escape_dir = None

        # Davranış durumu sistemi (interoception)
        self.behavioral_state = BehavioralState()

    def process_signals(self, dt, organism, nearby_threats, memory_system, scent_direction):
        """
        Sinyalleri işler ve hareket yönünü belirler.
        BehavioralState sistemini kullanarak iç duruma göre karar verir.

        Args:
            scent_direction: Kokunun yoğunlaştığı yön (Vector2) veya None

        Geriye (new_direction, vector_type, vector_value) döner.
        vector_type: 'ESCAPE', 'TRAIL', 'HUNT' veya None
        """
        self_pos = organism.pos

        # Escape lock timer'ı güncelle
        if self.escape_lock_timer > 0:
            self.escape_lock_timer -= dt

        # Davranış durumunu değerlendir (interoception)
        state = self.behavioral_state.evaluate(organism, nearby_threats, scent_direction)

        # 1. THREATENED - Tehdit varsa kaç
        if self.behavioral_state.should_flee():
            # En yakın tehdidi bul
            closest_threat = min(nearby_threats, key=lambda k: self_pos.distance_to(k.pos))

            # Eğer kaçış yönü kilitliyse, onu kullan
            if self.escape_lock_timer > 0 and self.locked_escape_dir:
                self.target_direction = self.locked_escape_dir
            else:
                # Yeni kaçış yönü hesapla ve kilitle
                mem_data = memory_system.retrieve(closest_threat.uid)
                escape_dir = MoveDirection.calculate_threat_escape(self_pos, closest_threat, mem_data)
                self.target_direction = escape_dir
                self.locked_escape_dir = escape_dir
                self.escape_lock_timer = 0.5  # 0.5 saniye kilitle

            return (self.target_direction, 'ESCAPE', self.target_direction * 40)

        # Tehdit yok, kaçış kilidini sıfırla
        self.locked_escape_dir = None
        self.escape_lock_timer = 0

        # 2. KOKU İZİNDEN KAÇINMA (tehdit olmasa bile iz varsa kaçın)
        trail_mem = memory_system.retrieve("trail_prediction")
        if trail_mem:
            avoid_dir = MoveDirection.calculate_trail_avoid(self_pos, trail_mem)
            if avoid_dir and avoid_dir.length() > 0:
                self.target_direction = avoid_dir
                return (self.target_direction, 'TRAIL', avoid_dir * 50)

        # 3. WALL_AVOID - Duvar görünüyorsa kaçın
        wall_data = self._detect_wall_in_vision(organism)
        if wall_data:
            avoid_dir = MoveDirection.calculate_wall_avoidance(self_pos, wall_data)
            if avoid_dir and avoid_dir.length() > 0:
                self.target_direction = avoid_dir
                return (self.target_direction, 'WALL_AVOID', avoid_dir * 25)

        # 4. FULL veya IDLE - Rastgele dolaş
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.target_direction = self.target_direction.rotate(random.uniform(-45, 45)).normalize()
            self.wander_timer = random.uniform(0.5, 2.0)

        return (self.target_direction, None, None)

    def _detect_wall_in_vision(self, organism):
        """
        Organizmanın görme alanında duvar olup olmadığını kontrol eder.
        Photoreceptor'ün görme mesafesini kullanır.

        Returns:
            dict: {'walls': [...], 'distances': {...}} veya None
        """
        # Görme mesafesini bul (en uzun menzilli Photoreceptor)
        vision_range = 0
        for organ in organism.organs:
            if isinstance(organ, Photoreceptor):
                if organ.logic.range > vision_range:
                    vision_range = organ.logic.range

        if vision_range == 0:
            return None

        pos = organism.pos
        walls = []
        distances = {}

        # Sol duvar kontrolü
        if pos.x < vision_range:
            walls.append('left')
            distances['left'] = pos.x

        # Sağ duvar kontrolü
        if pos.x > WIDTH - vision_range:
            walls.append('right')
            distances['right'] = WIDTH - pos.x

        # Üst duvar kontrolü
        if pos.y < vision_range:
            walls.append('top')
            distances['top'] = pos.y

        # Alt duvar kontrolü
        if pos.y > HEIGHT - vision_range:
            walls.append('bottom')
            distances['bottom'] = HEIGHT - pos.y

        if walls:
            return {'walls': walls, 'distances': distances}

        return None