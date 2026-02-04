from organs.base_organ import BaseOrgan
from .logic_chemoreceptor import ChemoreceptorLogic
from .view_chemoreceptor import draw_chemoreceptor, draw_chemoreceptor_debug

class Chemoreceptor(BaseOrgan):
    # Debug modu (tüm kemoreseptörler için)
    DEBUG_ENABLED = True

    def __init__(self, attachment_angle=0, length=5.0):
        # Gövde sınırında olsun
        super().__init__(attachment_angle, offset_distance=1.0)
        self.logic = ChemoreceptorLogic(length)

        # Koku hafızası - daha yoğun bulana kadar takip et
        self.locked_intensity = 0.0  # Kilitlenilen yoğunluk
        self.locked_direction = None  # Kilitlenilen yön

        # Debug bilgileri
        self.debug_tip_pos = None
        self.debug_direction = None
        self.debug_intensity = 0.0
        self.debug_food_positions = []  # Algılanan besinlerin pozisyonları
        self.debug_is_locked = False  # Koku kilidinde mi?

    def get_tip_position(self, parent):
        """Kemoreseptörün uç pozisyonunu döndürür"""
        organ_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        outward_dir = (organ_pos - parent.pos).normalize() if (organ_pos - parent.pos).length() > 0 else parent.direction
        return organ_pos + outward_dir * self.logic.length

    def sample_scent(self, parent, foods):
        """
        Kemoreseptörün PİXEL BAZLI koku algılaması + KOKU KİLİDİ.

        Mantık:
        1. Kemoreseptörün U-yapısı boyunca tüm pixelleri tara
        2. Her pixel için: Koku alanı içindeyse → o noktadaki yoğunluğu ölç
        3. En yoğun kokuyu algılayan pixel'i bul
        4. KOKU KİLİDİ:
           - Yeni yoğunluk > kilitli yoğunluk → Yeni yöne kilitlen
           - Yeni yoğunluk <= kilitli yoğunluk → Eski yönü takip et
           - Koku tamamen kayboldu → Kilidi serbest bırak
        5. Yön = Organizma MERKEZİNDEN → Kilitli pixel'e

        Returns: (total_intensity, gradient_direction)
            - total_intensity: Algılanan yoğunluk
            - gradient_direction: Merkez → hedef yön (Vector2 veya None)
        """
        import pygame

        # Kemoreseptörün tüm pixel noktalarını al
        sample_points = self._get_all_sample_points(parent)

        # Debug
        self.debug_tip_pos = sample_points[-1] if sample_points else None
        self.debug_food_positions = []

        best_intensity = 0.0
        best_point = None

        # Her pixel noktası için
        for point in sample_points:
            # Her besin için koku kontrolü
            for food in foods:
                # Pixel koku alanı içinde mi?
                dist = point.distance_to(food.pos)
                if dist >= food.scent_radius:
                    continue

                # Bu noktadaki koku yoğunluğu
                intensity = food.get_scent_intensity(point)

                if intensity > 0 and self.logic.can_smell_food(intensity):
                    # Debug: temas noktasını kaydet
                    self.debug_food_positions.append((point, intensity))

                    # En yoğun noktayı güncelle
                    if intensity > best_intensity:
                        best_intensity = intensity
                        best_point = point

        # KOKU KİLİDİ MANTIĞI
        current_direction = None
        if best_point is not None:
            to_best_point = best_point - parent.pos
            if to_best_point.length() > 0:
                current_direction = to_best_point.normalize()

        # Kilit kararı
        if best_intensity > self.locked_intensity:
            # Daha yoğun koku bulundu → Yeni yöne kilitlen
            self.locked_intensity = best_intensity
            self.locked_direction = current_direction
            self.debug_is_locked = False
        elif best_intensity > 0 and self.locked_direction is not None:
            # Daha az yoğun ama hala koku var → Eski yönü takip et
            self.debug_is_locked = True
        else:
            # Koku tamamen kayboldu → Kilidi serbest bırak
            self.locked_intensity = 0.0
            self.locked_direction = None
            self.debug_is_locked = False

        # Sonuç: Kilitli yön varsa onu, yoksa mevcut yönü döndür
        result_direction = self.locked_direction if self.locked_direction else current_direction
        result_intensity = best_intensity if best_intensity > 0 else 0.0

        # Debug bilgilerini güncelle
        self.debug_direction = result_direction
        self.debug_intensity = result_intensity

        return result_intensity, result_direction

    def _get_all_sample_points(self, parent):
        """
        Kemoreseptörün U-yapısı boyunca tüm sample noktalarını döndürür.

        U-yapısı:
        - Taban çizgisi (sol-sağ)
        - Sol kol (tabandan uca)
        - Sağ kol (tabandan uca)

        Her çizgi boyunca pixel aralıklarla noktalar oluşturulur.
        """
        import pygame

        points = []

        # Kemoreseptör geometrisi
        organ_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        outward_dir = (organ_pos - parent.pos)
        if outward_dir.length() > 0:
            outward_dir = outward_dir.normalize()
        else:
            outward_dir = parent.direction

        length = self.logic.length
        width = length * 0.8
        perp = pygame.math.Vector2(-outward_dir.y, outward_dir.x)

        # U-yapısının köşe noktaları
        left_base = organ_pos + perp * (width / 2.0)
        right_base = organ_pos - perp * (width / 2.0)
        left_tip = left_base + outward_dir * length
        right_tip = right_base + outward_dir * length

        # Pixel aralığı (yaklaşık 2px)
        pixel_step = 2.0

        # 1. Taban çizgisi (left_base → right_base)
        base_length = width
        base_steps = max(1, int(base_length / pixel_step))
        for i in range(base_steps + 1):
            t = i / base_steps
            point = left_base + (right_base - left_base) * t
            points.append(point)

        # 2. Sol kol (left_base → left_tip)
        arm_steps = max(1, int(length / pixel_step))
        for i in range(1, arm_steps + 1):  # 0 zaten tabanda eklendi
            t = i / arm_steps
            point = left_base + (left_tip - left_base) * t
            points.append(point)

        # 3. Sağ kol (right_base → right_tip)
        for i in range(1, arm_steps + 1):
            t = i / arm_steps
            point = right_base + (right_tip - right_base) * t
            points.append(point)

        return points

    def draw(self, screen, parent):
        pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        outward_dir = (pos - parent.pos).normalize() if (pos - parent.pos).length() > 0 else parent.direction
        draw_chemoreceptor(screen, pos, outward_dir, self.logic.length, self.logic.length)

        # Debug çizimi
        if Chemoreceptor.DEBUG_ENABLED and self.debug_tip_pos:
            draw_chemoreceptor_debug(
                screen,
                parent.pos,
                self.debug_tip_pos,
                self.debug_direction,
                self.debug_intensity,
                self.debug_food_positions,
                self.debug_is_locked,
                self.locked_intensity
            )

    def grow(self):
        self.logic.grow()

    def is_touching(self, parent, target_pos, target_radius):
        """U-yapısı koku noktasına fiziksel olarak temas ediyor mu?"""
        organ_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        # Reseptörün ucu (U'nun kollarının ulaştığı yer)
        outward_dir = (organ_pos - parent.pos).normalize() if (organ_pos - parent.pos).length() > 0 else parent.direction
        tip_pos = organ_pos + outward_dir * self.logic.length

        # Basit bir çarpışma kontrolü: Merkeze veya uca yakınlık
        dist_to_base = organ_pos.distance_to(target_pos)
        dist_to_tip = tip_pos.distance_to(target_pos)

        # Eğer koku noktası taban veya uç arasındaysa temas vardır
        return dist_to_base < target_radius or dist_to_tip < target_radius