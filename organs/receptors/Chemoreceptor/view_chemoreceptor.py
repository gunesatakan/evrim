import pygame
import math

def draw_chemoreceptor(screen, organ_pos, outward_dir, length, color_ignore):
    """Beyazdan Çam Yeşili (Pine Green) rengine gradyanlı U-kemoreseptör."""
    # Renk: Beyaz (255, 255, 255) -> Çam Yeşili (1, 121, 111)
    # length 5.0 -> 20.0 menzilinde gelişim
    progress = min(max(0, (length - 5.0) / 15.0), 1.0)

    r = int(255 - progress * 254) # 255 -> 1
    g = int(255 - progress * 134) # 255 -> 121
    b = int(255 - progress * 144) # 255 -> 111
    color = (r, g, b)

    width = length * 0.8
    perp = pygame.math.Vector2(-outward_dir.y, outward_dir.x) * (width / 2.0)

    left_start = organ_pos + perp
    left_end = left_start + outward_dir * length
    right_start = organ_pos - perp
    right_end = right_start + outward_dir * length

    # U-yapısını çiz
    pygame.draw.line(screen, color, (int(left_start.x), int(left_start.y)), (int(left_end.x), int(left_end.y)), 3)
    pygame.draw.line(screen, color, (int(right_start.x), int(right_start.y)), (int(right_end.x), int(right_end.y)), 3)
    pygame.draw.line(screen, color, (int(left_start.x), int(left_start.y)), (int(right_start.x), int(right_start.y)), 3)


def draw_chemoreceptor_debug(screen, parent_pos, tip_pos, direction, intensity, contact_points,
                             is_locked=False, locked_intensity=0.0):
    """
    Kemoreseptör debug bilgilerini çizer.

    - Temas noktaları: Yoğunluğa göre renkli noktalar (kırmızı=yoğun, mavi=zayıf)
    - Hesaplanan yön: Sarı ok (normal) veya Turuncu ok (kilitli)
    - En yoğun nokta: Büyük kırmızı halka
    - Kilit durumu: Turuncu gösterge
    """
    if tip_pos is None:
        return

    parent = (int(parent_pos.x), int(parent_pos.y))

    # 1. Temas noktalarını çiz (yoğunluğa göre renk)
    best_point = None
    best_intensity = 0.0

    for point, point_intensity in contact_points:
        px = (int(point.x), int(point.y))

        # Yoğunluğa göre renk: Mavi (zayıf) → Kırmızı (yoğun)
        red = int(min(255, point_intensity * 255))
        blue = int(max(0, 255 - point_intensity * 255))
        color = (red, 100, blue)

        # Nokta boyutu yoğunluğa göre
        size = max(2, int(3 + point_intensity * 4))
        pygame.draw.circle(screen, color, px, size)

        # En yoğun noktayı takip et
        if point_intensity > best_intensity:
            best_intensity = point_intensity
            best_point = point

    # 2. En yoğun nokta - Büyük kırmızı halka
    if best_point is not None:
        best_px = (int(best_point.x), int(best_point.y))
        pygame.draw.circle(screen, (255, 50, 50), best_px, 8, 2)

    # 3. Hesaplanan yön - Sarı ok (normal) veya Turuncu ok (kilitli)
    if direction and direction.length() > 0:
        arrow_length = 40
        arrow_end = parent_pos + direction * arrow_length
        end = (int(arrow_end.x), int(arrow_end.y))

        # Kilit durumuna göre renk: Turuncu (kilitli) veya Sarı (normal)
        arrow_color = (255, 150, 0) if is_locked else (255, 255, 0)

        # Ok gövdesi
        line_width = 3 if is_locked else 2
        pygame.draw.line(screen, arrow_color, parent, end, line_width)

        # Ok ucu
        arrow_head_size = 8
        angle = math.atan2(direction.y, direction.x)
        left_angle = angle + math.radians(150)
        right_angle = angle - math.radians(150)

        left_point = (int(arrow_end.x + arrow_head_size * math.cos(left_angle)),
                      int(arrow_end.y + arrow_head_size * math.sin(left_angle)))
        right_point = (int(arrow_end.x + arrow_head_size * math.cos(right_angle)),
                       int(arrow_end.y + arrow_head_size * math.sin(right_angle)))

        pygame.draw.line(screen, arrow_color, end, left_point, line_width)
        pygame.draw.line(screen, arrow_color, end, right_point, line_width)

    # 4. Yoğunluk ve kilit durumu (metin)
    font = pygame.font.Font(None, 20)
    if is_locked:
        text = font.render(f"LOCKED: {locked_intensity:.2f}", True, (255, 150, 0))
    elif intensity > 0:
        text = font.render(f"Scent: {intensity:.2f}", True, (255, 255, 100))
    else:
        text = None

    if text:
        screen.blit(text, (parent[0] + 15, parent[1] - 15))
