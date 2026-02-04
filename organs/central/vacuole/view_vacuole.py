import pygame
import math

def draw_vacuole(screen, pos, parent_radius, direction, area):
    """Hücre içinde enerji deposu kesesi."""
    # Vakuol yarıçapı area'dan hesaplanır (alan = pi * r^2 -> r = sqrt(alan/pi))
    vac_radius = int(math.sqrt(area / math.pi))
    if vac_radius < 1:
        vac_radius = 1

    # Hücrenin içinde, yöne göre pozisyonlanır
    offset_dist = parent_radius * 0.3
    # Yönün tersine (arkaya doğru) yerleştir
    offset_vec = pygame.math.Vector2(-direction.x, -direction.y) * offset_dist
    vac_pos = pos + offset_vec

    # Su mavisi, yarı saydam
    s = pygame.Surface((vac_radius*2, vac_radius*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (100, 200, 255, 150), (vac_radius, vac_radius), vac_radius)
    screen.blit(s, (int(vac_pos.x - vac_radius), int(vac_pos.y - vac_radius)))