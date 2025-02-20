import pygame
import sys
import time
import numpy as np
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import tkinter as tk
from tkinter import filedialog
from PIL import Image

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ML Traffic Signal Simulator")

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

# Initialize ML model
try:
    model = load_model('my_model.keras')
    model_loaded = True
    print("ML model loaded successfully!")
except Exception as e:
    model_loaded = False
    print(f"Couldn't load ML model: {e}")
    print("Simulator will run without ML capabilities")

class Car:
    def __init__(self, x, y, speed, is_emergency=False):
        self.x = x
        self.y = y
        self.speed = speed
        self.width = 60
        self.height = 30
        self.color = (255, 0, 0) if is_emergency else (0, 0, 255)  # Red for emergency, blue for normal
        self.stopped = False
        self.is_emergency = is_emergency

    def move(self, light_state):
        # Emergency vehicles don't stop at red lights
        if self.is_emergency:
            self.x += self.speed
        else:
            # Normal cars stop if the light is red or yellow and car is near the light
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
        window_color = (200, 200, 255) if not self.is_emergency else (255, 200, 200)
        pygame.draw.rect(screen, window_color, (self.x + 10, self.y + 5, 15, 20))
        pygame.draw.rect(screen, window_color, (self.x + 35, self.y + 5, 15, 20))
        
        # Draw emergency lights if it's an emergency vehicle
        if self.is_emergency:
            if pygame.time.get_ticks() % 1000 < 500:  # Blinking effect
                pygame.draw.circle(screen, (0, 0, 255), (self.x + 10, self.y), 5)  # Blue light
                pygame.draw.circle(screen, (255, 0, 0), (self.x + 50, self.y), 5)  # Red light

class TrafficLight:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = LIGHT_RED
        self.timer = 0
        self.auto_mode = True
        self.emergency_override = False
        self.override_time = 0
        
    def update(self):
        # Handle emergency override
        if self.emergency_override:
            self.state = LIGHT_GREEN
            if pygame.time.get_ticks() - self.override_time > 5000:  # 5 seconds override
                self.emergency_override = False
                self.timer = 0
                return
        
        # Regular updates in auto mode
        if self.auto_mode and not self.emergency_override:
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
        if not self.emergency_override:
            self.state = LIGHT_RED
            self.timer = 0
        
    def set_green(self):
        self.state = LIGHT_GREEN
        self.timer = 0
    
    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
    
    def emergency_detected(self):
        if self.state == LIGHT_RED:
            self.emergency_override = True
            self.state = LIGHT_GREEN
            self.override_time = pygame.time.get_ticks()
            return True
        return False
        
    def draw(self, screen):
        # Draw traffic light pole
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, 20, 120))
        
        # Draw traffic light box
        light_box_color = BLACK
        if self.emergency_override:
            # Make the light box flash when in emergency override
            if pygame.time.get_ticks() % 1000 < 500:
                light_box_color = (100, 0, 0)
        
        pygame.draw.rect(screen, light_box_color, (self.x - 15, self.y - 80, 50, 100), border_radius=10)
        
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
    
    # Image upload button
    upload_button_color = (150, 100, 200) if model_loaded else (100, 100, 100)
    upload_button = pygame.draw.rect(screen, upload_button_color, (550, 500, 200, 50), border_radius=10)
    upload_text = "Upload Vehicle Image" if model_loaded else "ML Model Not Loaded"
    text = font.render(upload_text, True, WHITE)
    screen.blit(text, (565, 515))
    
    return red_button, green_button, auto_button, upload_button

