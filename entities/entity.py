import pygame
import random

# Constants
WIDTH, HEIGHT = 1200, 800
FPS = 60
SCALE = 10  # 1 unit = 10 pixels

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)

class Entity:
    def __init__(self, x, y, radius, speed, color):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = radius
        self.speed = speed
        self.color = color
        self.direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()

    def move(self, dt):
        self.pos += self.direction * self.speed * dt
        self.check_bounds()

    def check_bounds(self):
        # Default bound check - bounce off walls
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.direction.x *= -1
        elif self.pos.x + self.radius > WIDTH:
            self.pos.x = WIDTH - self.radius
            self.direction.x *= -1
        
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.direction.y *= -1
        elif self.pos.y + self.radius > HEIGHT:
            self.pos.y = HEIGHT - self.radius
            self.direction.y *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
