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

    # Su mavisi, yari saydam - ZARLA CEVRILI bir kesedir, o yuzden
    # dolgunun yaninda bir KENAR da cizilir. Kenarsiz haliyle koyu
    # sitoplazmada yalnizca sonuk bir leke olarak gorunuyordu ve
    # "vakuolu goremiyorum" denmesine yol aciyordu.
    pad = 2
    s = pygame.Surface(((vac_radius + pad) * 2,) * 2, pygame.SRCALPHA)
    mid = vac_radius + pad
    pygame.draw.circle(s, (100, 200, 255, 150), (mid, mid), vac_radius)
    pygame.draw.circle(s, (190, 235, 255, 230), (mid, mid), vac_radius, 1)
    # kesenin parlama noktasi - kabarcik oldugu okunsun
    if vac_radius >= 4:
        pygame.draw.circle(s, (225, 245, 255, 190),
                           (int(mid - vac_radius * 0.32), int(mid - vac_radius * 0.32)),
                           max(1, vac_radius // 4))
    screen.blit(s, (int(vac_pos.x - mid), int(vac_pos.y - mid)))