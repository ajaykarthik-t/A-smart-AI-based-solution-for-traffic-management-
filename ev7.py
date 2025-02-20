import pygame
import sys
import time

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Traffic Signal Simulator")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# Traffic light states
LIGHT_RED = 0
LIGHT_YELLOW = 1
LIGHT_GREEN = 2

class Car:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed
        self.width = 60
        self.height = 30
        self.color = (0, 0, 255)  # Blue car
        self.stopped = False

    def move(self, light_state):
        # Stop the car if the light is red or yellow and car is near the light
        if (light_state == LIGHT_RED or light_state == LIGHT_YELLOW) and 450 <= self.x <= 520:
            self.stopped = True
        else:
            self.stopped = False
            
        if not self.stopped:
            self.x += self.speed
            
        # Reset position when car moves off screen
        if self.x > WIDTH + 100:
            self.x = -self.width - 50

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Draw car windows
        pygame.draw.rect(screen, (200, 200, 255), (self.x + 10, self.y + 5, 15, 20))
        pygame.draw.rect(screen, (200, 200, 255), (self.x + 35, self.y + 5, 15, 20))

class TrafficLight:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = LIGHT_RED
        self.timer = 0
        self.auto_mode = True
        
    def update(self):
        if self.auto_mode:
            self.timer += 1
            
            # State transitions
            if self.state == LIGHT_RED and self.timer >= 100:
                self.state = LIGHT_GREEN
                self.timer = 0
            elif self.state == LIGHT_GREEN and self.timer >= 80:
                self.state = LIGHT_YELLOW
                self.timer = 0
            elif self.state == LIGHT_YELLOW and self.timer >= 30:
                self.state = LIGHT_RED
                self.timer = 0
    
    def set_red(self):
        self.state = LIGHT_RED
        self.timer = 0
        
    def set_green(self):
        self.state = LIGHT_GREEN
        self.timer = 0
    
    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
        
    def draw(self, screen):
        # Draw traffic light pole
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, 20, 120))
        
        # Draw traffic light box
        pygame.draw.rect(screen, BLACK, (self.x - 15, self.y - 80, 50, 100), border_radius=10)
        
        # Draw red light
        red_color = RED if self.state == LIGHT_RED else (50, 0, 0)
        pygame.draw.circle(screen, red_color, (self.x + 10, self.y - 60), 15)
        
        # Draw yellow light
        yellow_color = YELLOW if self.state == LIGHT_YELLOW else (50, 50, 0)
        pygame.draw.circle(screen, yellow_color, (self.x + 10, self.y - 30), 15)
        
        # Draw green light
        green_color = GREEN if self.state == LIGHT_GREEN else (0, 50, 0)
        pygame.draw.circle(screen, green_color, (self.x + 10, self.y - 0), 15)

def draw_road():
    # Draw road
    pygame.draw.rect(screen, DARK_GRAY, (0, 300, WIDTH, 100))
    
    # Draw lane markings
    for i in range(0, WIDTH, 50):
        pygame.draw.rect(screen, WHITE, (i, 350, 30, 5))

def draw_buttons():
    # Red button
    red_button = pygame.draw.rect(screen, (200, 0, 0), (50, 500, 100, 50), border_radius=10)
    font = pygame.font.SysFont(None, 24)
    text = font.render("Set RED", True, WHITE)
    screen.blit(text, (70, 515))
    
    # Green button
    green_button = pygame.draw.rect(screen, (0, 200, 0), (200, 500, 100, 50), border_radius=10)
    text = font.render("Set GREEN", True, WHITE)
    screen.blit(text, (210, 515))
    
    # Auto toggle button
    auto_color = (0, 200, 200) if traffic_light.auto_mode else (200, 200, 0)
    auto_button = pygame.draw.rect(screen, auto_color, (350, 500, 150, 50), border_radius=10)
    auto_text = "AUTO Mode: ON" if traffic_light.auto_mode else "AUTO Mode: OFF"
    text = font.render(auto_text, True, BLACK)
    screen.blit(text, (360, 515))
    
    return red_button, green_button, auto_button

# Create traffic light
traffic_light = TrafficLight(500, 350)

# Create cars
cars = []
for i in range(3):
    cars.append(Car(-200 - i * 200, 320, 2 + i * 0.5))

# Main game loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            red_button, green_button, auto_button = draw_buttons()  # Get button rectangles
            
            if red_button.collidepoint(mouse_pos):
                traffic_light.auto_mode = False
                traffic_light.set_red()
            elif green_button.collidepoint(mouse_pos):
                traffic_light.auto_mode = False
                traffic_light.set_green()
            elif auto_button.collidepoint(mouse_pos):
                traffic_light.toggle_auto_mode()
    
    # Update
    traffic_light.update()
    for car in cars:
        car.move(traffic_light.state)
    
    # Draw
    screen.fill(WHITE)
    
    # Draw sky
    pygame.draw.rect(screen, (135, 206, 235), (0, 0, WIDTH, 300))
    
    # Draw grass
    pygame.draw.rect(screen, (34, 139, 34), (0, 250, WIDTH, 50))
    pygame.draw.rect(screen, (34, 139, 34), (0, 400, WIDTH, 100))
    
    # Draw road and traffic elements
    draw_road()
    traffic_light.draw(screen)
    
    # Draw cars
    for car in cars:
        car.draw(screen)
    
    # Draw instructions
    font = pygame.font.SysFont(None, 32)
    title = font.render("Traffic Signal Simulator", True, BLACK)
    screen.blit(title, (WIDTH//2 - 150, 20))
    
    font = pygame.font.SysFont(None, 24)
    red_text = font.render("RED: Stop", True, RED)
    screen.blit(red_text, (20, 70))
    
    yellow_text = font.render("YELLOW: Wait", True, (150, 150, 0))
    screen.blit(yellow_text, (20, 100))
    
    green_text = font.render("GREEN: Go", True, GREEN)
    screen.blit(green_text, (20, 130))
    
    # Draw control buttons
    draw_buttons()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()