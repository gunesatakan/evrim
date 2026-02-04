import pygame
import math

def draw_flagella(screen, pos, direction, radius, color, length, is_shutdown=False, boost=1.0,
                  attachment_angle=math.pi, thrust_angle=math.pi, show_thrust_vector=False):
    """Hücrenin attachment_angle noktasından çıkan, thrust_angle yönünde dalgalanan kamçı (Flagellum). Boost ile sallanma hızı artar."""
    if direction.length() == 0:
        return

    dir_angle = math.atan2(direction.y, direction.x)

    # Başlangıç noktası: hücrenin kenarında, ATTACHMENT açısında (fiziksel tutunma noktası)
    world_attachment_angle = dir_angle + attachment_angle
    attachment_dir = pygame.math.Vector2(math.cos(world_attachment_angle), math.sin(world_attachment_angle))
    start_pos = pos + attachment_dir * radius

    # Flagella'nın uzanma yönü: thrust_angle'a göre (sapma dahil)
    world_thrust_angle = dir_angle + thrust_angle
    flagella_dir = pygame.math.Vector2(math.cos(world_thrust_angle), math.sin(world_thrust_angle))
    perp_dir = pygame.math.Vector2(-flagella_dir.y, flagella_dir.x)
    points = [start_pos]
    segments = 10

    # Zaman katsayısı boost ile çarpılıyor (Boost 3x ise 3 kat hızlı dalgalanır)
    t = 0 if is_shutdown else (pygame.time.get_ticks() / 100.0) * boost

    for i in range(1, segments + 1):
        pw = i / segments
        dist = pw * length
        base_pos = start_pos + flagella_dir * dist
        current_amp = 0 if is_shutdown else 2.0 * pw
        wave_offset = perp_dir * math.sin(t + pw * 10) * current_amp
        points.append(base_pos + wave_offset)

    if len(points) > 1:
        pygame.draw.lines(screen, color, False, points, 1)

