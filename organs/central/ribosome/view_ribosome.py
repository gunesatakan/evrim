import pygame
import math
import random

def draw_ribosome(screen, parent_pos, parent_radius, is_busy):
    # Ribozomları sitoplazma içinde dağınık küçük noktalar olarak temsil edelim
    # Meşgulse yanıp sönebilir veya renk değiştirebilir
    
    color = (200, 200, 255) if not is_busy else (255, 100, 100)
    
    # Basit bir görselleştirme: Merkeze yakın 3 küçük nokta
    # Dönme efekti ekleyelim ki canlı dursun
    time_offset = pygame.time.get_ticks() * 0.005
    
    for i in range(3):
        angle = time_offset + (i * (2 * math.pi / 3))
        dist = parent_radius * 0.3
        
        # parent_pos bir Vector2, onu (x,y) tuple yapıp int'e çevirerek kullanalım
        center_x, center_y = parent_pos.x, parent_pos.y
        
        rx = center_x + math.cos(angle) * dist
        ry = center_y + math.sin(angle) * dist
        
        pygame.draw.circle(screen, color, (int(rx), int(ry)), 2)
