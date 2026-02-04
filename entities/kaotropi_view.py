import pygame

def draw(kaotropi, screen):
    pygame.draw.circle(screen, kaotropi.color, (int(kaotropi.pos.x), int(kaotropi.pos.y)), kaotropi.radius)
