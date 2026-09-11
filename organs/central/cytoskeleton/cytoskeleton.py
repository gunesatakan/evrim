import pygame
from organs.base_organ import BaseOrgan
from .danger_transmission.danger_transmission import DangerTransmission

class Cytoskeleton(BaseOrgan):
    def __init__(self):
        super().__init__(attachment_angle=0, offset_distance=0)
        self.logic = DangerTransmission()

    def update(self, dt, parent, nearby_threats, memory_system, scent_intensity,
               prey_dir=None, behavior_response=0.0, koku_gradyani=None,
               behavior_dir=None, behavior_is_social=None):
        """
        Sinyalleri işler ve parent'ın yönünü ve görsel vektörlerini günceller.

        scent_intensity: Skalar koku yoğunluğu (float)
        """
        new_dir, vec_type, vec_value = self.logic.process_signals(
            dt,
            parent,  # organism'i gönder (interoception için)
            nearby_threats,
            memory_system,
            scent_intensity,
            prey_dir,
            behavior_response,
            koku_gradyani,
            behavior_dir,
            behavior_is_social
        )
        
        # Kararı Organism'e uygula - HAREKET yönü
        if new_dir:
            # ESCAPE durumunda smoothing yapma - direkt takip et!
            if vec_type == 'ESCAPE':
                parent.target_movement = new_dir
            else:
                import math
                # Mevcut hareket yönü ile yeni hedef arasındaki açı farkını hesapla
                current_move = parent.target_movement if parent.target_movement else parent.direction
                cur_angle = math.atan2(current_move.y, current_move.x)
                new_angle = math.atan2(new_dir.y, new_dir.x)
                angle_diff = abs((new_angle - cur_angle + math.pi) % (2 * math.pi) - math.pi)

                # Eğer hedef çok arkadaysa (>120°), smoothing yapma
                if angle_diff > math.radians(120):
                    parent.target_movement = new_dir
                else:
                    # Normal durumda smooth geçiş
                    lerp_factor = 0.3
                    smoothed = current_move.lerp(new_dir, lerp_factor)
                    if smoothed.length() > 0:
                        parent.target_movement = smoothed.normalize()
                    else:
                        parent.target_movement = new_dir

        # Görselleştirme verilerini uygula
        parent.current_calm_escape_vector = None
        parent.current_trail_escape_vector = None
        parent.current_wall_avoid_vector = None
        parent.current_hunt_vector = None

        if vec_type == 'ESCAPE':
            parent.current_calm_escape_vector = vec_value
        elif vec_type == 'TRAIL':
            parent.current_trail_escape_vector = vec_value
        elif vec_type == 'WALL_AVOID':
            parent.current_wall_avoid_vector = vec_value
        elif vec_type == 'HUNT':
            parent.current_hunt_vector = vec_value

    def draw(self, screen, parent):
        """Sitoplazmayi kesen filament agi.

        Onceden hicbir sey cizmiyordu (`pass`), yani iskeleti olan hucre ile
        olmayan hucre gorsel olarak ayni gorunuyordu. Gercekte iskelet
        hucrenin ic yapisidir: bakteride MreB sarmallari ve FtsZ halkasi,
        okaryotta aktin + mikrotubul agi. Sitoplazmayi bastan basa gecer.
        """
        import math
        r = getattr(parent, 'radius', 0.0) * 0.78
        if r < 4:
            return
        cx, cy = parent.pos.x, parent.pos.y
        renk = getattr(parent, 'color', (180, 180, 180))
        ton = tuple(min(255, int(c * 0.55) + 60) for c in renk)
        # MreB benzeri sarmal seritler: govdeyi capraz kesen yaylar
        for k in range(3):
            faz = k * 2.094               # 120 derece arayla
            noktalar = []
            for i in range(13):
                t = i / 12.0
                a = faz + t * 3.4
                rr = r * (0.30 + 0.70 * math.sin(math.pi * t))
                noktalar.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            if len(noktalar) > 2:
                pygame.draw.lines(screen, ton, False, noktalar, 1)
        # FtsZ benzeri bolunme halkasi - govdenin ortasinda ince bir cember
        pygame.draw.circle(screen, ton, (int(cx), int(cy)), int(r * 0.5), 1)

    def gelisim(self):
        """Iskeletin gelisme ekseni YOKTUR.

        grow() bos: iskelet buyuyup kucullmez, karar makinesidir. Bos
        liste dondurmek panele "bu organ var ama yukseltilemez" dedirtir;
        gelisim() hic tanimlamamak ise "bilmiyorum" demek olurdu ve
        ikisi ayni sey degil.
        """
        return []

    def grow(self):
        pass
