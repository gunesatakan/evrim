import pygame

def get_auditory_reflex_direction(observer_pos, source_pos):
    """
    Tehdit duyulduğunda ama görülmediğinde (İşitsel Refleks):
    Sesin geldiği kaynağın tam tersi yöne (180 derece) kaçış yönünü hesaplar.
    
    Args:
        observer_pos (Vector2): Kaçacak olanın konumu.
        source_pos (Vector2): Ses kaynağının konumu.
        
    Returns:
        Vector2: Kaçış yönü vektörü (normalize).
    """
    to_source = source_pos - observer_pos
    if to_source.length() > 0:
        return -to_source.normalize()
    else:
        # Eğer tam üst üstelerse rastgele bir yere git
        return pygame.math.Vector2(1, 0)
