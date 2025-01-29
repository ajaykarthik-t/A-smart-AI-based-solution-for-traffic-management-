import pygame
import time
import random
import sys
from enum import Enum
from typing import List, Dict, Tuple

# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = (1024, 768)
ROAD_WIDTH = 120
LANE_WIDTH = ROAD_WIDTH // 2
CENTER = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
VEHICLE_SIZES = {
    'car': (40, 20),
    'truck': (60, 24),
    'bike': (30, 15),
    'bus': (80, 30)
}
GRASS_COLOR = (34, 139, 34)
ROAD_COLOR = (50, 50, 50)
MARKING_COLOR = (255, 255, 255)
YELLOW_MARKING = (255, 255, 0)
SIDEWALK_COLOR = (180, 180, 180)
BLACK = (0, 0, 0)
RED = (255, 30, 30)
GREEN = (30, 255, 30)
YELLOW = (255, 255, 30)

# Fonts
FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 24)
INFO_FONT = pygame.font.Font(None, 18)

class Direction(Enum):
    NORTH = 0
    SOUTH = 180
    EAST = 90
    WEST = 270

class VehicleType(Enum):
    CAR = 'car'
    TRUCK = 'truck'
    BIKE = 'bike'
    BUS = 'bus'

class Vehicle:
    def __init__(self, direction: Direction):
        self.direction = direction
        self.type = random.choice(list(VehicleType))
        self.size = VEHICLE_SIZES[self.type.value]
        self.speed = random.uniform(3, 5)
        self.max_speed = 5
        self.acceleration = 0.1
        self.deceleration = 0.05
        
        if self.type == VehicleType.CAR:
            self.color = random.choice([(200,0,0), (0,0,200), (0,200,0), (200,200,0), (200,100,0)])
        elif self.type == VehicleType.TRUCK:
            self.color = random.choice([(100,100,100), (150,150,150), (80,80,80)])
        elif self.type == VehicleType.BIKE:
            self.color = random.choice([(0,0,0), (50,50,50), (100,100,100)])
        else:  # BUS
            self.color = random.choice([(255, 165, 0), (0, 0, 255), (0, 255, 255)])

        offset = random.choice([-10, 10])
        if direction == Direction.NORTH:
            self.position = [CENTER[0] - LANE_WIDTH//2 + offset, WINDOW_SIZE[1] + self.size[0]]
        elif direction == Direction.SOUTH:
            self.position = [CENTER[0] + LANE_WIDTH//2 + offset, -self.size[0]]
        elif direction == Direction.EAST:
            self.position = [-self.size[0], CENTER[1] - LANE_WIDTH//2 + offset]
        else:  # WEST
            self.position = [WINDOW_SIZE[0] + self.size[0], CENTER[1] + LANE_WIDTH//2 + offset]
        
        self.waiting_time = 0
        self.stop_distance = 100

    def draw(self, screen):
        shadow_offset = 4
        shadow_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0,0,0,64), (0, 0, *self.size))
        rotated_shadow = pygame.transform.rotate(shadow_surface, -self.direction.value)
        screen.blit(rotated_shadow, (self.position[0] - rotated_shadow.get_width()//2 + shadow_offset,
                                   self.position[1] - rotated_shadow.get_height()//2 + shadow_offset))
        
        vehicle_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(vehicle_surface, self.color, (0, 0, *self.size))
        
        rotated = pygame.transform.rotate(vehicle_surface, -self.direction.value)
        screen.blit(rotated, (self.position[0] - rotated.get_width()//2,
                             self.position[1] - rotated.get_height()//2))

    def update(self, ns_green: bool, waiting: bool):
        if waiting:
            if self.speed > 0:
                self.speed -= self.deceleration
            if self.speed < 0:
                self.speed = 0
        elif self.speed < self.max_speed:
            self.speed += self.acceleration
        
        if self.direction == Direction.NORTH:
            self.position[1] -= self.speed
        elif self.direction == Direction.SOUTH:
            self.position[1] += self.speed
        elif self.direction == Direction.EAST:
            self.position[0] += self.speed
        else:  # WEST
            self.position[0] -= self.speed

    def check_if_stop(self, ns_green: bool):
        if self.direction in [Direction.NORTH, Direction.SOUTH]:
            return not ns_green
        else:
            return ns_green

class TrafficLight:
    def __init__(self, position: Tuple[int, int], direction: Direction):
        self.position = position
        self.direction = direction
        self.color = RED
        self.timer = 30
        self.box_rect = pygame.Rect(position[0]-25, position[1]-65, 50, 140)
    
    def draw(self, screen):
        pygame.draw.rect(screen, (70,70,70), self.box_rect)
        pygame.draw.rect(screen, (50,50,50), self.box_rect, 3)
        
        light_colors = [RED, YELLOW, GREEN]
        for i, color in enumerate(light_colors):
            pos = (self.position[0], self.position[1] - 40 + i*40)
            pygame.draw.circle(screen, (30,30,30), pos, 15)
            light_color = color if color == self.color else tuple(x//4 for x in color)
            pygame.draw.circle(screen, light_color, pos, 12)
        
        timer_text = SMALL_FONT.render(str(self.timer), True, (255,255,255))
        text_rect = timer_text.get_rect(center=(self.position[0], self.position[1] + 60))
        screen.blit(timer_text, text_rect)

class TrafficSimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Traffic Signal Simulation")
        
        self.clock = pygame.time.Clock()
        self.vehicles = []
        
        light_offset = ROAD_WIDTH + 30
        self.lights = {
            Direction.NORTH: TrafficLight((CENTER[0] - light_offset, CENTER[1] - light_offset), Direction.NORTH),
            Direction.SOUTH: TrafficLight((CENTER[0] + light_offset, CENTER[1] + light_offset), Direction.SOUTH),
            Direction.EAST: TrafficLight((CENTER[0] + light_offset, CENTER[1] - light_offset), Direction.EAST),
            Direction.WEST: TrafficLight((CENTER[0] - light_offset, CENTER[1] + light_offset), Direction.WEST)
        }
        
        self.ns_green = True  # North-South starts green
        self.last_spawn = time.time()
        
        # Button for manual control of traffic signal
        self.button_rect = pygame.Rect(WINDOW_SIZE[0] - 150, 50, 120, 40)
        
        # Input box for signal number
        self.signal_input_rect = pygame.Rect(WINDOW_SIZE[0] - 300, 120, 150, 40)
        self.signal_number = ""

    def update_lights(self):
        if self.ns_green:
            for direction in [Direction.NORTH, Direction.SOUTH]:
                self.lights[direction].color = GREEN
            for direction in [Direction.EAST, Direction.WEST]:
                self.lights[direction].color = RED
        else:
            for direction in [Direction.NORTH, Direction.SOUTH]:
                self.lights[direction].color = RED
            for direction in [Direction.EAST, Direction.WEST]:
                self.lights[direction].color = GREEN

    def spawn_vehicle(self):
        if time.time() - self.last_spawn > random.uniform(1, 2.5):
            direction = random.choice(list(Direction))
            self.vehicles.append(Vehicle(direction))
            self.last_spawn = time.time()
    
    def update_vehicles(self):
        for vehicle in self.vehicles[:]:
            should_stop = vehicle.check_if_stop(self.ns_green)
            vehicle.update(self.ns_green, should_stop)
            
            if (vehicle.position[0] < -100 or vehicle.position[0] > WINDOW_SIZE[0] + 100 or
                vehicle.position[1] < -100 or vehicle.position[1] > WINDOW_SIZE[1] + 100):
                self.vehicles.remove(vehicle)
        
    def draw_road_markings(self):
        crossing_width = 40
        stripe_width = 8
        for x in range(CENTER[0] - ROAD_WIDTH//2 - crossing_width, 
                      CENTER[0] - ROAD_WIDTH//2):
            pygame.draw.rect(self.screen, MARKING_COLOR,
                           (x, CENTER[1] - ROAD_WIDTH//2, stripe_width, ROAD_WIDTH))
        for x in range(CENTER[0] + ROAD_WIDTH//2, 
                      CENTER[0] + ROAD_WIDTH//2 + crossing_width):
            pygame.draw.rect(self.screen, MARKING_COLOR,
                           (x, CENTER[1] - ROAD_WIDTH//2, stripe_width, ROAD_WIDTH))
        
        stop_line_width = 8
        pygame.draw.rect(self.screen, MARKING_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2, CENTER[1] - ROAD_WIDTH//2 - stop_line_width,
                         ROAD_WIDTH, stop_line_width))
        pygame.draw.rect(self.screen, MARKING_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2, CENTER[1] + ROAD_WIDTH//2,
                         ROAD_WIDTH, stop_line_width))
        
        dash_length = 20
        gap_length = 20
        y = 0
        while y < WINDOW_SIZE[1]:
            if abs(y - CENTER[1]) > ROAD_WIDTH//2:
                pygame.draw.rect(self.screen, YELLOW_MARKING,
                               (CENTER[0], y, 2, dash_length))
            y += dash_length + gap_length
        
        x = 0
        while x < WINDOW_SIZE[0]:
            if abs(x - CENTER[0]) > ROAD_WIDTH//2:
                pygame.draw.rect(self.screen, YELLOW_MARKING,
                               (x, CENTER[1], dash_length, 2))
            x += dash_length + gap_length

    def draw(self):
        self.screen.fill(GRASS_COLOR)
        
        pygame.draw.rect(self.screen, ROAD_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2, 0, ROAD_WIDTH, WINDOW_SIZE[1]))
        pygame.draw.rect(self.screen, ROAD_COLOR,
                        (0, CENTER[1] - ROAD_WIDTH//2, WINDOW_SIZE[0], ROAD_WIDTH))
        
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2 - 30, 0, 30, WINDOW_SIZE[1]))
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (CENTER[0] + ROAD_WIDTH//2, 0, 30, WINDOW_SIZE[1]))
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (0, CENTER[1] - ROAD_WIDTH//2 - 30, WINDOW_SIZE[0], 30))
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (0, CENTER[1] + ROAD_WIDTH//2, WINDOW_SIZE[0], 30))
        
        self.draw_road_markings()
        
        for light in self.lights.values():
            light.draw(self.screen)
        
        self.update_vehicles()
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)

        stats_text = INFO_FONT.render("Manual Signal Control", True, BLACK)
        self.screen.blit(stats_text, (10, 10))
        
        pygame.draw.rect(self.screen, (0, 0, 255), self.button_rect)
        button_text = FONT.render("Toggle NS", True, (255, 255, 255))
        self.screen.blit(button_text, (self.button_rect.centerx - button_text.get_width()//2, self.button_rect.centery - button_text.get_height()//2))

        # Display Signal Number Input Box
        pygame.draw.rect(self.screen, (200, 200, 200), self.signal_input_rect)
        input_text = FONT.render(self.signal_number, True, (0, 0, 0))
        self.screen.blit(input_text, (self.signal_input_rect.x + 10, self.signal_input_rect.y + 5))

        # Show entered signal number
        signal_text = INFO_FONT.render(f"Entered Signal: {self.signal_number}", True, (0, 0, 0))
        self.screen.blit(signal_text, (10, 50))
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.update_lights()
            self.spawn_vehicle()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_rect.collidepoint(event.pos):
                        self.ns_green = not self.ns_green  # Toggle the signal between NS and EW
                    elif self.signal_input_rect.collidepoint(event.pos):
                        self.signal_number = ""  # Clear the input when clicked
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.signal_number = self.signal_number[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.signal_number == "1":
                            self.ns_green = True
                        elif self.signal_number == "2":
                            self.ns_green = False
                    else:
                        if len(self.signal_number) < 1:  # Limit to 1 digit
                            self.signal_number += event.unicode
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# Run simulation
sim = TrafficSimulation()
sim.run()
