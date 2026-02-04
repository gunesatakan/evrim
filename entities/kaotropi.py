import pygame
import random
import math
from entities.entity import Entity, WIDTH, HEIGHT, SCALE, RED
import entities.kaotropi_view as kaotropi_view

class Kaotropi(Entity):
    def __init__(self, uid, x, y):
        super().__init__(x, y, 3 * SCALE, 0.8 * SCALE, RED)
        self.uid = f"kaotropi_{uid}"
        self.current_path_end = self.calculate_impact_point()

    def check_bounds(self):
        # When hitting a boundary, pick a new random direction
        hit = False
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            hit = True
        elif self.pos.x + self.radius > WIDTH:
            self.pos.x = WIDTH - self.radius
            hit = True
        
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            hit = True
        elif self.pos.y + self.radius > HEIGHT:
            self.pos.y = HEIGHT - self.radius
            hit = True
        
        if hit:
            # Pick a new random direction
            angle = random.uniform(0, 2 * math.pi)
            self.direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
            self.current_path_end = self.calculate_impact_point()

    def move(self, dt):
        super().move(dt)

    def draw(self, screen):
        kaotropi_view.draw(self, screen)

    def calculate_impact_point(self):
        # Raycast to find where it hits the wall based on current direction
        t_min = float('inf')
        
        if self.direction.x > 0:
            t = (WIDTH - self.radius - self.pos.x) / self.direction.x
            t_min = min(t_min, t)
        elif self.direction.x < 0:
            t = (self.radius - self.pos.x) / self.direction.x
            t_min = min(t_min, t)
            
        if self.direction.y > 0:
            t = (HEIGHT - self.radius - self.pos.y) / self.direction.y
            t_min = min(t_min, t)
        elif self.direction.y < 0:
            t = (self.radius - self.pos.y) / self.direction.y
            t_min = min(t_min, t)
            
        impact_pos = self.pos + self.direction * t_min
        return impact_pos
