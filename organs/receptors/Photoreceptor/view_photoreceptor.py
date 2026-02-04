import pygame
import colorsys
import math

def draw_vision_cone(screen, pos, base_angle_rad, vision_angle_rad, vision_range, color):
    """Görüş konisini pie/arc şeklinde çizer. 360 dereceye kadar destekler."""
    vision_angle_deg = math.degrees(vision_angle_rad)

    # 360 derece veya üstü = tam daire
    if vision_angle_deg >= 360:
        cone_surf = pygame.Surface((int(vision_range*2), int(vision_range*2)), pygame.SRCALPHA)
        cone_color = (int(color[0]), int(color[1]), int(color[2]), 30)
        pygame.draw.circle(cone_surf, cone_color, (int(vision_range), int(vision_range)), int(vision_range))
        screen.blit(cone_surf, (int(pos.x - vision_range), int(pos.y - vision_range)))
        return

    # Pie şeklinde çizim için noktalar oluştur
    points = [pos]  # Merkez (göz pozisyonu)

    # Arc üzerinde noktalar - açıya göre segment sayısı
    num_segments = max(8, int(vision_angle_deg / 5))  # Her 5 derecede bir nokta

    start_angle = base_angle_rad - vision_angle_rad / 2
    angle_step = vision_angle_rad / num_segments

    for i in range(num_segments + 1):
        angle = start_angle + i * angle_step
        point = pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * vision_range
        points.append(point)

    # Polygon olarak çiz
    if len(points) >= 3:
        WIDTH, HEIGHT = screen.get_size()
        cone_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        cone_color = (int(color[0]), int(color[1]), int(color[2]), 30)
        pygame.draw.polygon(cone_surf, cone_color, points)
        screen.blit(cone_surf, (0, 0))


def draw_photoreceptor(screen, pos, level, color_hue, radius, neon_level=0.5):
    """Göz çizimi - range ile renk tonu (level), açı ile renk pigmenti (neon_level)."""
    # Renk tonu: Kırmızı (0.0) -> Mor (0.8) - range'e bağlı
    current_hue = (color_hue + level * 0.8) % 1.0

    # Açı ile saturation: düşük açıda soluk, yüksek açıda pigmentli
    # Subtle değişim: 0.65 -> 1.0
    saturation = 0.65 + neon_level * 0.35

    rgb = colorsys.hsv_to_rgb(current_hue, saturation, 1.0)
    ec = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

    size_factor = radius / 10.0

    # Ana göz
    eye_size = int(4.0 * size_factor)
    pygame.draw.circle(screen, ec, (int(pos.x), int(pos.y)), eye_size)

    # Parlak çekirdek
    pygame.draw.circle(screen, (255, 255, 255), (int(pos.x), int(pos.y)), max(1, int(1.5 * size_factor)))