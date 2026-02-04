import pygame
import random
import math
import game_settings
from entities.entity import Entity, WIDTH, HEIGHT, GREEN

class Food(Entity):
    def __init__(self, x, y):
        # Radius'u FOOD_AREA'dan hesapla: area = π * r² → r = √(area / π)
        radius = math.sqrt(game_settings.FOOD_AREA / math.pi)
        super().__init__(x, y, radius, 0, GREEN)

        # Koku sistemi
        self.scent_radius = radius * 10.5  # Kokunun yayılma mesafesi (%30 azaltıldı)
        self.max_scent_intensity = 1.0   # Merkezde maksimum yoğunluk

    def get_scent_intensity(self, pos):
        """
        Verilen pozisyondaki koku yoğunluğunu hesaplar.
        Merkeze yakın = yüksek, uzaklaştıkça azalır.

        Returns: 0.0 (koku yok) - 1.0 (maksimum yoğunluk)
        """
        dist = self.pos.distance_to(pos)

        # Koku alanı dışındaysa
        if dist >= self.scent_radius:
            return 0.0

        # Besin üzerindeyse maksimum
        if dist <= self.radius:
            return self.max_scent_intensity

        # Gradyan: Üstel azalma (daha gerçekçi difüzyon)
        # intensity = max * e^(-k * distance)
        ratio = (dist - self.radius) / (self.scent_radius - self.radius)
        # Daha yumuşak azalma: k=2 (önceki k=3 çok hızlı azalıyordu)
        intensity = self.max_scent_intensity * math.exp(-2 * ratio)

        return max(0.0, intensity)

    def draw(self, screen):
        # Koku alanını çiz (dıştan içe, yoğunluk artan)
        scent_color_base = (0, 100, 0)  # Koyu yeşil baz
        num_rings = 8  # Halka sayısı

        for i in range(num_rings, 0, -1):
            # Halka yarıçapı (dıştan içe)
            ring_ratio = i / num_rings
            ring_radius = self.radius + (self.scent_radius - self.radius) * ring_ratio

            # Bu mesafedeki yoğunluk (formülle eşleşmeli)
            intensity = math.exp(-2 * ring_ratio)  # 0.14 - 1.0 arası

            # Renk: yoğunlukla orantılı alpha efekti (RGB ile simüle)
            alpha_sim = int(intensity * 40)  # Maksimum 40 opaklık
            ring_color = (scent_color_base[0] + alpha_sim,
                          scent_color_base[1] + alpha_sim,
                          scent_color_base[2] + alpha_sim)

            pygame.draw.circle(screen, ring_color,
                             (int(self.pos.x), int(self.pos.y)),
                             int(ring_radius), 2)  # Sadece çizgi (width=2)

        # Besinin kendisi (üstte)
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius))

    @staticmethod
    def spawn(count):
        return [Food(random.randint(30, WIDTH - 30), random.randint(30, HEIGHT - 30)) for _ in range(count)]
