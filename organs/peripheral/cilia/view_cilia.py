import pygame
import math

def draw_cilia(screen, organ_pos, outward_dir, length, color, is_shutdown=False,
               calcium_boost=1.0, stroke_offset=0.0, is_power_stroke=True, power_boost=1.0,
               stroke_phase=0.0, extension=1.0, thrust_dir=None, reverse_stroke=False):
    """
    Cilia görselleştirmesi - Kürek hareketi.

    Cilia HER ZAMAN gövdeden DIŞARI doğru uzanır (kürek gibi).
    Sadece TEĞET yönde sallanır - asla gövdenin içine girmez.

    Power Stroke: Teğet yönde hızlı sallanma (itme)
    Recovery Stroke: Teğet yönde yavaş geri dönme

    thrust_dir: Cilia'nın itme yönü - sadece hangi teğet yöne sallandığını belirler.
    reverse_stroke: True ise animasyon tersine çalışır (keskin dönüşte karşı taraf)
                    Kürek İLERİYE doğru çekilir (normal GERİYE yerine)
    """
    base_angle = math.atan2(outward_dir.y, outward_dir.x)

    if is_shutdown:
        # Shutdown - soluk ve hareketsiz
        faint_color = tuple(max(30, c // 3) for c in color)
        end_pos = organ_pos + pygame.math.Vector2(
            math.cos(base_angle), math.sin(base_angle)
        ) * (length * 0.3)
        pygame.draw.line(screen, faint_color,
                        (int(organ_pos.x), int(organ_pos.y)),
                        (int(end_pos.x), int(end_pos.y)), 1)
        return

    # İtme yönünden teğet sapma açısını hesapla
    # thrust_dir, teğet yönlerden biri (outward ± 90°)
    if thrust_dir is not None:
        thrust_angle = math.atan2(thrust_dir.y, thrust_dir.x)
        # İtme yönü ile dışarı yön arasındaki fark = teğet sapma
        tangent_offset = thrust_angle - base_angle
        # -π ile +π arasına normalize et
        while tangent_offset > math.pi:
            tangent_offset -= 2 * math.pi
        while tangent_offset < -math.pi:
            tangent_offset += 2 * math.pi
    else:
        tangent_offset = 0

    # Sallanma yönü: İtme yönünün TERSİ (kürek fiziği)
    # Kürek suyu GERİYE iter → tekne İLERİ gider
    # Power stroke'ta kürek itme yönüne (geriye) uzanır
    # Görsel: thrust_dir yönüne sallan (suyu o yöne itiyor)
    swing_direction = -1 if tangent_offset >= 0 else 1

    # Keskin dönüşte karşı taraf TERSİNE kürek çeker
    # reverse_stroke=True: Kürek İLERİYE gider (tekneyi döndürmek için)
    if reverse_stroke:
        swing_direction = -swing_direction

    effective_length = length * extension

    if is_power_stroke:
        # POWER STROKE: İtme yönüne doğru sallanma
        line_width = max(2, int(3 * power_boost))
        brightness = min(1.4, 0.8 + 0.4 * power_boost)
        tip_color = tuple(min(255, int(c * brightness)) for c in color)

        # Sallanma: stroke_offset'i itme yönüne göre uygula
        # Power stroke başında max eğim, sonunda daha az
        swing_angle = swing_direction * abs(stroke_offset)
        current_angle = base_angle + swing_angle * 0.6  # Max ±36° sapma

        end_pos = organ_pos + pygame.math.Vector2(
            math.cos(current_angle), math.sin(current_angle)
        ) * effective_length

        pygame.draw.line(screen, tip_color,
                        (int(organ_pos.x), int(organ_pos.y)),
                        (int(end_pos.x), int(end_pos.y)), line_width)
    else:
        # RECOVERY STROKE: Ters yöne geri çekilme
        line_width = 1
        tip_color = tuple(max(40, int(c * 0.4)) for c in color)

        # Recovery: İtmenin tersine doğru geri dön
        swing_angle = -swing_direction * abs(stroke_offset)

        segments = 3
        points = [(int(organ_pos.x), int(organ_pos.y))]

        for i in range(1, segments + 1):
            t = i / segments
            # Uç noktaya doğru artan kıvrılma
            curl_amount = t * t * 0.5
            seg_angle = base_angle + swing_angle * 0.6 * (1.0 - curl_amount)
            seg_length = effective_length * t
            p = organ_pos + pygame.math.Vector2(
                math.cos(seg_angle), math.sin(seg_angle)
            ) * seg_length
            points.append((int(p.x), int(p.y)))

        if len(points) > 1:
            pygame.draw.lines(screen, tip_color, False, points, line_width)
