import pygame
import math
import colorsys

def draw_mechanoreceptor_sausage(screen, parent_pos, radius, attachment_angle, parent_direction, size):
    """İnce ve hücre zarına yayılmış sosis mekanoreseptör + Duyma Aurası."""
    base_angle = math.atan2(parent_direction.y, parent_direction.x)
    total_angle = base_angle + attachment_angle
    
    # 1. DUYMA AURASI (Sound Radius)
    # Organın merkez konumu
    organ_center_offset = pygame.math.Vector2(math.cos(total_angle), math.sin(total_angle)) * radius
    organ_pos = parent_pos + organ_center_offset
    
    # Duyma menzili (Logic'ten gelmeli ama view'de size üzerinden tahmin edebiliriz veya parametre alabiliriz)
    # Simdilik size * 30 standartini kullanalim
    sound_radius = int(size * 30)
    if sound_radius < 1: sound_radius = 1
    
    aura_surf = pygame.Surface((sound_radius*2, sound_radius*2), pygame.SRCALPHA)
    # Gri, çok şeffaf bir aura
    pygame.draw.circle(aura_surf, (150, 150, 150, 20), (sound_radius, sound_radius), sound_radius)
    screen.blit(aura_surf, (int(organ_pos.x - sound_radius), int(organ_pos.y - sound_radius)))

    # 2. SOSIS GÖRSELİ
    # Fiziksel boyut SABİT, sadece renk değişiyor
    progress = min(max(0, (size - 1.0) / 2.0), 1.0)
    r = int(255 - progress * 205)
    g = int(255 - progress * 155)
    b = 255
    color = (r, g, b)

    angle_span = math.radians(45)
    start_angle = total_angle - angle_span / 2
    thickness = 2.0  # Sabit kalınlık
    
    points = []
    segments = 15
    for i in range(segments + 1):
        angle = start_angle + (angle_span * i / segments)
        p = parent_pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * (radius + thickness)
        points.append(p)
    for i in range(segments, -1, -1):
        angle = start_angle + (angle_span * i / segments)
        p = parent_pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * radius
        points.append(p)
        
    if len(points) > 2:
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 1)
