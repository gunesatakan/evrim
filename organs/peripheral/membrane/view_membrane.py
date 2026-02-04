import pygame

def draw_calcium_aura(screen, pos, radius, boost):
    """Kalsiyum patlamasını hücre etrafında parlama olarak çizer."""
    if boost <= 1.1: return
    
    # Boost 1.0 -> 3.0 iken parlaklık ve genişlik artar
    intensity = int(min(255, (boost - 1.0) * 100))
    aura_radius = int(radius + (boost - 1.0) * 5)
    
    s = pygame.Surface((aura_radius*2, aura_radius*2), pygame.SRCALPHA)
    # Beyaz/Mavi arası bir parlama
    pygame.draw.circle(s, (255, 255, 255, intensity // 2), (aura_radius, aura_radius), aura_radius, 2)
    screen.blit(s, (int(pos.x - aura_radius), int(pos.y - aura_radius)))
