import pygame

def get_trail_escape_direction(trail_start, trail_end):
    """
    Koku/İzden Kaçış (Trail Escape):
    Tespit edilen bir koku rotasının (trail) gidiş yönünün TAM TERSİNE kaçış.
    
    Args:
        trail_start (Vector2): İzin başlangıcı.
        trail_end (Vector2): İzin tahmini bitişi.
        
    Returns:
        Vector2: Kaçış yönü (normalize).
    """
    trail_vec = trail_end - trail_start
    if trail_vec.length() > 0:
        # Rotanin TAM TERSINE kos (Run Opposite)
        route_dir = trail_vec.normalize()
        return -route_dir
    return pygame.math.Vector2(0, 0)
