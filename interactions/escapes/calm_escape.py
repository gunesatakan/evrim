import pygame

def get_calm_escape_direction(observer_pos, threat_pos):
    """
    Sakin Kaçış (Calm Escape):
    Tehdit uzaktayken veya aciliyet yokken, tehditten direkt uzaklaşma vektörü.
    
    Args:
        observer_pos (Vector2): Kaçacak olanın konumu.
        threat_pos (Vector2): Tehdidin konumu.
        
    Returns:
        Vector2: Uzaklaşma yönü (normalize).
    """
    escape_vec = observer_pos - threat_pos
    if escape_vec.length() > 0:
        return escape_vec.normalize()
    return pygame.math.Vector2(0, 0)
