import time
import pygame

class MemoryProtein:
    def __init__(self, key, data, stability=5.0):
        self.key = key
        self.data = data # (start, end)
        self.creation_time = time.time()
        self.stability = stability

    @property
    def is_degraded(self):
        return (time.time() - self.creation_time) > self.stability

class DirectionMemorySystem:
    def __init__(self, capacity=10):
        self.proteins = {} 
        self.capacity = capacity

    def encode(self, key, data, stability=5.0):
        if len(self.proteins) >= self.capacity and key not in self.proteins:
            oldest_key = next(iter(self.proteins))
            del self.proteins[oldest_key]
        self.proteins[key] = MemoryProtein(key, data, stability)

    def retrieve(self, key):
        protein = self.proteins.get(key)
        if protein:
            if protein.is_degraded:
                del self.proteins[key]
                return None
            return protein.data
        return None

    def forget(self, key):
        if key in self.proteins:
            del self.proteins[key]

    def update(self):
        current_keys = list(self.proteins.keys())
        for key in current_keys:
            if self.proteins[key].is_degraded:
                del self.proteins[key]
    
    @property
    def memory_map(self):
        return {key: p.data for key, p in self.proteins.items() if not p.is_degraded}

    def draw(self, screen, color):
        """Hafızadaki rotaları çizer."""
        WIDTH, HEIGHT = screen.get_size()
        SCALE = 10 # Sabit SCALE değeri, entity.py'dan almak yerine
        
        for uid, protein in self.proteins.items():
            if protein.is_degraded: continue
            
            start, end = protein.data
            line_vec = end - start
            if line_vec.length() == 0: continue
            
            if uid == "trail_prediction":
                # Koku İzi Tahmini
                prediction_dir = line_vec.normalize()
                cone_angle = 40 
                p1 = start
                left_dir = prediction_dir.rotate(-cone_angle / 2)
                right_dir = prediction_dir.rotate(cone_angle / 2)
                p2 = p1 + left_dir * line_vec.length()
                p3 = p1 + right_dir * line_vec.length()
                
                cone_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(cone_surf, (int(color[0]), int(color[1]), int(color[2]), 20), [p1, p2, p3])
                screen.blit(cone_surf, (0, 0))
                
                pygame.draw.line(screen, (int(color[0]), int(color[1]), int(color[2]), 40), p1, p2, 1)
                pygame.draw.line(screen, (int(color[0]), int(color[1]), int(color[2]), 40), p1, p3, 1)
            else:
                # Tehdit Rotaları
                pygame.draw.line(screen, color, start, end, int(6 * 10)) # 6 * SCALE