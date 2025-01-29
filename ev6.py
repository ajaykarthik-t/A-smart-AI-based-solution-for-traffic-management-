import pygame
import time
import random
import sys
import tkinter as tk
from tkinter import filedialog
from enum import Enum
from typing import List, Dict, Tuple
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Initialize Pygame
pygame.init()

# Initialize tkinter for file dialog
root = tk.Tk()
root.withdraw()

# Constants
WINDOW_SIZE = (1024, 768)
ROAD_WIDTH = 120
LANE_WIDTH = ROAD_WIDTH // 2
CENTER = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
VEHICLE_SIZES = {
    'car': (40, 20),
    'truck': (60, 24),
    'bike': (30, 15),
    'bus': (80, 30),
    'ambulance': (50, 25)
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
HOSPITAL_POS = (100, 100)  # Position of hospital

# Fonts
FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 24)
INFO_FONT = pygame.font.Font(None, 18)

# Load emergency vehicle detection model
EMERGENCY_MODEL = load_model('my_model.keras')

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
    AMBULANCE = 'ambulance'

class Vehicle:
    def __init__(self, direction: Direction, is_emergency=False):
        self.direction = direction
        self.is_emergency = is_emergency
        self.type = VehicleType.AMBULANCE if is_emergency else random.choice(list(VehicleType))
        self.size = VEHICLE_SIZES[self.type.value]
        self.speed = random.uniform(5, 7) if is_emergency else random.uniform(3, 5)
        self.max_speed = 7 if is_emergency else 5
        self.acceleration = 0.2 if is_emergency else 0.1
        self.deceleration = 0.1 if is_emergency else 0.05
        self.original_direction = direction
        
        if self.is_emergency:
            self.color = (255, 0, 0)
            self.siren_color = (255, 255, 255)
            self.siren_phase = 0
        else:
            self.color = random.choice([(200,0,0), (0,0,200), (0,200,0), (200,200,0), (200,100,0)])
            if self.type == VehicleType.TRUCK:
                self.color = random.choice([(100,100,100), (150,150,150), (80,80,80)])
            elif self.type == VehicleType.BIKE:
                self.color = random.choice([(0,0,0), (50,50,50), (100,100,100)])
            elif self.type == VehicleType.BUS:
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
        self.override_signal = False

    def draw(self, screen):
        # Draw siren for emergency vehicles
        if self.is_emergency:
            siren_rect = (self.position[0] - self.size[0]//2, 
                        self.position[1] - self.size[1]//2,
                        self.size[0], self.size[1]//4)
            pygame.draw.rect(screen, self.siren_color if self.siren_phase else (255, 0, 0), siren_rect)
            self.siren_phase = not self.siren_phase

        vehicle_surface = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(vehicle_surface, self.color, (0, 0, *self.size))
        
        rotated = pygame.transform.rotate(vehicle_surface, -self.direction.value)
        screen.blit(rotated, (self.position[0] - rotated.get_width()//2,
                             self.position[1] - rotated.get_height()//2))

    def update(self, ns_green: bool, waiting: bool):
        if self.is_emergency and self.override_signal:
            waiting = False
            self.speed = self.max_speed

        if waiting:
            if self.speed > 0:
                self.speed -= self.deceleration
            if self.speed < 0:
                self.speed = 0
        elif self.speed < self.max_speed:
            self.speed += self.acceleration
        
        # Emergency vehicles heading to hospital
        if self.is_emergency:
            target_x, target_y = HOSPITAL_POS
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            
            # Change direction if needed
            if abs(dx) > abs(dy):
                self.direction = Direction.EAST if dx > 0 else Direction.WEST
            else:
                self.direction = Direction.SOUTH if dy > 0 else Direction.NORTH

        if self.direction == Direction.NORTH:
            self.position[1] -= self.speed
        elif self.direction == Direction.SOUTH:
            self.position[1] += self.speed
        elif self.direction == Direction.EAST:
            self.position[0] += self.speed
        else:  # WEST
            self.position[0] -= self.speed

    def check_if_stop(self, ns_green: bool):
        if self.is_emergency:
            return False  # Emergency vehicles don't stop
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
        self.emergency_override = False
    
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
        pygame.display.set_caption("Smart Traffic Simulation")
        
        self.clock = pygame.time.Clock()
        self.vehicles = []
        self.emergency_vehicles = []
        
        light_offset = ROAD_WIDTH + 30
        self.lights = {
            Direction.NORTH: TrafficLight((CENTER[0] - light_offset, CENTER[1] - light_offset), Direction.NORTH),
            Direction.SOUTH: TrafficLight((CENTER[0] + light_offset, CENTER[1] + light_offset), Direction.SOUTH),
            Direction.EAST: TrafficLight((CENTER[0] + light_offset, CENTER[1] - light_offset), Direction.EAST),
            Direction.WEST: TrafficLight((CENTER[0] - light_offset, CENTER[1] + light_offset), Direction.WEST)
        }
        
        self.ns_green = True
        self.last_spawn = time.time()
        self.button_rect = pygame.Rect(WINDOW_SIZE[0] - 150, 50, 120, 40)
        self.image_button_rect = pygame.Rect(WINDOW_SIZE[0] - 150, 150, 120, 40)
        self.image_path = None
        self.uploaded_image = None

    def detect_emergency(self, image_path):
        img = image.load_img(image_path, target_size=(224, 224))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        prediction = EMERGENCY_MODEL.predict(img_array)
        return prediction[0][0] > 0.5  # Assuming binary classification

    def update_lights(self):
        # Emergency override system
        if any(vehicle.is_emergency for vehicle in self.vehicles):
            for vehicle in self.vehicles:
                if vehicle.is_emergency:
                    if vehicle.direction in [Direction.NORTH, Direction.SOUTH]:
                        self.ns_green = True
                    else:
                        self.ns_green = False
                    break

        # Update light colors based on current state
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

    def spawn_vehicle(self, is_emergency=False, direction=None):
        if not direction:
            direction = random.choice(list(Direction))
        self.vehicles.append(Vehicle(direction, is_emergency))
        if is_emergency:
            self.emergency_vehicles.append(self.vehicles[-1])

    def update_vehicles(self):
        for vehicle in self.vehicles[:]:
            should_stop = vehicle.check_if_stop(self.ns_green)
            vehicle.update(self.ns_green, should_stop)
            
            # Remove vehicles that have left the screen
            if (vehicle.position[0] < -100 or vehicle.position[0] > WINDOW_SIZE[0] + 100 or
                vehicle.position[1] < -100 or vehicle.position[1] > WINDOW_SIZE[1] + 100):
                self.vehicles.remove(vehicle)
                if vehicle in self.emergency_vehicles:
                    self.emergency_vehicles.remove(vehicle)

    def draw_road_markings(self):
        # Draw crosswalk markings
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
        
        self.draw_road_markings()
        
        # Draw traffic lights
        for light in self.lights.values():
            light.draw(self.screen)
        
        # Update and draw vehicles
        self.update_vehicles()
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)

        # Draw hospital
        pygame.draw.rect(self.screen, (255, 255, 255), (*HOSPITAL_POS, 50, 50))
        hospital_text = FONT.render("H", True, (255, 0, 0))
        self.screen.blit(hospital_text, (HOSPITAL_POS[0]+15, HOSPITAL_POS[1]+10))

        # Draw UI elements
        stats_text = INFO_FONT.render("Manual Signal Control", True, BLACK)
        self.screen.blit(stats_text, (10, 10))
        
        # Draw control buttons
        pygame.draw.rect(self.screen, (0, 0, 255), self.button_rect)
        button_text = FONT.render("Toggle NS", True, (255, 255, 255))
        self.screen.blit(button_text, (self.button_rect.centerx - button_text.get_width()//2, 
                                     self.button_rect.centery - button_text.get_height()//2))

        pygame.draw.rect(self.screen, (255, 165, 0), self.image_button_rect)
        upload_button_text = FONT.render("Upload Image", True, (255, 255, 255))
        self.screen.blit(upload_button_text, (self.image_button_rect.centerx - upload_button_text.get_width()//2,
                                            self.image_button_rect.centery - upload_button_text.get_height()//2))

        if self.uploaded_image:
            self.screen.blit(self.uploaded_image, (WINDOW_SIZE[0] - 180, 200))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.update_lights()
            
            # Auto-spawn regular vehicles
            if time.time() - self.last_spawn > random.uniform(1, 2.5):
                self.spawn_vehicle()
                self.last_spawn = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_rect.collidepoint(event.pos):
                        self.ns_green = not self.ns_green
                    if self.image_button_rect.collidepoint(event.pos):
                        file_path = filedialog.askopenfilename()
                        if file_path:
                            try:
                                is_emergency = self.detect_emergency(file_path)
                                direction = random.choice(list(Direction))
                                self.spawn_vehicle(is_emergency, direction)
                                self.uploaded_image = pygame.image.load(file_path)
                            except Exception as e:
                                print(f"Error loading image: {e}")
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    sim = TrafficSimulation()
    sim.run()