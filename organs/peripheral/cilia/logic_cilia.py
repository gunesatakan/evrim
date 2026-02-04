import game_settings
import math
import random

class CiliaLogic:
    """
    Cilia (Sil) - Kürek Hareketi Fiziği

    Gerçek sillerin çalışma prensibi:
    1. Güç Vuruşu (Power Stroke): Sil dik, yüksek direnç, güçlü itme
    2. Geri Dönüş (Recovery Stroke): Sil yatık, düşük direnç, az geri itme
    3. Net kuvvet = Güç - Geri > 0 (asimetrik itme)

    Flagella'dan farkları:
    - Anlık yön değişimi (gecikme yok)
    - Geri gidebilme (thrust_angle = 0)
    - Döngüsel vuruş hareketi
    - Düşük hız, yüksek manevra
    """

    def __init__(self, length=3.0, base_direction=math.pi, max_deflection=math.radians(75),
                 phase_offset=None):
        """
        Args:
            length: Sil uzunluğu
            base_direction: Temel itme yönü (π = geri, 0 = ileri)
            max_deflection: Maksimum sapma açısı (yön kontrolü için)
            phase_offset: Başlangıç faz ofseti (metachronal dalga için)
        """
        self.length = length
        self.base_direction = base_direction      # Temel itme yönü
        self.target_direction = base_direction    # Hedef yön (motor kontrolden)
        self.max_deflection = max_deflection

        # Vuruş döngüsü parametreleri
        # Metachronal dalga: Her cilia farklı fazda başlar
        if phase_offset is not None:
            self.stroke_phase = phase_offset % 1.0
        else:
            self.stroke_phase = random.random()  # Rastgele başlangıç fazı
        self.stroke_frequency = 0.5       # Hz - yavaş hız (2s döngü) - takip edilebilir animasyon
        self.power_stroke_ratio = 0.25    # Power stroke döngünün %25'i, recovery %75'i
        self.sweep_amplitude = math.radians(60)  # Süpürme genişliği (±30°)

        # Güç katsayıları
        self.power_stroke_coefficient = 1.0    # Güç vuruşunda tam itme
        self.recovery_coefficient = 0.35       # Geri dönüşte %35 (daha fazla kontrol imkanı)

        # Görsel uzanma faktörü (0.0=geri çekilmiş, 1.0=tam uzanmış)
        self.extension = 1.0

        # Pozisyon bazlı kontrol (dönüş için)
        self.power_boost = 1.0                 # 0.0-2.0 arası güç çarpanı
        self.direction_bias = 0.0             # Vuruş yönü sapması (radyan)

        # Dinamik değerler (her frame güncellenir)
        self.current_thrust_angle = base_direction
        self.current_thrust_magnitude = 0.0
        self.is_power_stroke = True

        self.recalculate_boosts()

    @property
    def thrust_angle(self):
        """Geriye uyumluluk için"""
        return self.current_thrust_angle

    @property
    def thrust_magnitude(self):
        """Anlık itme gücü (vuruş fazına bağlı)"""
        return self.current_thrust_magnitude

    def recalculate_boosts(self):
        """Temel itme gücünü hesapla"""
        self.base_thrust_magnitude = self.length * game_settings.CILIA_SPEED_MULTI

    def set_deflection(self, deflection_amount):
        """
        Hedef yönü ayarla (motor kontrolden).
        Cilia'da bu ANLIK uygulanır (flagella gibi smooth değil).

        deflection_amount: -1.0 (saat yönü) ile +1.0 (saat yönü tersi) arası
        """
        clamped = max(-1.0, min(1.0, deflection_amount))
        self.target_direction = self.base_direction - (clamped * self.max_deflection) + self.direction_bias

    def reset_deflection(self):
        """Hedef yönü temel konuma döndür"""
        self.target_direction = self.base_direction
        self.power_boost = 1.0
        self.direction_bias = 0.0

    def set_base_direction(self, direction):
        """
        Temel itme yönünü güncelle (koordineli teğet model için).
        Organizma tarafından çağrılır.
        """
        self.base_direction = direction
        self.target_direction = direction

    def set_turn_control(self, power_boost, direction_bias=0.0):
        """
        Pozisyon bazlı dönüş kontrolü.

        Args:
            power_boost: Güç çarpanı (0.0 = dur, 1.0 = normal, 2.0 = maksimum)
            direction_bias: Ek yön sapması (radyan)
        """
        self.power_boost = max(0.0, min(2.0, power_boost))
        self.direction_bias = direction_bias

    def update(self, dt):
        """
        Her frame çağrılır. Vuruş döngüsünü ilerletir ve anlık değerleri hesaplar.

        Ahtapot solungacı modeli:
        - Power stroke (%25): Ani snap-out, kuvvet başta zirve yapar
        - Recovery stroke (%75): Yavaş geri çekilme, minimum sürüklenme

        Args:
            dt: Delta time (saniye)
        """
        # Vuruş fazını ilerlet
        self.stroke_phase += self.stroke_frequency * dt
        self.stroke_phase = self.stroke_phase % 1.0  # 0-1 arasında tut

        # Asimetrik zamanlama: Power stroke kısa (%25), Recovery uzun (%75)
        self.is_power_stroke = self.stroke_phase < self.power_stroke_ratio

        if self.is_power_stroke:
            # === POWER STROKE: Güçlü itme ===
            # Döngünün %25'inde 0→1 faz pozisyonu
            phase_position = self.stroke_phase / self.power_stroke_ratio
            thrust_coefficient = self.power_stroke_coefficient

            # Kuvvet başta zirve, hızla düşer (ani itme)
            stroke_intensity = (1.0 - phase_position) ** 0.5

            # Uzanma: Tam uzanmış, hafif geri çekilir
            self.extension = 1.0 - 0.15 * phase_position  # 1.0 → 0.85

            # Power stroke: SABİT YÖNDE güçlü itme (süpürme yok!)
            # Thrust açısı = hedef yön (sweep offset yok)
            sweep_offset = 0.0

        else:
            # === RECOVERY STROKE: Sessiz geri dönme ===
            # Döngünün %75'inde 0→1 faz pozisyonu
            phase_position = (self.stroke_phase - self.power_stroke_ratio) / (1.0 - self.power_stroke_ratio)

            # Recovery'de düşük ama kontrol edilebilir kuvvet
            thrust_coefficient = self.recovery_coefficient * 0.5  # ~%17 kuvvet
            stroke_intensity = 0.4

            # Uzanma: Yavaşça geri çekil (0.85 → 0.40)
            self.extension = 0.85 - 0.45 * phase_position

            # Recovery stroke: Görsel sweep var ama kuvvet ihmal edilebilir
            eased_phase = phase_position ** 2
            sweep_offset = self.sweep_amplitude * (-1.0 + 2.0 * eased_phase)

        # Anlık thrust açısı
        self.current_thrust_angle = self.target_direction + sweep_offset

        # Anlık thrust büyüklüğü
        self.current_thrust_magnitude = (
            self.base_thrust_magnitude *
            thrust_coefficient *
            self.power_boost *
            max(0.1, stroke_intensity)
        )

    def get_stroke_visual_offset(self):
        """
        Görselleştirme için süpürme ofseti.
        Sil'in o anki açısal pozisyonunu döndürür.
        Asimetrik zamanlama ve easing uygulanır.
        """
        if self.is_power_stroke:
            phase_position = self.stroke_phase / self.power_stroke_ratio
            eased_phase = 1.0 - (1.0 - phase_position) ** 2  # ease-out
            return self.sweep_amplitude * (1.0 - 2.0 * eased_phase)
        else:
            phase_position = (self.stroke_phase - self.power_stroke_ratio) / (1.0 - self.power_stroke_ratio)
            eased_phase = phase_position ** 2  # ease-in
            return self.sweep_amplitude * (-1.0 + 2.0 * eased_phase)

    @property
    def base_energy_cost(self):
        """Enerji maliyeti - cilia daha fazla enerji harcar"""
        return self.length * 0.05  # Flagella'dan daha yüksek (0.03 vs 0.05)

    def update_stats(self, delta_length=0):
        self.length += delta_length
        self.recalculate_boosts()

    def grow(self):
        self.length += game_settings.GROW_CILIA
        self.recalculate_boosts()