def predict_vehicle_type(image_path):
    """Predict if the image contains an emergency vehicle or normal vehicle"""
    try:
        img = image.load_img(image_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0  # Normalize as in your code
        
        prediction = model.predict(img_array)
        predicted_class_index = np.argmax(prediction)
        
        class_names = ['Normal', 'Emergency Vechicle']
        predicted_class = class_names[predicted_class_index]
        
        return predicted_class, img
    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Error", None

def show_prediction_overlay(predicted_class, img=None):
    """Show prediction result overlay on the simulation"""
    # Create a semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black
    screen.blit(overlay, (0, 0))
    
    # Draw prediction result
    font = pygame.font.SysFont(None, 48)
    
    if predicted_class == "Emergency Vechicle":
        result_text = "EMERGENCY VEHICLE DETECTED!"
        color = (255, 50, 50)
    elif predicted_class == "Normal":
        result_text = "Normal Vehicle Detected"
        color = (50, 255, 50)
    else:
        result_text = "Error in prediction"
        color = (255, 255, 50)
    
    text = font.render(result_text, True, color)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 100))
    
    # Draw current action based on traffic light state
    action_text = ""
    if predicted_class == "Emergency Vechicle":
        if traffic_light.state == LIGHT_RED:
            action_text = "Switching traffic light to GREEN"
        else:
            action_text = "Traffic light already GREEN - No action needed"
    else:
        action_text = "No action needed"
        
    action_font = pygame.font.SysFont(None, 36)
    action_rendered = action_font.render(action_text, True, WHITE)
    screen.blit(action_rendered, (WIDTH//2 - action_rendered.get_width()//2, HEIGHT//2))
    
    # Draw continue button
    continue_button = pygame.draw.rect(screen, (0, 150, 0), 
                                      (WIDTH//2 - 100, HEIGHT//2 + 100, 200, 50), 
                                      border_radius=10)
    button_text = font.render("Continue", True, WHITE)
    screen.blit(button_text, (WIDTH//2 - button_text.get_width()//2, HEIGHT//2 + 100 + 5))
    
    # If image is provided, display it
    if img is not None:
        # Convert PIL Image to Pygame surface
        img_data = np.array(img)
        img_surface = pygame.surfarray.make_surface(img_data.transpose((1, 0, 2)))
        img_surface = pygame.transform.scale(img_surface, (150, 150))
        screen.blit(img_surface, (WIDTH//2 - 75, HEIGHT//2 - 250))
    
    pygame.display.flip()
    
    # Wait for user to click continue
    waiting_for_click = True
    while waiting_for_click:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint(event.pos):
                    waiting_for_click = False

def open_file_dialog():
    """Open a file dialog to select an image for prediction"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    file_path = filedialog.askopenfilename(
        title="Select Vehicle Image",
        filetypes=[("Image files", "*.jpg *.jpeg *.png")]
    )
    
    root.destroy()
    return file_path

# Create traffic light
traffic_light = TrafficLight(500, 350)

# Create cars
cars = []
for i in range(3):
    cars.append(Car(-200 - i * 200, 320, 2 + i * 0.5, is_emergency=False))

# Main game loop
clock = pygame.time.Clock()
running = True
showing_prediction = False
last_image_path = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and not showing_prediction:
            mouse_pos = pygame.mouse.get_pos()
            red_button, green_button, auto_button, upload_button = draw_buttons()
            
            if red_button.collidepoint(mouse_pos):
                traffic_light.auto_mode = False
                traffic_light.set_red()
            elif green_button.collidepoint(mouse_pos):
                traffic_light.auto_mode = False
                traffic_light.set_green()
            elif auto_button.collidepoint(mouse_pos):
                traffic_light.toggle_auto_mode()
            elif upload_button.collidepoint(mouse_pos) and model_loaded:
                # Open file dialog to select image
                image_path = open_file_dialog()
                if image_path:
                    last_image_path = image_path
                    predicted_class, img = predict_vehicle_type(image_path)
                    print(f"Predicted: {predicted_class}")
                    
                    # Apply traffic rules based on prediction
                    if predicted_class == "Emergency Vechicle" and traffic_light.state == LIGHT_RED:
                        traffic_light.emergency_detected()
                    
                    # Show prediction overlay
                    showing_prediction = True
                    show_prediction_overlay(predicted_class, img)
                    showing_prediction = False
    
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
    
    # Draw UI elements
    font = pygame.font.SysFont(None, 32)
    title = font.render("ML Traffic Signal Simulator", True, BLACK)
    screen.blit(title, (WIDTH//2 - 150, 20))
    
    font = pygame.font.SysFont(None, 24)
    red_text = font.render("RED: Stop", True, RED)
    screen.blit(red_text, (20, 70))
    
    yellow_text = font.render("YELLOW: Wait", True, (150, 150, 0))
    screen.blit(yellow_text, (20, 100))
    
    green_text = font.render("GREEN: Go", True, GREEN)
    screen.blit(green_text, (20, 130))
    
    # Show ML status
    ml_status = "ML Model: Loaded" if model_loaded else "ML Model: Not Loaded"
    ml_text = font.render(ml_status, True, (0, 100, 0) if model_loaded else (150, 0, 0))
    screen.blit(ml_text, (WIDTH - 200, 70))
    
    # Draw control buttons
    draw_buttons()
    
    # Display last prediction if available
    if last_image_path and not showing_prediction:
        font = pygame.font.SysFont(None, 20)
        filename = os.path.basename(last_image_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        text = font.render(f"Last image: {filename}", True, BLACK)
        screen.blit(text, (WIDTH - 300, 100))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()