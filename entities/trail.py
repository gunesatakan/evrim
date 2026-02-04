import pygame
import time

class TrailPoint:
    def __init__(self, x, y, owner_uid, direction, radius):
        self.pos = pygame.math.Vector2(x, y)
        self.owner_uid = owner_uid
        self.direction = pygame.math.Vector2(direction)
        
        # 1. Koku Yoğunluğu Hesaplama (Hacim Oranı x 10)
        # Formül: (Alan / Standart Alan) * 10 => (r^2 / 100) * 10 = r^2 / 10
        self.max_intensity = (radius ** 2) / 10.0
        self.current_intensity = float(self.max_intensity)
        
        # 2. Azalma Oranı: Her saniye azami değerin %5'i
        # Bu sayede her iz boyutu ne olursa olsun 20 saniyede silinir.
        self.decay_per_second = self.max_intensity * 0.05
        
        self.radius = radius
        self.timestamp = time.time()
        self.life_time = 20.0 

    def update(self, dt):
        self.current_intensity -= self.decay_per_second * dt
        if self.current_intensity < 0:
            self.current_intensity = 0

class TrailManager:
    def __init__(self):
        self.points = []

    def add_point(self, x, y, owner_uid, direction, radius):
        self.points.append(TrailPoint(x, y, owner_uid, direction, radius))

    def update(self, dt):
        active_points = []
        for p in self.points:
            p.update(dt)
            if p.current_intensity > 0:
                active_points.append(p)
        self.points = active_points

    def draw(self, screen):
        for p in self.points:
            intensity_ratio = p.current_intensity / p.max_intensity
            if intensity_ratio <= 0: continue
            
            # Görsel netlik için alpha hesaplaması
            alpha = int(120 * intensity_ratio)
            # İz boyutu yoğunlukla birlikte hafifçe daralsın
            draw_radius = int(p.radius * (0.4 + 0.6 * intensity_ratio))
            
            s = pygame.Surface((draw_radius*2, draw_radius*2), pygame.SRCALPHA)
            color = (200, 100, 100, alpha) if "kaotropi" in p.owner_uid else (150, 150, 150, alpha)
            
            pygame.draw.circle(s, color, (draw_radius, draw_radius), draw_radius)
            screen.blit(s, (int(p.pos.x - draw_radius), int(p.pos.y - draw_radius)))

    def get_nearby_trails(self, pos, radius, ignore_uid=None):
        nearby = []
        for p in self.points:
            if ignore_uid and p.owner_uid == ignore_uid:
                continue
            if pos.distance_to(p.pos) <= radius:
                nearby.append(p)
        return nearby
