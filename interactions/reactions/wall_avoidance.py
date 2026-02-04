import pygame

def get_wall_avoidance_direction(observer_pos, wall_data):
    """
    Duvara yakınlık durumunda kaçınma yönü hesaplar.
    Tehdit değil, sadece mantıksız bir yön olarak işaretler.

    Args:
        observer_pos (Vector2): Organizmanın pozisyonu
        wall_data (dict): Duvar bilgileri
            - 'walls': Görünen duvarların listesi ('left', 'right', 'top', 'bottom')
            - 'distances': Her duvara olan mesafe

    Returns:
        Vector2: Kaçınma yönü (normalize edilmiş) veya None
    """
    if not wall_data or not wall_data.get('walls'):
        return None

    walls = wall_data['walls']
    distances = wall_data['distances']

    # Kaçınma vektörünü hesapla (duvarlardan uzaklaşma)
    avoid_dir = pygame.math.Vector2(0, 0)

    for wall in walls:
        dist = distances.get(wall, 0)
        if dist <= 0:
            continue

        # Mesafeye ters orantılı güç (yakın duvar = güçlü itme)
        strength = 1.0 / max(dist, 1)

        if wall == 'left':
            avoid_dir.x += strength  # Sağa it
        elif wall == 'right':
            avoid_dir.x -= strength  # Sola it
        elif wall == 'top':
            avoid_dir.y += strength  # Aşağı it
        elif wall == 'bottom':
            avoid_dir.y -= strength  # Yukarı it

    if avoid_dir.length() > 0:
        return avoid_dir.normalize()

    return None
