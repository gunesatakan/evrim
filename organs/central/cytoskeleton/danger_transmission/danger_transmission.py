import pygame
import random
import math
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

        # Temporal chemotaxis
        # last_perception: bir ÖNCEKİ algı penceresinin ortalaması.
        # None = henüz karşılaştırılacak pencere yok (ilk delta 0 olmalı).
        self.last_perception = None
        self.last_delta = 0.0
        self.base_tumble_rate = getattr(game_settings, 'BASE_TUMBLE_RATE', 1.0)
        self.tumble_rate = self.base_tumble_rate

        # Algı penceresi: kare başına (1/60 sn) ölçülen fark, canlı o sürede
        # neredeyse hiç yer değiştirmediği için sıfıra yakın çıkar ve
        # tumble_rate hiç modüle olmaz. Bu yüzden algı bir pencere boyunca
        # biriktirilip pencere ortalamaları karşılaştırılır.
        self.sample_interval = getattr(game_settings, 'CHEMO_SAMPLE_INTERVAL', 0.5)
        self._sample_accum = 0.0
        self._sample_time = 0.0

        # Levy flight (IDLE)
        self.levy_run_duration = 0.0
        self.levy_timer = 0.0

    def process_signals(self, dt, organism, nearby_threats, memory_system, scent_intensity, prey_dir=None, behavior_response='ignore'):
        """
        Sinyalleri işler ve hareket yönünü belirler.
        BehavioralState sistemini kullanarak iç duruma göre karar verir.

        Args:
            scent_intensity: Skalar koku yoğunluğu (float)

        Geriye (new_direction, vector_type, vector_value) döner.
        vector_type: 'ESCAPE', 'TRAIL', 'HUNT' veya None
        """
        self_pos = organism.pos

        # Escape lock timer'ı güncelle
        if self.escape_lock_timer > 0:
            self.escape_lock_timer -= dt

        # Davranış durumunu değerlendir (interoception)
        state = self.behavioral_state.evaluate(organism, nearby_threats, scent_intensity > 0)

        # 1. THREATENED - Tehdit varsa kaç.
        # Davranış genomu açıkken kaçma kararı ARTIK TABLODAN gelir; sabit
        # "tehdit gördün, kaç" refleksi yalnızca tablo susarsa devreye girer.
        genome_drives = (getattr(game_settings, 'BEHAVIOR_ENABLED', False)
                         and behavior_response in ('flee', 'approach', 'attack')
                         and prey_dir is not None)
        if not genome_drives and self.behavioral_state.should_flee():
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

            self._reset_chemotaxis_sampling()
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
                self._reset_chemotaxis_sampling()
                return (self.target_direction, 'TRAIL', avoid_dir * 50)

        # 3. WALL_AVOID - Duvar görünüyorsa kaçın
        wall_data = self._detect_wall_in_vision(organism)
        if wall_data:
            avoid_dir = MoveDirection.calculate_wall_avoidance(self_pos, wall_data)
            if avoid_dir and avoid_dir.length() > 0:
                self.target_direction = avoid_dir
                self._reset_chemotaxis_sampling()
                return (self.target_direction, 'WALL_AVOID', avoid_dir * 25)

        # 3.5 AVLANMA - görüş alanındaki avı doğrudan takip et.
        # Tehdit / iz / duvardan SONRA gelir: kaçmak ve sıkışmamak önceliklidir.
        # Ava görüşle kilitlenmek kokudan önce gelir; koku zaten avın yaydığı
        # izi takip ederek hücreyi buraya kadar getirmiştir.
        if prey_dir is not None and getattr(game_settings, 'PREY_VISION_PRIORITY', 1):
            self.target_direction = prey_dir
            self._reset_chemotaxis_sampling()
            # Görselleştirme tepkiye göre: kaçış / yaklaşma / saldırı
            vec_type = {'flee': 'ESCAPE', 'attack': 'HUNT',
                        'approach': 'HUNT'}.get(behavior_response, 'HUNT')
            return (self.target_direction, vec_type, prey_dir * 45)

        # 4. CHEMOTAXIS veya IDLE
        if scent_intensity > 0:
            # --- RUN-AND-TUMBLE (pencereli zamansal örnekleme) ---
            # Algıyı pencere boyunca biriktir; tumble_rate yalnızca pencere
            # dolduğunda güncellenir ve aralarda korunur (hücrenin iç durumu).
            self._sample_accum += scent_intensity * dt
            self._sample_time += dt

            if self._sample_time >= self.sample_interval:
                window_mean = self._sample_accum / self._sample_time
                if self.last_perception is None:
                    delta = 0.0          # ilk pencere: karşılaştıracak şey yok
                else:
                    delta = window_mean - self.last_perception
                self.last_perception = window_mean
                self.last_delta = delta
                self._sample_accum = 0.0
                self._sample_time = 0.0

                gain_pos = getattr(game_settings, 'TUMBLE_GAIN_POSITIVE', 5.0)
                gain_neg = getattr(game_settings, 'TUMBLE_GAIN_NEGATIVE', 2.0)
                rate_min = getattr(game_settings, 'TUMBLE_RATE_MIN', 0.05)
                rate_max = getattr(game_settings, 'TUMBLE_RATE_MAX', 10.0)

                if delta > 0:
                    self.tumble_rate = self.base_tumble_rate * math.exp(-gain_pos * delta)
                else:
                    self.tumble_rate = self.base_tumble_rate * math.exp(-gain_neg * delta)

                self.tumble_rate = max(rate_min, min(rate_max, self.tumble_rate))

            tumble_prob = 1.0 - math.exp(-self.tumble_rate * dt)

            if random.random() < tumble_prob:
                # TUMBLE: rastgele yeni yön
                angle = random.uniform(-180, 180)
                self.target_direction = self.target_direction.rotate(angle)
                if self.target_direction.length() > 0:
                    self.target_direction = self.target_direction.normalize()

            return (self.target_direction, None, None)
        else:
            # --- LEVY FLIGHT ---
            self._reset_chemotaxis_sampling()
            self.levy_timer += dt

            if self.levy_timer >= self.levy_run_duration:
                alpha = getattr(game_settings, 'LEVY_ALPHA', 1.5)
                min_step = getattr(game_settings, 'LEVY_MIN_STEP', 0.5)
                max_dur = getattr(game_settings, 'LEVY_MAX_DURATION', 10.0)
                u = max(0.001, random.random())
                self.levy_run_duration = min(min_step / (u ** (1.0 / (alpha - 1))), max_dur)
                self.levy_timer = 0.0
                angle = random.uniform(-180, 180)
                self.target_direction = self.target_direction.rotate(angle)
                if self.target_direction.length() > 0:
                    self.target_direction = self.target_direction.normalize()

            return (self.target_direction, None, None)

    def _reset_chemotaxis_sampling(self):
        """Algı penceresini sıfırla.

        Kaçış / iz / duvar dallarına sapıldığında pencere yarıda kalır.
        Eski ortalamayı saklamak, kemotaksiye dönüşte saniyeler öncesine
        göre sahte bir sıçrama üretip yanlış bir RUN/TUMBLE kararı verdirir.
        """
        self.last_perception = None
        self.last_delta = 0.0
        self._sample_accum = 0.0
        self._sample_time = 0.0
        self.tumble_rate = self.base_tumble_rate

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