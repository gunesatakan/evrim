import pygame

def draw_cytoplasm(screen, pos, radius, color):
    """Hücrenin ana gövdesi."""
    pygame.draw.circle(screen, color, (int(pos.x), int(pos.y)), int(radius))
    # Hafif bir kenarlık/parlaklık
    pygame.draw.circle(screen, (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30)), 
                       (int(pos.x), int(pos.y)), int(radius), 2)
