import math
import random

class MotorCalibration:
    """
    Motor kontrol kalibrasyonu.
    Flagella/Cilia'nın fiziksel etkisini öğrenerek doğru deflection hesaplar.

    Hibrit yaklaşım:
    1. Fizikten teorik gain hesapla (başlangıç)
    2. Sürekli adaptive güncelleme (ince ayar)
    """

    def __init__(self):
        # Öğrenilen gain: "1 birim deflection = X birim açısal hız"
        # Başlangıçta None, ilk fizik hesabında set edilir
        self.learned_gain = None

        # Adaptive öğrenme parametreleri
        self.learning_rate = 0.1  # Ne kadar hızlı adapte olsun
        self.min_deflection_threshold = 0.05  # Bu altında öğrenme yapma (gürültü)

        # 180 derece problemi için: seçilen dönüş yönünü hatırla
        self.chosen_turn_direction = 0  # -1: sol, +1: sağ, 0: henüz seçilmedi

        # Son frame verileri (karşılaştırma için)
        self.last_deflection = 0.0
        self.last_direction_angle = 0.0

        # Stabilite için
        self.gain_history = []
        self.max_history = 10

    def estimate_theoretical_gain(self, organism):
        """
        Fizik formüllerinden teorik gain hesapla.
        Bu değer başlangıç tahmini - adaptive ile düzeltilecek.
        """
        # Basit model: gain ≈ (toplam tork kapasitesi) / (atalet momenti)

        total_torque_capacity = 0.0

        for organ in organism.organs:
            if hasattr(organ.logic, 'thrust_magnitude') and hasattr(organ.logic, 'max_deflection'):
                # Bu organın maksimum tork üretme kapasitesi
                r = organism.radius  # Kol uzunluğu
                max_thrust = organ.logic.thrust_magnitude
                max_deflection = organ.logic.max_deflection

                # Maksimum tork ≈ r * F * sin(max_deflection)
                max_torque = r * max_thrust * math.sin(max_deflection)
                total_torque_capacity += abs(max_torque)

        # Atalet momenti (sıvı dolu küre + viskoz ortam: I = 0.8 × m × r²)
        moment_of_inertia = max(1.0, organism.radius ** 2 * 0.8)

        # Teorik gain: 1 birim deflection (-1 to +1) için açısal hız
        if total_torque_capacity > 0:
            # Full deflection (1.0) ile elde edilecek açısal hız
            theoretical_angular_velocity = total_torque_capacity / moment_of_inertia
            return theoretical_angular_velocity

        return 1.0  # Fallback

    def initialize_if_needed(self, organism):
        """İlk kez çağrıldığında teorik gain'i hesapla"""
        if self.learned_gain is None:
            self.learned_gain = self.estimate_theoretical_gain(organism)
            self.last_direction_angle = math.atan2(
                organism.direction.y, organism.direction.x
            )

    def calculate_deflection(self, organism, target_direction):
        """
        Hedef yöne ulaşmak için gereken deflection değerini hesapla.

        Returns: deflection (-1.0 to +1.0)
        """
        self.initialize_if_needed(organism)

        # Mevcut ve hedef açılar
        current_angle = math.atan2(organism.direction.y, organism.direction.x)
        target_angle = math.atan2(target_direction.y, target_direction.x)

        # Açı farkı (en kısa yol)
        angle_diff = target_angle - current_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # 180 derece problemi: Hedef tam arkadaysa hangi yöne döneceğimiz belirsiz
        force_max_deflection = False
        if abs(angle_diff) > math.pi * 0.65:  # ~117 dereceden fazla
            # İlk kez mi yoksa devam mı?
            if self.chosen_turn_direction == 0:
                # Rastgele sağa veya sola seç ve hatırla
                self.chosen_turn_direction = random.choice([-1, 1])
            force_max_deflection = True  # Maksimum deflection zorla
        elif abs(angle_diff) < math.pi * 0.3:  # ~54 derecenin altına düşünce reset
            self.chosen_turn_direction = 0

        # 180 derece durumunda direkt maksimum deflection ver
        if force_max_deflection:
            deflection = self.chosen_turn_direction * 1.0  # ±1.0 maksimum
        else:
            # Normal durum: açısal hız hesapla
            max_angular_velocity = 3.0  # rad/s
            desired_angular_velocity = angle_diff * 2.0  # P gain
            desired_angular_velocity = max(-max_angular_velocity,
                                           min(max_angular_velocity, desired_angular_velocity))

            # Deflection = istenen açısal hız / öğrenilen gain
            if abs(self.learned_gain) > 0.001:
                deflection = desired_angular_velocity / self.learned_gain
            else:
                deflection = 0.0

        # Clamp to valid range
        deflection = max(-1.0, min(1.0, deflection))

        # Kaydet (öğrenme için)
        self.last_deflection = deflection
        self.last_direction_angle = current_angle

        return deflection

    def update_learning(self, organism, dt):
        """
        Gerçek dönüşü ölç ve gain'i güncelle.
        Her frame çağrılmalı.
        """
        if self.learned_gain is None:
            return

        # Mevcut açı
        current_angle = math.atan2(organism.direction.y, organism.direction.x)

        # Gerçek açısal değişim
        angle_change = current_angle - self.last_direction_angle

        # Normalize (-π to +π)
        while angle_change > math.pi:
            angle_change -= 2 * math.pi
        while angle_change < -math.pi:
            angle_change += 2 * math.pi

        # Gerçek açısal hız
        if dt > 0.001:
            actual_angular_velocity = angle_change / dt
        else:
            actual_angular_velocity = 0.0

        # Sadece anlamlı deflection varsa öğren
        if abs(self.last_deflection) > self.min_deflection_threshold:
            # Beklenen açısal hız (mevcut gain'e göre)
            expected_angular_velocity = self.last_deflection * self.learned_gain

            # Hata: gerçek vs beklenen (sadece aynı yönde hareket varsa öğren)
            if abs(expected_angular_velocity) > 0.001:
                # Makul aralıkta mı? (aşırı değerler gürültü olabilir)
                ratio = actual_angular_velocity / expected_angular_velocity
                if 0.2 < ratio < 5.0:
                    # Gain'i güncelle
                    new_gain = self.learned_gain * ratio

                    self.learned_gain = (self.learned_gain * (1 - self.learning_rate) +
                                        new_gain * self.learning_rate)

                    # Stabilite için history tut
                    self.gain_history.append(self.learned_gain)
                    if len(self.gain_history) > self.max_history:
                        self.gain_history.pop(0)

        # Sonraki frame için kaydet
        self.last_direction_angle = current_angle

    def get_confidence(self):
        """
        Kalibrasyon güvenilirliği (0-1).
        History'deki varyans düşükse güvenilirlik yüksek.
        """
        if len(self.gain_history) < 3:
            return 0.0

        mean = sum(self.gain_history) / len(self.gain_history)
        variance = sum((g - mean) ** 2 for g in self.gain_history) / len(self.gain_history)
        std_dev = math.sqrt(variance)

        # Düşük std_dev = yüksek güven
        # std_dev 0 ise güven 1, std_dev yüksekse güven düşük
        confidence = max(0.0, 1.0 - std_dev / (mean + 0.001))
        return confidence
