import game_settings
import math

class FlagellaLogic:
    def __init__(self, length=10.0, thrust_angle=math.pi, max_deflection=math.radians(45)):
        """
        thrust_angle: Temel itme yönü (hücrenin lokal koordinatında, radyan)
                      0 = ileri, π = geri, π/2 = sola, -π/2 = sağa
                      Varsayılan π = geriye doğru itme (hücreyi ileriye iter)
        max_deflection: Maksimum sapma açısı (manevra kabiliyeti)
        """
        self.length = length
        self.base_thrust_angle = thrust_angle      # Temel itme yönü (sabit)
        self.current_thrust_angle = thrust_angle   # Anlık itme yönü (dinamik)
        self.target_thrust_angle = thrust_angle    # Hedef açı (smooth geçiş için)
        self.max_deflection = max_deflection       # Maksimum sapma
        self.angle_speed = 8.0                     # Açı değişim hızı (radyan/saniye)

        # Akıllı güç kontrolü
        self.power = 1.0          # 0.0 = durgun, 1.0 = tam güç
        self.target_power = 1.0   # Hedef güç (smooth geçiş)
        self.power_speed = 5.0    # Güç değişim hızı (saniye başına)

        self.recalculate_boosts()

    @property
    def thrust_angle(self):
        """Geriye uyumluluk için"""
        return self.current_thrust_angle

    def recalculate_boosts(self):
        # Kuvvet büyüklüğü (güç çarpanı ile)
        self.base_thrust = self.length * game_settings.FLAGELLA_SPEED_MULTI

    @property
    def thrust_magnitude(self):
        """Anlık itme kuvveti (güç seviyesine bağlı)"""
        return self.base_thrust * self.power

    def set_power(self, power_level):
        """Flagella gücünü ayarla (0.0 - 1.0)"""
        self.target_power = max(0.0, min(1.0, power_level))

    def set_deflection(self, deflection_amount):
        """
        Thrust açısını belirli bir miktar saptır (hedef olarak ayarlar, anında değiştirmez).
        deflection_amount: -1.0 (saat yönü) ile +1.0 (saat yönü tersi) arası

        Fizik: Flagella arkada (π), thrust açısı artınca (>π) tepki kuvveti
        hücrenin arkasını SOLA iter → saat yönünde döner.
        """
        clamped = max(-1.0, min(1.0, deflection_amount))
        # Negatif deflection → thrust açısı ARTMALI (>π) → saat yönünde dönüş
        self.target_thrust_angle = self.base_thrust_angle - (clamped * self.max_deflection)

    def reset_deflection(self):
        """Thrust açısını temel konuma döndür (hedef olarak)"""
        self.target_thrust_angle = self.base_thrust_angle

    def update(self, dt):
        """
        Her frame çağrılır. Açıyı ve gücü yumuşak şekilde hedefe yaklaştırır.
        dt: delta time (saniye)
        """
        # Açı geçişi
        if self.current_thrust_angle != self.target_thrust_angle:
            diff = self.target_thrust_angle - self.current_thrust_angle

            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi

            max_change = self.angle_speed * dt

            if abs(diff) <= max_change:
                self.current_thrust_angle = self.target_thrust_angle
            else:
                direction = 1 if diff > 0 else -1
                self.current_thrust_angle += direction * max_change

        # Güç geçişi (smooth)
        if self.power != self.target_power:
            power_diff = self.target_power - self.power
            max_power_change = self.power_speed * dt

            if abs(power_diff) <= max_power_change:
                self.power = self.target_power
            else:
                direction = 1 if power_diff > 0 else -1
                self.power += direction * max_power_change

    @property
    def base_energy_cost(self):
        return self.length * game_settings.COST_FLAGELLA

    def update_stats(self, delta_length=0):
        self.length += delta_length
        self.recalculate_boosts()

    def grow(self):
        self.length += game_settings.GROW_FLAGELLA
        self.recalculate_boosts()