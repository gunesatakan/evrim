import pygame
import math

def draw_flagella(screen, pos, direction, radius, color, length, is_shutdown=False, boost=1.0,
                  attachment_angle=math.pi, thrust_angle=math.pi, show_thrust_vector=False,
                  olcek=1.0):
    """Kamçıyı çiz: kökten uca doğru KIVRILAN, dalgalanan bir kuyruk.

    Eskiden kamçı DÜZ bir ışındı ve sapma onu kökünden bütün olarak
    döndürüyordu; zar üzerinde keskin bir kırık oluşuyor, dönerken kamçının
    kıvrıldığı görülmüyordu. Gerçekte kamçı tabanından bükülür: kök zara dik
    çıkar, gövde boyunca yavaşça itme yönüne döner.

    Bunun için ayrı bir "kıvrım" durumu tutmuyoruz - işaretli sapma zaten
    `thrust_angle - attachment_angle` farkında var ve motor mantığı onu
    yumuşatarak (8 rad/s) taşıyor. Yani kıvrım fizikle kendiliğinden
    senkron: hangi tarafa tork üretiliyorsa kamçı o tarafa kıvrılır.
    """
    if direction.length() == 0:
        return

    dir_angle = math.atan2(direction.y, direction.x)

    # Kök: hücrenin kenarında, ATTACHMENT açısında (fiziksel tutunma noktası)
    world_attachment_angle = dir_angle + attachment_angle
    attachment_dir = pygame.math.Vector2(math.cos(world_attachment_angle),
                                         math.sin(world_attachment_angle))
    start_pos = pos + attachment_dir * radius

    # Kıvrım miktarı: kökün yönü ile itme yönü arasındaki işaretli fark.
    kivrim = (thrust_angle - attachment_angle + math.pi) % (2 * math.pi) - math.pi

    segments = 10
    seg_len = (length / segments)
    t = 0 if is_shutdown else (pygame.time.get_ticks() / 100.0) * boost

    points = [start_pos]
    p = pygame.math.Vector2(start_pos)
    for i in range(1, segments + 1):
        pw = i / segments
        # Bükülme kökte yoğun, uçta biter: smoothstep. Uç, itme yönüne
        # oturur - fizik de o yönü kullandığı için ikisi ayrışmaz.
        e = pw * pw * (3 - 2 * pw)
        ang = world_attachment_angle + kivrim * e
        yon = pygame.math.Vector2(math.cos(ang), math.sin(ang))
        p = p + yon * seg_len
        # Dalga: gövdeye dik, uca doğru büyüyen genlik
        perp = pygame.math.Vector2(-yon.y, yon.x)
        amp = 0 if is_shutdown else 2.0 * pw * olcek
        points.append(p + perp * math.sin(t + pw * 10) * amp)

    if len(points) > 1:
        pygame.draw.lines(screen, color, False, points,
                          max(1, int(round(olcek))))
