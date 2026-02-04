"""
BaseMotorOrgan - Tüm motor organlar için temel sınıf.

Motor organlar (Flagella, Cilia) bu sınıftan türer.
Her motor kendi fiziğine göre itme yönü ve büyüklüğü sağlar.
"""

import math
from organs.base_organ import BaseOrgan


class BaseMotorOrgan(BaseOrgan):
    """
    Tüm motor organlar için temel sınıf.

    Motor organlar kendi fiziklerine göre itme yönü belirler:
    - Flagella: attachment_angle + π (geriye doğru)
    - Cilia: attachment_angle + π/2 (teğet)

    UnifiedMotorController bu arayüzü kullanarak
    hedef hareket yönüne göre motor güçlerini optimize eder.
    """

    def get_thrust_direction(self):
        """
        Bu motorun itme yönünü döndür (global koordinat, radyan).

        Bu metot alt sınıflar tarafından override edilmeli.
        Dönen değer motorun suyu/ortamı ittiği yöndür.
        Hareket yönü bunun tersidir (Newton 3).
        """
        raise NotImplementedError("Alt sınıf get_thrust_direction() metodunu implemente etmeli")

    def get_thrust_magnitude(self):
        """
        Anlık itme büyüklüğünü döndür.

        Bu değer motorun o anki gücüne, stroke fazına vs. bağlıdır.
        """
        if hasattr(self, 'logic') and hasattr(self.logic, 'thrust_magnitude'):
            return self.logic.thrust_magnitude
        return 0.0

    def get_reaction_direction(self):
        """
        Tepki kuvveti yönünü döndür (hareket yönü).

        Bu, itme yönünün tam tersidir (Newton'un 3. yasası).
        """
        return self.get_thrust_direction() + math.pi

    def set_power(self, power):
        """
        Motor gücünü ayarla.

        Args:
            power: 0.0 (kapalı) ile 1.0 (tam güç) arası
        """
        if hasattr(self, 'logic') and hasattr(self.logic, 'set_power'):
            self.logic.set_power(power)
        elif hasattr(self, 'logic') and hasattr(self.logic, 'power_boost'):
            # Cilia için power_boost kullan
            self.logic.power_boost = max(0.0, min(2.0, power * 2.0))

    def get_power(self):
        """Mevcut motor gücünü döndür."""
        if hasattr(self, 'logic'):
            if hasattr(self.logic, 'power'):
                return self.logic.power
            elif hasattr(self.logic, 'power_boost'):
                return self.logic.power_boost / 2.0
        return 1.0

    def contributes_to_direction(self, target_angle):
        """
        Bu motorun hedef yöne katkısını hesapla.

        Args:
            target_angle: Hedef hareket yönü (radyan)

        Returns:
            -1.0 ile +1.0 arası katkı değeri
            +1.0 = tam hedef yönünde katkı
            0.0 = dik açı (nötr)
            -1.0 = tam ters yönde
        """
        reaction_dir = self.get_reaction_direction()
        angle_diff = target_angle - reaction_dir

        # Normalize et (-π, π)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        return math.cos(angle_diff)
