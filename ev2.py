import pygame
import time
import random
import math
from enum import Enum
from typing import List, Dict, Tuple
import sys

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
    'bus': (80, 30)  # Added a new vehicle type for more realism
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
INFO_FONT = pygame.font.Font(None, 18)  # New font for additional info

class Direction(Enum):
    NORTH = 0
    SOUTH = 180
    EAST = 90
    WEST = 270

class VehicleType(Enum):
    CAR = 'car'
    TRUCK = 'truck'
    BIKE = 'bike'
    BUS = 'bus'  # Added bus type

class Vehicle:
    def __init__(self, direction: Direction):
        self.direction = direction
        self.type = random.choice(list(VehicleType))
        self.size = VEHICLE_SIZES[self.type.value]
        self.speed = random.uniform(3, 5)  # Adjusting speed for realism
        self.max_speed = 5  # Maximum speed
        self.acceleration = 0.1  # How fast it accelerates
        self.deceleration = 0.05  # How fast it decelerates
        
        # Random vehicle colors based on type
        if self.type == VehicleType.CAR:
            self.color = random.choice([(200,0,0), (0,0,200), (0,200,0), (200,200,0), (200,100,0)])
        elif self.type == VehicleType.TRUCK:
            self.color = random.choice([(100,100,100), (150,150,150), (80,80,80)])
        elif self.type == VehicleType.BIKE:
            self.color = random.choice([(0,0,0), (50,50,50), (100,100,100)])
        else:  # BUS
            self.color = random.choice([(255, 165, 0), (0, 0, 255), (0, 255, 255)])

        # Set initial position based on direction and lane
        offset = random.choice([-10, 10])  # Random lane offset for realism
        if direction == Direction.NORTH:
            self.position = [CENTER[0] - LANE_WIDTH//2 + offset, WINDOW_SIZE[1] + self.size[0]]
        elif direction == Direction.SOUTH:
            self.position = [CENTER[0] + LANE_WIDTH//2 + offset, -self.size[0]]
        elif direction == Direction.EAST:
            self.position = [-self.size[0], CENTER[1] - LANE_WIDTH//2 + offset]
        else:  # WEST
            self.position = [WINDOW_SIZE[0] + self.size[0], CENTER[1] + LANE_WIDTH//2 + offset]
        
        self.waiting_time = 0
        self.stop_distance = 100  # Distance to stop before the intersection

    def draw(self, screen):
        # Draw vehicle shadow
        shadow_offset = 4
        shadow_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0,0,0,64), (0, 0, *self.size))
        rotated_shadow = pygame.transform.rotate(shadow_surface, -self.direction.value)
        screen.blit(rotated_shadow, (self.position[0] - rotated_shadow.get_width()//2 + shadow_offset,
                                   self.position[1] - rotated_shadow.get_height()//2 + shadow_offset))
        
        # Draw vehicle body
        vehicle_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(vehicle_surface, self.color, (0, 0, *self.size))
        
        # Add vehicle details
        if self.type == VehicleType.CAR:
            # Windows
            window_color = (150,150,150)
            window_width = self.size[0] // 3
            pygame.draw.rect(vehicle_surface, window_color, (window_width, 2, window_width, self.size[1]-4))
        elif self.type == VehicleType.TRUCK:
            # Cab and cargo area
            pygame.draw.line(vehicle_surface, (50,50,50), (self.size[0]//3, 0), (self.size[0]//3, self.size[1]), 2)
        elif self.type == VehicleType.BUS:
            # Bus windows
            window_color = (180, 180, 180)
            window_width = self.size[0] // 4
            pygame.draw.rect(vehicle_surface, window_color, (5, 5, window_width, self.size[1] - 10))
        
        rotated = pygame.transform.rotate(vehicle_surface, -self.direction.value)
        screen.blit(rotated, (self.position[0] - rotated.get_width()//2,
                             self.position[1] - rotated.get_height()//2))

    def update(self, ns_green: bool, waiting: bool):
        # If the light is red, slow down and stop gradually
        if waiting:
            if self.speed > 0:  # Reduce speed gradually
                self.speed -= self.deceleration
            if self.speed < 0:  # Ensure speed doesn't go negative
                self.speed = 0
        elif self.speed < self.max_speed:  # Accelerate when moving
            self.speed += self.acceleration
        
        # Normal movement
        if self.direction == Direction.NORTH:
            self.position[1] -= self.speed
        elif self.direction == Direction.SOUTH:
            self.position[1] += self.speed
        elif self.direction == Direction.EAST:
            self.position[0] += self.speed
        else:  # WEST
            self.position[0] -= self.speed

    def check_if_stop(self, ns_green: bool):
        """Returns whether the vehicle should stop due to a red light."""
        if self.direction in [Direction.NORTH, Direction.SOUTH]:
            return not ns_green  # Stop if it's red
        else:
            return ns_green  # Stop if it's red for East-West traffic

class TrafficLight:
    def __init__(self, position: Tuple[int, int], direction: Direction):
        self.position = position
        self.direction = direction
        self.color = RED
        self.timer = 30
        self.box_rect = pygame.Rect(position[0]-25, position[1]-65, 50, 140)
    
    def draw(self, screen):
        # Draw traffic light box
        pygame.draw.rect(screen, (70,70,70), self.box_rect)
        pygame.draw.rect(screen, (50,50,50), self.box_rect, 3)
        
        # Draw lights
        light_colors = [RED, YELLOW, GREEN]
        for i, color in enumerate(light_colors):
            pos = (self.position[0], self.position[1] - 40 + i*40)
            # Draw light casing
            pygame.draw.circle(screen, (30,30,30), pos, 15)
            # Draw actual light (dimmed if not current color)
            light_color = color if color == self.color else tuple(x//4 for x in color)
            pygame.draw.circle(screen, light_color, pos, 12)
        
        # Draw timer
        timer_text = SMALL_FONT.render(str(self.timer), True, (255,255,255))
        text_rect = timer_text.get_rect(center=(self.position[0], self.position[1] + 60))
        screen.blit(timer_text, text_rect)

class TrafficSimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Traffic Signal Simulation")
        
        self.clock = pygame.time.Clock()
        self.vehicles = []
        
        # Position traffic lights with offset for better visibility
        light_offset = ROAD_WIDTH + 30
        self.lights = {
            Direction.NORTH: TrafficLight((CENTER[0] - light_offset, CENTER[1] - light_offset), Direction.NORTH),
            Direction.SOUTH: TrafficLight((CENTER[0] + light_offset, CENTER[1] + light_offset), Direction.SOUTH),
            Direction.EAST: TrafficLight((CENTER[0] + light_offset, CENTER[1] - light_offset), Direction.EAST),
            Direction.WEST: TrafficLight((CENTER[0] - light_offset, CENTER[1] + light_offset), Direction.WEST)
        }
        
        self.ns_green = True  # North-South will start as green
        self.start_time = pygame.time.get_ticks()  # Get the starting time
        self.cycle_duration = 120  # Total cycle duration (120 seconds)
        self.last_spawn = time.time()
        self.stats = {'crossed': 0, 'waiting': 0}
        
        # Button for manual control of traffic signal
        self.button_rect = pygame.Rect(WINDOW_SIZE[0] - 150, 50, 120, 40)

    def update_lights(self):
        # Get the elapsed time in seconds from the start of the simulation
        elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000  # Convert ms to seconds
        
        # Determine the light color based on elapsed time
        cycle_position = elapsed_time % self.cycle_duration  # Reset every 120 seconds
        
        if cycle_position < 60:
            # First 60 seconds: North-South green, East-West red
            self.ns_green = True
        else:
            # Next 60 seconds: North-South red, East-West green
            self.ns_green = False
        
        # Update traffic lights based on the cycle position
        for direction, light in self.lights.items():
            if direction in [Direction.NORTH, Direction.SOUTH]:
                light.color = GREEN if self.ns_green else RED
            else:
                light.color = RED if self.ns_green else GREEN
            light.timer = int(self.cycle_duration - cycle_position)  # Show remaining time in the cycle
    
    def spawn_vehicle(self):
        if time.time() - self.last_spawn > random.uniform(1, 2.5):
            direction = random.choice(list(Direction))
            self.vehicles.append(Vehicle(direction))
            self.last_spawn = time.time()
    
    def update_vehicles(self):
        waiting_count = 0
        for vehicle in self.vehicles[:]:
            # Check if vehicle should stop at intersection
            should_stop = vehicle.check_if_stop(self.ns_green)
            if should_stop:
                waiting_count += 1
            
            # Update vehicle's movement and speed
            vehicle.update(self.ns_green, should_stop)
            
            # Remove vehicles that have left the screen
            if (vehicle.position[0] < -100 or vehicle.position[0] > WINDOW_SIZE[0] + 100 or
                vehicle.position[1] < -100 or vehicle.position[1] > WINDOW_SIZE[1] + 100):
                self.vehicles.remove(vehicle)
                self.stats['crossed'] += 1
        
        self.stats['waiting'] = waiting_count
    
    def draw_road_markings(self):
        # Draw zebra crossings
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
        
        # Draw stop lines
        stop_line_width = 8
        pygame.draw.rect(self.screen, MARKING_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2, CENTER[1] - ROAD_WIDTH//2 - stop_line_width,
                         ROAD_WIDTH, stop_line_width))
        pygame.draw.rect(self.screen, MARKING_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2, CENTER[1] + ROAD_WIDTH//2,
                         ROAD_WIDTH, stop_line_width))
        
        # Draw lane dividers
        dash_length = 20
        gap_length = 20
        # Vertical road
        y = 0
        while y < WINDOW_SIZE[1]:
            if abs(y - CENTER[1]) > ROAD_WIDTH//2:
                pygame.draw.rect(self.screen, YELLOW_MARKING,
                               (CENTER[0], y, 2, dash_length))
            y += dash_length + gap_length
        
        # Horizontal road
        x = 0
        while x < WINDOW_SIZE[0]:
            if abs(x - CENTER[0]) > ROAD_WIDTH//2:
                pygame.draw.rect(self.screen, YELLOW_MARKING,
                               (x, CENTER[1], dash_length, 2))
            x += dash_length + gap_length

    def draw(self):
        # Fill background with grass
        self.screen.fill(GRASS_COLOR)
        
        # Draw roads
        pygame.draw.rect(self.screen, ROAD_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2, 0, ROAD_WIDTH, WINDOW_SIZE[1]))
        pygame.draw.rect(self.screen, ROAD_COLOR,
                        (0, CENTER[1] - ROAD_WIDTH//2, WINDOW_SIZE[0], ROAD_WIDTH))
        
        # Draw sidewalks
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (CENTER[0] - ROAD_WIDTH//2 - 30, 0, 30, WINDOW_SIZE[1]))
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (CENTER[0] + ROAD_WIDTH//2, 0, 30, WINDOW_SIZE[1]))
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (0, CENTER[1] - ROAD_WIDTH//2 - 30, WINDOW_SIZE[0], 30))
        pygame.draw.rect(self.screen, SIDEWALK_COLOR,
                        (0, CENTER[1] + ROAD_WIDTH//2, WINDOW_SIZE[0], 30))
        
        # Draw road markings
        self.draw_road_markings()
        
        # Draw traffic lights
        for light in self.lights.values():
            light.draw(self.screen)
        
        # Update vehicle positions and draw them
        self.update_vehicles()
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)
        
        # Draw stats
        stats_text = INFO_FONT.render(f"Crossed: {self.stats['crossed']} | Waiting: {self.stats['waiting']}", True, BLACK)
        self.screen.blit(stats_text, (10, 10))
        
        # Draw the button for manual signal control
        pygame.draw.rect(self.screen, (0, 0, 255), self.button_rect)
        button_text = FONT.render("Manually Control", True, (255, 255, 255))
        self.screen.blit(button_text, (self.button_rect.centerx - button_text.get_width()//2, self.button_rect.centery - button_text.get_height()//2))
        
        pygame.display.flip()  # Update the screen with the new frame

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
                        self.ns_green = not self.ns_green  # Toggle between NS Green and EW Green
            
            self.draw()
            self.clock.tick(60)  # 60 frames per second
        
        pygame.quit()
        sys.exit()

# Run simulation
sim = TrafficSimulation()
sim.run()
