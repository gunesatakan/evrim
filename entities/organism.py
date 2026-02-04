import pygame
import random
import math
import game_settings
from entities.entity import Entity, SCALE
import interactions.reflexes
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor
from organs.receptors.Mechanoreceptor.mechanoreceptor import Mechanoreceptor
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.peripheral.membrane.membrane import Membrane
from organs.central.vacuole.vacuole import Vacuole
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from systems.protein_systems.short_protein_memory.direction_memory import DirectionMemorySystem
from systems.motor_control.motor_calibration import MotorCalibration
from systems.motor_control.smart_flagella_controller import SmartFlagellaController
from systems.motor_control.smart_motor_brain import SmartMotorBrain

class Organism(Entity):
    def __init__(self, index, x, y, color):
        super().__init__(x, y, 10, 0, color)
        self.index = index
        self.organs = []

        self.radius = 10
        self.speed = 0
        self.max_turn_rate = 0
        self.max_energy = 50
        self.energy = 50

        # Fizik tabanlı hareket değişkenleri
        self.thrust_direction = 0  # Net itme yönü (lokal koordinat)
        self.torque_turn_rate = 0  # Torktan kaynaklanan dönme hızı
        
        self.direction_memory = DirectionMemorySystem(capacity=10)
        self.motor_calibration = MotorCalibration()
        self.flagella_controller = SmartFlagellaController()
        self.motor_brain = SmartMotorBrain()  # Akıllı motor koordinasyonu

        # Optimal ön hesaplama sistemi
        # 360 derece taranarak en hızlı gidilebilecek yön bulunur
        self.optimal_front_angle = 0.0  # Lokal koordinatta (radyan)
        self.optimal_front_speed = 0.0  # Bu yönde elde edilebilecek maksimum hız
        self.natural_thrust_offset = 0.0  # Geriye uyumluluk için (optimal_front_angle ile aynı)
        self.wander_timer = 0
        self.target_direction = pygame.math.Vector2(self.direction)
        self.target_movement = None  # Hedef hareket yönü (fizik tabanlı)
        self.max_memory_length = 100 
        
        self.reflex_timer = 0
        self.reflex_direction = pygame.math.Vector2(0, 0)
        self.reflex_speed = 0

        self.shutdown = False
        self.log_enabled, self.log_timer = False, 0
        self.stuck_timer, self.stuck_check_interval = 0, 2.0
        self.last_stuck_pos = pygame.math.Vector2(x, y)
        self.current_trail_escape_vector, self.current_calm_escape_vector = None, None
        self.current_wall_avoid_vector = None  # Duvar kaçınma vektörü (turuncu)
        self.current_scent_intensity = 0.0  # Anlık koku yoğunluğu

    def add_organ(self, organ):
        self.organs.append(organ)
        if isinstance(organ, Membrane): self.membrane = organ
        if isinstance(organ, Cytoplasm): self.body = organ
        if isinstance(organ, Vacuole): self.vacuole = organ
        if isinstance(organ, Cytoskeleton): self.cytoskeleton = organ
        if organ.__class__.__name__ == "Ribosome": self.ribosome = organ

        # Cilia eklendiyse, tüm cilia yönlerini güncelle (koordineli teğet model)
        if isinstance(organ, Cilia):
            self._update_cilia_directions()

        # Motor organ eklendiyse, optimal önü yeniden hesapla
        if isinstance(organ, (Flagella, Cilia)):
            self._update_optimal_front()

        if hasattr(self, 'body'): self.recalculate_physics()

    def calculate_optimal_thrust_direction(self):
        """
        Cilia dağılım eksenine dik olan optimal itme yönünü hesaplar.
        Kürek teknesi mantığı: kürekler teknın yanlarında, itme ileri/geri.

        Returns:
            float: Optimal itme yönü (radyan)
        """
        cilia_organs = [o for o in self.organs if isinstance(o, Cilia)]
        if not cilia_organs:
            return math.pi  # Varsayılan: geri

        # Cilia pozisyonlarının vektörel toplamı
        sum_x, sum_y = 0.0, 0.0
        for cilia in cilia_organs:
            sum_x += math.cos(cilia.attachment_angle)
            sum_y += math.sin(cilia.attachment_angle)

        # Dağılım ekseni (cilia'ların ortalama yönü)
        if abs(sum_x) < 0.01 and abs(sum_y) < 0.01:
            # Simetrik dağılım - varsayılan eksen kullan
            axis_angle = 0
        else:
            axis_angle = math.atan2(sum_y, sum_x)

        # Optimal itme = eksene dik (saat yönünde 90°)
        optimal_direction = axis_angle + math.pi/2
        return optimal_direction

    def calculate_optimal_front(self):
        """
        360 dereceyi tarayarak en hızlı gidilebilecek yönü (optimal ön) hesapla.

        Her açı için:
        1. Flagella'ları o açıya max katkı sağlayacak şekilde deflection ayarla
        2. Cilia'ları o açı için optimal power distribution ayarla
        3. Net itme vektörünü hesapla
        4. Target açıya olan projeksiyonu bul

        Returns:
            tuple: (optimal_angle, max_speed) - Lokal koordinatta radyan ve hız birimi
        """
        best_angle = 0.0
        best_speed = 0.0

        # Motor organları topla
        flagellas = [o for o in self.organs if isinstance(o, Flagella)]
        cilias = [o for o in self.organs if isinstance(o, Cilia)]

        if not flagellas and not cilias:
            return 0.0, 0.0  # Motor organ yok

        # 360 dereceyi tara (1 derece hassasiyetle)
        for degree in range(360):
            target_angle = math.radians(degree)
            speed = self._simulate_thrust_for_angle(target_angle, flagellas, cilias)

            if speed > best_speed:
                best_speed = speed
                best_angle = target_angle

        return best_angle, best_speed

    def _simulate_thrust_for_angle(self, target_angle, flagellas, cilias):
        """
        Verilen açıya gitmek için tüm motorları optimal kullandığımızda
        elde edilecek hızı hesapla.

        Args:
            target_angle: Hedef hareket yönü (lokal koordinat, radyan)
            flagellas: Flagella organlarının listesi
            cilias: Cilia organlarının listesi

        Returns:
            float: Target yönünde elde edilecek hız (projeksiyon)
        """
        net_x, net_y = 0.0, 0.0

        # --- FLAGELLA HESABI ---
        for flagella in flagellas:
            # Flagella'nın temel özellikleri
            base_thrust_angle = flagella.attachment_angle  # Takılı olduğu noktadan dışa iter
            max_deflection = flagella.logic.max_deflection
            thrust_magnitude = flagella.logic.base_thrust  # Tam güçte

            # Hedef: Tepki kuvveti target_angle yönünde olmalı
            # Tepki = thrust + π, yani thrust = target_angle + π - π = target_angle
            # Ama aslında: reaction = thrust + π → thrust = reaction - π
            # Biz target_angle'a gitmek istiyoruz, yani reaction = target_angle olmalı
            # Bu durumda: thrust = target_angle - π (veya target_angle + π, aynı şey)
            desired_thrust = target_angle + math.pi

            # Base thrust'tan desired thrust'a gitmek için gereken deflection
            needed_deflection = desired_thrust - base_thrust_angle

            # Normalize et (-π, π) arasına
            while needed_deflection > math.pi:
                needed_deflection -= 2 * math.pi
            while needed_deflection < -math.pi:
                needed_deflection += 2 * math.pi

            # Max deflection sınırı içinde tut
            actual_deflection = max(-max_deflection, min(max_deflection, needed_deflection))
            actual_thrust = base_thrust_angle + actual_deflection

            # Tepki yönü (hareket yönü) = thrust + π
            reaction_angle = actual_thrust + math.pi

            # Net kuvvete katkı
            net_x += math.cos(reaction_angle) * thrust_magnitude
            net_y += math.sin(reaction_angle) * thrust_magnitude

        # --- CILIA HESABI ---
        # Cilia'lar için: Her cilia'nın target_angle'a katkısını hesapla
        # Koordineli çalışma: Dönüş yönündekiler güçlü, ters yöndekiler zayıf
        for cilia in cilias:
            # Cilia teğet yönde iter: attachment_angle + π/2 veya - π/2
            # Hangi teğet yönün target'a daha yakın olduğunu bul
            attachment = cilia.attachment_angle

            # İki olası teğet yön
            tangent_cw = attachment - math.pi/2   # Saat yönünde teğet
            tangent_ccw = attachment + math.pi/2  # Saat yönü tersine teğet

            # Her iki yönün reaction'ı (hareket yönü)
            reaction_cw = tangent_cw + math.pi
            reaction_ccw = tangent_ccw + math.pi

            # Hangisi target'a daha yakın?
            diff_cw = abs(self._normalize_angle(target_angle - reaction_cw))
            diff_ccw = abs(self._normalize_angle(target_angle - reaction_ccw))

            if diff_cw < diff_ccw:
                best_reaction = reaction_cw
                best_thrust = tangent_cw
            else:
                best_reaction = reaction_ccw
                best_thrust = tangent_ccw

            # Target yönüne katkı (cosine similarity)
            contribution = math.cos(self._normalize_angle(target_angle - best_reaction))

            # Katkıya göre güç ayarla (0.2 - 1.0 arası)
            if contribution > 0:
                power = 0.2 + 0.8 * contribution  # Pozitif katkı → güçlü
            else:
                power = 0.2  # Negatif katkı → minimum güç

            thrust_magnitude = cilia.logic.base_thrust_magnitude * power

            # Net kuvvete katkı
            net_x += math.cos(best_reaction) * thrust_magnitude
            net_y += math.sin(best_reaction) * thrust_magnitude

        # Net kuvvet vektörü
        net_magnitude = math.sqrt(net_x**2 + net_y**2)

        if net_magnitude < 0.001:
            return 0.0

        net_angle = math.atan2(net_y, net_x)

        # Target yönündeki projeksiyon (bu yönde elde edilecek hız)
        angle_diff = self._normalize_angle(target_angle - net_angle)
        projection = net_magnitude * math.cos(angle_diff)

        return max(0.0, projection)

    def _normalize_angle(self, angle):
        """Açıyı -π ile +π arasına normalize et."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def _update_optimal_front(self):
        """
        Optimal önü yeniden hesapla.
        Motor organlar değiştiğinde çağrılmalı.
        """
        self.optimal_front_angle, self.optimal_front_speed = self.calculate_optimal_front()
        # Geriye uyumluluk için natural_thrust_offset'i de güncelle
        self.natural_thrust_offset = self.optimal_front_angle

    def _update_cilia_directions(self):
        """
        Tüm cilia'ların optimal itme yönünü hesapla ve ayarla.
        Koordineli teğet model: Tüm cilia'lar aynı yöne iter.

        NOT: Fizik sistemi LOKAL koordinat kullanıyor (hücre yönüne göre).
        Bu yüzden global optimal yönü lokal koordinata çeviriyoruz.
        """
        optimal_dir_global = self.calculate_optimal_thrust_direction()

        # Global -> Lokal dönüşüm: hücre yönünü çıkar
        cell_heading = math.atan2(self.direction.y, self.direction.x)
        optimal_dir_local = optimal_dir_global - cell_heading

        for organ in self.organs:
            if isinstance(organ, Cilia):
                organ.set_optimal_direction(optimal_dir_local)

    def set_cilia_reverse(self, reverse=True):
        """
        Geri hareket için cilia yönlerini tersine çevir.

        Args:
            reverse: True ise geri git, False ise normal yön
        """
        optimal_dir_global = self.calculate_optimal_thrust_direction()
        if reverse:
            optimal_dir_global += math.pi  # 180° döndür

        # Global -> Lokal dönüşüm
        cell_heading = math.atan2(self.direction.y, self.direction.x)
        optimal_dir_local = optimal_dir_global - cell_heading

        for organ in self.organs:
            if isinstance(organ, Cilia):
                organ.set_optimal_direction(optimal_dir_local)

    def update_motor_deflection(self, deflection):
        """
        Tüm motor organların thrust açılarını ayarlar (eski metot, geriye uyumluluk).
        """
        self.update_cilia_deflection(deflection)

    def update_cilia_deflection(self, deflection):
        """
        Koordineli teğet modelde cilia kontrolü.
        Optimal yönün bir tarafındaki cilia'lar güçlü, diğer taraftakiler zayıf.
        Flagella'lar SmartFlagellaController tarafından yönetiliyor.
        """
        optimal_dir = self.calculate_optimal_thrust_direction()

        for organ in self.organs:
            # Sadece Cilia için (set_turn_control olan organlar)
            if hasattr(organ.logic, 'set_turn_control'):
                # Cilia'nın optimal yöne göre pozisyonu
                relative_angle = organ.attachment_angle - optimal_dir
                position_factor = math.sin(relative_angle)

                power_boost = 1.0 - (position_factor * deflection * 0.8)
                power_boost = max(0.2, min(1.8, power_boost))

                organ.logic.set_turn_control(power_boost)
                organ.logic.set_deflection(deflection * 0.3)

    def reset_motor_deflection(self):
        """Tüm motor organları temel konuma döndür"""
        self.reset_cilia_deflection()

    def reset_cilia_deflection(self):
        """Sadece Cilia'ları temel konuma döndür"""
        for organ in self.organs:
            if hasattr(organ.logic, 'set_turn_control'):
                if hasattr(organ.logic, 'reset_deflection'):
                    organ.logic.reset_deflection()
                if hasattr(organ.logic, 'set_turn_control'):
                    organ.logic.set_turn_control(1.0)

    def recalculate_physics(self):
        """
        Fizik tabanlı hareket hesabı.
        Her motor organın pozisyonu ve itme yönü dikkate alınır.
        Asimetrik yerleşim → tork → dönme
        """
        boost = self.membrane.logic.calcium_boost if hasattr(self, 'membrane') else 1.0

        # Net kuvvet ve tork hesabı
        net_force_x = 0.0
        net_force_y = 0.0
        net_torque = 0.0

        for organ in self.organs:
            if hasattr(organ.logic, 'thrust_magnitude'):
                # current_thrust_angle kullan (dinamik)
                thrust_angle = getattr(organ.logic, 'current_thrust_angle',
                                      getattr(organ.logic, 'thrust_angle', math.pi))

                # Organın pozisyonu (hücre merkezine göre, lokal koordinat)
                r_x = math.cos(organ.attachment_angle) * self.radius
                r_y = math.sin(organ.attachment_angle) * self.radius

                # İtme kuvveti vektörü (lokal koordinat)
                thrust_mag = organ.logic.thrust_magnitude * boost
                f_x = math.cos(thrust_angle) * thrust_mag
                f_y = math.sin(thrust_angle) * thrust_mag

                # Net kuvvete ekle
                net_force_x += f_x
                net_force_y += f_y

                # Tork hesabı: τ = r × F_tepki (2D cross product)
                # Tepki kuvveti = -F (thrust'ın tersi)
                # Pozitif tork = saat yönünün tersine (counterclockwise)
                # Negatif tork = saat yönünde (clockwise)
                torque = -(r_x * f_y - r_y * f_x)  # Negatif çünkü tepki kuvveti
                net_torque += torque

        # Hız: Net kuvvetin büyüklüğü
        # Motor organ varsa: hız tamamen fiziksel kuvvete bağlı (minimum 1.0 - sürüklenme)
        # Motor organ yoksa: varsayılan 5.0
        net_force_mag = math.sqrt(net_force_x**2 + net_force_y**2)
        has_motor_organs = any(hasattr(o.logic, 'thrust_magnitude') for o in self.organs)
        if has_motor_organs:
            self.speed = max(1.0, net_force_mag)  # Minimum 1.0 (çok düşük sürüklenme)
        else:
            self.speed = 5.0  # Motor organ yoksa varsayılan

        # Hareket yönü = kuvvet yönünün tersi (Newton'un 3. yasası: tepki kuvveti)
        # Flagella geriye iter → Hücre ileriye gider
        if net_force_mag > 0.01:
            force_angle = math.atan2(net_force_y, net_force_x)
            self.thrust_direction = force_angle + math.pi  # Tepki = ters yön
        else:
            self.thrust_direction = 0  # İleri

        # Dönme hızı: Tork / atalet momenti
        # Tek hücreli için düşük atalet - asimetrik yerleşim belirgin dönme yaratmalı
        # I = 0.2 × r² (sıvı ortamda küçük hücre için düşük atalet)
        moment_of_inertia = max(1.0, self.radius * self.radius * 0.2)
        self.torque_turn_rate = net_torque / moment_of_inertia

        # Maksimum dönüş hızı
        self.max_turn_rate = max(0.05, abs(self.torque_turn_rate) * 2)

        # Diğer fiziksel özellikler
        if hasattr(self, 'body'):
            self.radius = self.body.logic.radius
        if hasattr(self, 'vacuole'):
            self.max_energy = self.vacuole.logic.capacity

    @property
    def uid(self): return f"organism_{self.index}"
    @property
    def current_path_end(self): return self.pos + self.direction * self.speed * 2.0
    @property
    def move_regen(self): return self.membrane.logic.energy_regen if hasattr(self, 'membrane') else 1.0
    @property
    def memory(self):
        self.direction_memory.update()
        return self.direction_memory.memory_map

    @property
    def sound_radius(self):
        m = next((o for o in self.organs if isinstance(o, Mechanoreceptor)), None)
        return m.logic.sensitivity if m else 30
    @property
    def vision_range(self):
        p = next((o for o in self.organs if isinstance(o, Photoreceptor)), None)
        return p.logic.range if p else 25
    @property
    def vision_angle(self):
        p = next((o for o in self.organs if isinstance(o, Photoreceptor)), None)
        return p.logic.angle if p else 0.75
    @property
    def propulsion_power(self):
        boost = self.membrane.logic.calcium_boost if hasattr(self, 'membrane') else 1.0
        return (sum(o.logic.thrust_magnitude * 100 for o in self.organs if isinstance(o, Cilia)) or 10) * boost

    def draw(self, screen): 
        self.direction_memory.draw(screen, self.color)
        for organ in self.organs: organ.draw(screen, self)
        if self.current_trail_escape_vector:
            end = self.pos + self.current_trail_escape_vector
            pygame.draw.line(screen, (0, 255, 255), self.pos, end, 3)
            pygame.draw.circle(screen, (0, 255, 255), (int(end.x), int(end.y)), 4)
        if self.current_calm_escape_vector:
            end = self.pos + self.current_calm_escape_vector
            pygame.draw.line(screen, (255, 255, 255), self.pos, end, 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(end.x), int(end.y)), 4)
        if self.current_wall_avoid_vector:
            end = self.pos + self.current_wall_avoid_vector
            pygame.draw.line(screen, (255, 140, 0), self.pos, end, 2)  # Turuncu - duvar kaçınma
            pygame.draw.circle(screen, (255, 140, 0), (int(end.x), int(end.y)), 3)

        # Koku yoğunluğu yazısı
        if self.current_scent_intensity > 0:
            font = pygame.font.Font(None, 18)
            text = f"{self.current_scent_intensity:.2f}"
            text_surface = font.render(text, True, (200, 255, 200))
            text_pos = (int(self.pos.x + self.radius + 5), int(self.pos.y - 8))
            screen.blit(text_surface, text_pos)

    def check_collision(self, kaotropi): return self.pos.distance_to(kaotropi.pos) < (self.radius + kaotropi.radius)

    def can_see(self, target):
        to_t = target.pos - self.pos; dist = to_t.length()
        target_radius_angle = math.degrees(math.atan2(target.radius, dist)) if dist > 0 else 0
        for o in self.organs:
            if isinstance(o, Photoreceptor):
                organ_pos = o.get_absolute_position(self.pos, self.direction, self.radius)
                outward_dir = (organ_pos - self.pos).normalize() if (organ_pos - self.pos).length() > 0 else self.direction
                base_angle = math.degrees(math.atan2(outward_dir.y, outward_dir.x))
                target_angle = math.degrees(math.atan2(to_t.y, to_t.x))
                diff = abs(target_angle - base_angle)
                if diff > 180: diff = 360 - diff
                if dist <= o.logic.range + target.radius:
                    if diff <= (math.degrees(o.logic.angle)/2) + target_radius_angle: return True
        return False

    def can_hear(self, target): return self.pos.distance_to(target.pos) <= self.sound_radius + target.radius

    def calculate_organ_area(self):
        total = 0
        for o in self.organs:
            # Cytoplasm'ın kendi alanını (body) hesaplamaya dahil etmiyoruz çünkü o kabuk.
            if o == self.body: continue
            if hasattr(o.logic, 'area'): total += o.logic.area
            # Diğer organlar için şimdilik 5px varsayılan alan kabul edelim (Lego parçaları yer kaplar)
            else: total += 5.0 
        return total

    def consume_food(self, food):
        if hasattr(self, 'body'):
            organ_area = self.calculate_organ_area()
            return self.body.logic.add_food(food, organ_area)
        return False

    def _production_completed(self, food):
        self.energy = min(self.max_energy, self.energy + 1.0)
        possible_upgrades = []
        # Her organ kendi başına ihtimale dahil olur
        for organ in self.organs:
            if isinstance(organ, Flagella): possible_upgrades.append(('flagella', organ))
            elif isinstance(organ, Cilia): possible_upgrades.append(('cilia', organ))
            elif isinstance(organ, Photoreceptor): possible_upgrades.append(('vision_angle', organ)); possible_upgrades.append(('vision_range', organ))
            elif isinstance(organ, Mechanoreceptor): possible_upgrades.append(('sound_radius', organ))
            elif isinstance(organ, Chemoreceptor): possible_upgrades.append(('chemoreceptor', organ))
        if hasattr(self, 'body'): possible_upgrades.append('body_size'); possible_upgrades.append('digestion_speed')
        if hasattr(self, 'ribosome'): possible_upgrades.append('ribosome_speed')
        if hasattr(self, 'vacuole'): possible_upgrades.append('max_energy')
        if hasattr(self, 'membrane'): possible_upgrades.append('move_regen')
        possible_upgrades.append('memory_length')

        upgrade = random.choice(possible_upgrades)

        # Organ upgrade'leri tuple olarak gelir: (upgrade_type, organ)
        # Diğer upgrade'ler string olarak gelir
        if isinstance(upgrade, tuple):
            upgrade_type, organ = upgrade
            if upgrade_type == 'flagella': organ.grow()
            elif upgrade_type == 'cilia': organ.grow()
            elif upgrade_type == 'chemoreceptor': organ.grow()
            elif upgrade_type == 'vision_angle': organ.grow('angle')
            elif upgrade_type == 'vision_range': organ.grow('range')
            elif upgrade_type == 'sound_radius': organ.grow()
        elif upgrade == 'body_size': self.body.grow()
        elif upgrade == 'digestion_speed': self.body.logic.grow_enzyme(); self._log("[EVRIM] Sindirim hizi artti")
        elif upgrade == 'ribosome_speed': self.ribosome.grow(); self._log("[EVRIM] Ribozom üretim hızı arttı")
        elif upgrade == 'max_energy': self.vacuole.grow(); self._log("[EVRIM] Vakuol büyüdü")
        elif upgrade == 'move_regen': self.membrane.grow(); self._log("[EVRIM] ETC verimliliği arttı")
        elif upgrade == 'memory_length': self.direction_memory.capacity += game_settings.GROW_MEMORY; self._log("[EVRIM] Hafıza kapasitesi arttı")
        self.recalculate_physics()

    def sample_food_scent(self, foods):
        """
        Tüm kemoreseptörlerden koku örnekle.
        Sadece algılama yapar, takip mekanizması yok.

        Returns: (best_intensity, direction_to_best)
            - best_intensity: En yüksek algılanan yoğunluk
            - direction_to_best: Merkez → en yoğun pixel yönü (Vector2 veya None)
        """
        if not foods:
            return 0.0, None

        best_intensity = 0.0
        best_direction = None

        # Tum kemoreseptorlerin tum pixellerini tara
        for organ in self.organs:
            if isinstance(organ, Chemoreceptor):
                sample_points = organ._get_all_sample_points(self)

                for point in sample_points:
                    for food in foods:
                        dist = point.distance_to(food.pos)
                        if dist >= food.scent_radius:
                            continue

                        intensity = food.get_scent_intensity(point)

                        if intensity > 0 and organ.logic.can_smell_food(intensity):
                            if intensity > best_intensity:
                                best_intensity = intensity
                                to_point = point - self.pos
                                if to_point.length() > 0:
                                    best_direction = to_point.normalize()

        return best_intensity, best_direction

    def get_organ_stats(self):
        stats = []
        for o in self.organs:
            name = o.__class__.__name__
            if hasattr(o.logic, 'size'): stats.append(f"{name}(size:{o.logic.size:.2f})")
            elif hasattr(o.logic, 'length'): stats.append(f"{name}(len:{o.logic.length:.1f})")
            elif hasattr(o.logic, 'range'): stats.append(f"{name}(range:{o.logic.range:.1f})")
            elif name == "DigestionEnzymes": stats.append(f"Enzyme(time:{o.base_digestion_time:.1f}s)")
            elif name == "Ribosome": stats.append(f"Ribosome(time:{o.logic.base_production_time:.1f}s)")
            else: stats.append(name)
        
        # Sitoplazma içindeki enzimi ayrıca ekleyelim (çünkü o bir organ değil sistem)
        if hasattr(self, 'body') and hasattr(self.body.logic, 'enzyme'):
            stats.append(f"DigestionSpeed({self.body.logic.enzyme.base_digestion_time:.1f}s)")
            
        return ", ".join(stats)

    def _log(self, msg):
        if self.log_enabled: print(msg)

    def update(self, dt, kaotropis, foods=None, trail_manager=None, threat_uids=None):
        # 0. SİNDİRİM (DIGESTION) & ÜRETİM (PRODUCTION)
        if hasattr(self, 'body'):
            digested_food = self.body.logic.update(dt)
            if digested_food:
                if hasattr(self, 'ribosome'):
                    self.ribosome.logic.add_task(digested_food)
                else:
                    self._production_completed(digested_food)
        
        if hasattr(self, 'ribosome'):
            finished_product = self.ribosome.logic.update(dt)
            if finished_product:
                self._production_completed(finished_product)

        # 1. DUYU VERİSİ TOPLAMA
        nearby_threats = []
        for o in self.organs:
            if isinstance(o, Mechanoreceptor):
                heard = [k for k in kaotropis if o.is_hearing(self, k.pos, k.radius)]
                nearby_threats.extend(heard)
        
        # Gözler de eklenmeli
        for k in kaotropis:
            if self.can_see(k):
                nearby_threats.append(k)

        unique_threats = list({k.uid: k for k in nearby_threats}.values())

        # Koku örnekleme
        scent_intensity, scent_direction = self.sample_food_scent(foods) if foods else (0.0, None)
        self.current_scent_intensity = scent_intensity  # Çizim için sakla

        # Kalsiyum Seviyesi
        max_urgency = 1.0
        for o in self.organs:
            if isinstance(o, Mechanoreceptor):
                urgency = o.logic.check_urgency(unique_threats, self.pos)
                if urgency > max_urgency: max_urgency = urgency
        
        if hasattr(self, 'membrane'):
            self.membrane.update(dt, self, max_urgency)
            self.recalculate_physics()
        
        # Hafıza Güncelleme
        self.direction_memory.update()
        for k in kaotropis:
            if self.can_see(k):
                start = pygame.math.Vector2(k.pos); vec = pygame.math.Vector2(k.current_path_end) - start
                if vec.length() > 0:
                    trunc = vec.normalize() * min(vec.length(), self.max_memory_length)
                    self.direction_memory.encode(k.uid, (start, start + trunc))

        if trail_manager and threat_uids:
            chemos = [o for o in self.organs if isinstance(o, Chemoreceptor)]
            detected_points = [p for p in trail_manager.points if p.owner_uid in threat_uids and any(c.is_touching(self, p.pos, p.radius) and c.logic.can_detect(p.current_intensity) for c in chemos)]
            if detected_points:
                avg_dir, center_pos, total_int = pygame.math.Vector2(0,0), pygame.math.Vector2(0,0), 0
                for p in detected_points: avg_dir += p.direction * p.current_intensity; center_pos += p.pos * p.current_intensity; total_int += p.current_intensity
                if total_int > 0:
                    final_dir = avg_dir.normalize() if avg_dir.length() > 0 else pygame.math.Vector2(1,0)
                    self.direction_memory.encode("trail_prediction", (center_pos / total_int, (center_pos / total_int) + final_dir * 300))
            else: self.direction_memory.forget("trail_prediction")

        # 2. KARAR MEKANİZMASI (CYTOSKELETON)
        if hasattr(self, 'cytoskeleton'):
            # scent_direction: Kokunun yoğunlaştığı yön (None ise koku yok)
            self.cytoskeleton.update(dt, self, unique_threats, self.direction_memory, scent_direction)
        
        # 3. ENERJİ YÖNETİMİ
        if self.energy <= 0: self.energy, self.shutdown = 0, True
        if self.shutdown:
            self.energy += self.move_regen * dt
            if self.energy >= self.max_energy: self.energy, self.shutdown = self.max_energy, False
            return
        
        self.energy -= ((self.sound_radius / 100.0) + (self.vision_range * self.vision_angle / 1000.0) + (self.max_memory_length / 200.0)) * dt
        motor_cost = sum(o.logic.base_energy_cost for o in self.organs if hasattr(o.logic, 'base_energy_cost'))
        boost = self.membrane.logic.calcium_boost if hasattr(self, 'membrane') else 1.0
        self.energy -= (motor_cost * boost) * dt
        self.energy = min(self.max_energy, self.energy + self.move_regen * dt)

        self.log_timer -= dt
        if self.log_timer <= 0 and self.log_enabled:
            self.log_timer = 2.0
            self._log(f"\n--- ENERJI: {self.energy:.1f}/{self.max_energy:.1f} | Boost: x{boost:.1f}")

        # 4. FİZİKSEL HAREKET

        # Hedef hareketi belirle (target_movement veya target_direction'dan)
        movement_target = self.target_movement if self.target_movement else self.target_direction

        # Akıllı motor beynini kullan - organları koordine eder
        self.motor_brain.set_target(movement_target)
        self.motor_brain.update(self, dt)

        # DEBUG: Orange (index 3) için motor durumunu logla
        if getattr(self, 'debug_motor', False) and self.index == 3:
            if not hasattr(self, '_debug_timer'):
                self._debug_timer = 0
            self._debug_timer += dt
            if self._debug_timer >= 2.0:  # Her 2 saniyede bir
                self._debug_timer = 0
                self.motor_brain.debug_motor_state(self, f"Orange #{self.index}")

        # Motor organların açı/güç interpolasyonunu güncelle
        # NOT: Cytoskeleton farklı parametreler alır, onu atla
        for organ in self.organs:
            if isinstance(organ, (Flagella, Cilia)) and hasattr(organ, 'update'):
                organ.update(dt, self)

        # Fizik hesabını güncelle (güncel thrust açılarıyla)
        self.recalculate_physics()

        # Tork kaynaklı dönme - SADECE dönüş modunda uygula
        motor_mode = self.motor_brain.current_mode if hasattr(self, 'motor_brain') else "IDLE"

        if "TURN" in motor_mode or "CORRECT" in motor_mode:
            # Dönüş modunda: tork uygula
            if abs(self.torque_turn_rate) > 0.001:
                torque_rotation = math.degrees(self.torque_turn_rate * dt)
                self.direction = self.direction.rotate(torque_rotation)
                if self.direction.length() > 0:
                    self.direction = self.direction.normalize()

        # Hareket yönü = FİZİKTEN hesaplanan thrust yönü
        # Kürek fiziği: Cilia ön-arkada ise hücre YANA gider
        # thrust_direction: lokal koordinatta net itme yönünün tersi (hareket yönü)
        current_heading = math.atan2(self.direction.y, self.direction.x)
        actual_move_angle = current_heading + self.thrust_direction
        move_dir = pygame.math.Vector2(math.cos(actual_move_angle), math.sin(actual_move_angle))

        move_dist = self.speed * dt
        self.pos += move_dir * move_dist
        self.check_bounds()