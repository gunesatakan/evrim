"""
UnifiedMotorController - Birleşik Motor Kontrol Sistemi

Tüm motor organları (Flagella, Cilia) koordine eder.
Hedef hareket yönüne göre her motorun gücünü optimize eder.

Bu kontrolcü fizik tabanlı çalışır:
- Her motor kendi fiziğine göre iter (Flagella: geri, Cilia: teğet)
- Hedef yöne katkısına göre güç ayarlanır
- Net kuvvet hareket yönünü belirler
"""

import math
import pygame


class UnifiedMotorController:
    """
    Tüm motor organları koordine eden kontrolcü.

    Flagella ve Cilia'yı aynı anda yönetebilir.
    Her motor kendi fiziğine göre iter, kontrolcü güçleri optimize eder.
    """

    def __init__(self):
        self.target_movement = None
        self.last_net_direction = 0.0

    def set_target_movement(self, direction):
        """
        Hedef hareket yönünü ayarla.

        Args:
            direction: pygame.math.Vector2 - hedef hareket yönü
        """
        if direction is not None and direction.length() > 0:
            self.target_movement = direction.normalize()
        else:
            self.target_movement = None

    def update(self, organism, dt):
        """
        Her frame motor güçlerini güncelle.

        Hedef hareket yönüne göre her motorun gücünü ayarlar.
        Hedefe katkı sağlayan motorlar güçlenir, ters itenler zayıflar.

        NOT: Motor thrust yönleri LOKAL koordinatta (hücreye göre).
        target_movement GLOBAL koordinatta. Karşılaştırmadan önce
        target_movement'ı lokal koordinata çeviriyoruz.
        """
        if self.target_movement is None:
            # Hedef yoksa tüm motorları orta güçte çalıştır
            self._set_all_motors_power(organism, 0.5)
            return

        # Global target'ı lokal koordinata çevir
        cell_heading = math.atan2(organism.direction.y, organism.direction.x)
        global_target_angle = math.atan2(self.target_movement.y, self.target_movement.x)
        target_angle_local = global_target_angle - cell_heading

        for organ in organism.organs:
            if hasattr(organ, 'get_thrust_direction') and hasattr(organ, 'set_power'):
                # Motorun tepki yönü (hareket yönüne katkısı) - LOKAL koordinat
                thrust_dir = organ.get_thrust_direction()
                reaction_dir = thrust_dir + math.pi

                # Açı farkını normalize et (lokal koordinatta)
                angle_diff = target_angle_local - reaction_dir
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi

                # Hedefe katkı (cosine similarity)
                contribution = math.cos(angle_diff)

                # Güç ayarla
                if contribution > 0.1:
                    # Hedefe katkı sağlıyor - güçlendir
                    # Katkı oranına göre güç (0.1 -> 0.5, 1.0 -> 1.0)
                    power = 0.5 + contribution * 0.5
                    organ.set_power(power)
                elif contribution < -0.3:
                    # Ters yönde - kapat veya çok düşük
                    organ.set_power(0.1)
                else:
                    # Nötr bölge - orta güç
                    organ.set_power(0.4)

    def _set_all_motors_power(self, organism, power):
        """Tüm motorları belirli güce ayarla."""
        for organ in organism.organs:
            if hasattr(organ, 'set_power'):
                organ.set_power(power)

    def calculate_net_movement_direction(self, organism):
        """
        Tüm motorlardan net hareket yönünü hesapla.

        Returns:
            float: Net hareket yönü (radyan)
        """
        net_x, net_y = 0.0, 0.0

        for organ in organism.organs:
            if hasattr(organ, 'get_thrust_direction') and hasattr(organ, 'get_thrust_magnitude'):
                thrust_dir = organ.get_thrust_direction()
                magnitude = organ.get_thrust_magnitude()

                # Tepki kuvveti (hareket yönü)
                reaction_dir = thrust_dir + math.pi
                net_x += math.cos(reaction_dir) * magnitude
                net_y += math.sin(reaction_dir) * magnitude

        if abs(net_x) > 0.001 or abs(net_y) > 0.001:
            self.last_net_direction = math.atan2(net_y, net_x)

        return self.last_net_direction

    def get_motor_info(self, organism):
        """
        Debug için motor bilgilerini döndür.

        Returns:
            list: Her motor için (tip, açı, güç, katkı) tuple'ları
        """
        info = []
        target_angle = 0
        if self.target_movement is not None:
            target_angle = math.atan2(self.target_movement.y, self.target_movement.x)

        for organ in organism.organs:
            if hasattr(organ, 'get_thrust_direction'):
                thrust_dir = organ.get_thrust_direction()
                reaction_dir = thrust_dir + math.pi

                angle_diff = target_angle - reaction_dir
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi

                contribution = math.cos(angle_diff)
                power = organ.get_power() if hasattr(organ, 'get_power') else 1.0
                magnitude = organ.get_thrust_magnitude() if hasattr(organ, 'get_thrust_magnitude') else 0.0

                info.append({
                    'type': organ.__class__.__name__,
                    'attachment': math.degrees(organ.attachment_angle),
                    'thrust_dir': math.degrees(thrust_dir),
                    'reaction_dir': math.degrees(reaction_dir),
                    'contribution': contribution,
                    'power': power,
                    'magnitude': magnitude
                })

        return info
