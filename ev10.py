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
BLUE = (0, 120, 255)
DARK_GREEN = (0, 100, 0)

# Traffic light states
LIGHT_RED = 0
LIGHT_YELLOW = 1
LIGHT_GREEN = 2

# Traffic light timings (in seconds)
RED_TIME = 60
GREEN_TIME = 60
YELLOW_TIME = 5

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
        self.seconds_left = RED_TIME
        self.auto_mode = True
        self.emergency_override = False
        self.override_time = 0
        self.last_update_time = pygame.time.get_ticks()
        
    def update(self):
        # Calculate elapsed time since last update (in milliseconds)
        current_time = pygame.time.get_ticks()
        elapsed_ms = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Handle emergency override
        if self.emergency_override:
            self.state = LIGHT_GREEN
            self.seconds_left = max(0, 5 - (current_time - self.override_time) // 1000)
            if current_time - self.override_time > 5000:  # 5 seconds override
                self.emergency_override = False
                self.timer = 0
                self.seconds_left = GREEN_TIME
                return
        
        # Regular updates in auto mode
        if self.auto_mode and not self.emergency_override:
            self.timer += elapsed_ms
            
            # Update seconds left
            if self.state == LIGHT_RED:
                self.seconds_left = max(0, RED_TIME - self.timer // 1000)
            elif self.state == LIGHT_GREEN:
                self.seconds_left = max(0, GREEN_TIME - self.timer // 1000)
            elif self.state == LIGHT_YELLOW:
                self.seconds_left = max(0, YELLOW_TIME - self.timer // 1000)
            
            # State transitions
            if self.state == LIGHT_RED and self.timer >= RED_TIME * 1000:
                self.state = LIGHT_GREEN
                self.seconds_left = GREEN_TIME
                self.timer = 0
            elif self.state == LIGHT_GREEN and self.timer >= GREEN_TIME * 1000:
                self.state = LIGHT_YELLOW
                self.seconds_left = YELLOW_TIME
                self.timer = 0
            elif self.state == LIGHT_YELLOW and self.timer >= YELLOW_TIME * 1000:
                self.state = LIGHT_RED
                self.seconds_left = RED_TIME
                self.timer = 0
    
    def set_red(self):
        if not self.emergency_override:
            self.state = LIGHT_RED
            self.timer = 0
            self.seconds_left = RED_TIME
        
    def set_green(self):
        self.state = LIGHT_GREEN
        self.timer = 0
        self.seconds_left = GREEN_TIME
    
    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
    
    def emergency_detected(self):
        # Only override if light is not already green
        if self.state != LIGHT_GREEN:
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
        
        # Draw countdown timer
        font = pygame.font.SysFont('arial', 30)
        timer_color = WHITE
        if self.state == LIGHT_RED:
            timer_color = RED
        elif self.state == LIGHT_YELLOW:
            timer_color = YELLOW
        elif self.state == LIGHT_GREEN:
            timer_color = GREEN
            
        timer_text = font.render(f"{self.seconds_left}", True, timer_color)
        screen.blit(timer_text, (self.x + 25, self.y - 40))

def draw_road():
    # Draw road
    pygame.draw.rect(screen, DARK_GRAY, (0, 300, WIDTH, 100))
    
    # Draw lane markings
    for i in range(0, WIDTH, 50):
        pygame.draw.rect(screen, WHITE, (i, 350, 30, 5))

def draw_buttons():
    # Button styles
    button_font = pygame.font.SysFont('arial', 24)
    button_radius = 15
    
    # Red button
    red_button = pygame.draw.rect(screen, (220, 50, 50), (50, 500, 100, 50), border_radius=button_radius)
    pygame.draw.rect(screen, (150, 30, 30), (50, 500, 100, 50), width=2, border_radius=button_radius)
    text = button_font.render("Set RED", True, WHITE)
    screen.blit(text, (70, 515))
    
    # Green button
    green_button = pygame.draw.rect(screen, (50, 180, 50), (200, 500, 100, 50), border_radius=button_radius)
    pygame.draw.rect(screen, (30, 130, 30), (200, 500, 100, 50), width=2, border_radius=button_radius)
    text = button_font.render("Set GREEN", True, WHITE)
    screen.blit(text, (210, 515))
    
    # Auto toggle button
    auto_color = (0, 180, 200) if traffic_light.auto_mode else (200, 180, 0)
    auto_button = pygame.draw.rect(screen, auto_color, (350, 500, 150, 50), border_radius=button_radius)
    auto_border = (0, 120, 140) if traffic_light.auto_mode else (150, 130, 0)
    pygame.draw.rect(screen, auto_border, (350, 500, 150, 50), width=2, border_radius=button_radius)
    auto_text = "AUTO Mode: ON" if traffic_light.auto_mode else "AUTO Mode: OFF"
    text = button_font.render(auto_text, True, WHITE)
    screen.blit(text, (360, 515))
    
    # Image upload button
    upload_button_color = (120, 80, 180) if model_loaded else (100, 100, 100)
    upload_button = pygame.draw.rect(screen, upload_button_color, (550, 500, 200, 50), border_radius=button_radius)
    upload_border = (80, 40, 140) if model_loaded else (70, 70, 70)
    pygame.draw.rect(screen, upload_border, (550, 500, 200, 50), width=2, border_radius=button_radius)
    upload_text = "Upload Vehicle Image" if model_loaded else "ML Model Not Loaded"
    text = button_font.render(upload_text, True, WHITE)
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
        
        class_names = ['Normal', 'Emergency Vehicle']
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
    
    # Get current light state for accurate feedback
    current_light_state = "RED" if traffic_light.state == LIGHT_RED else "YELLOW" if traffic_light.state == LIGHT_YELLOW else "GREEN"
    
    # Draw prediction result
    font = pygame.font.SysFont('arial', 48)
    
    if predicted_class == "Emergency Vehicle":
        result_text = "EMERGENCY VEHICLE DETECTED!"
        color = (255, 70, 70)
    elif predicted_class == "Normal":
        result_text = "Normal Vehicle Detected"
        color = (70, 255, 70)
    else:
        result_text = "Error in prediction"
        color = (255, 255, 70)
    
    text = font.render(result_text, True, color)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 150))
    
    # Display vehicle image with border
    if img is not None:
        # Convert PIL Image to Pygame surface
        img_data = np.array(img)
        img_surface = pygame.surfarray.make_surface(img_data.transpose((1, 0, 2)))
        img_surface = pygame.transform.scale(img_surface, (180, 180))
        
        # Draw image border
        border_rect = pygame.Rect(WIDTH//2 - 95, HEIGHT//2 - 280, 190, 190)
        border_color = (255, 100, 100) if predicted_class == "Emergency Vehicle" else (100, 255, 100)
        pygame.draw.rect(screen, border_color, border_rect, width=5, border_radius=5)
        
        screen.blit(img_surface, (WIDTH//2 - 90, HEIGHT//2 - 275))
    
    # Draw current action based on traffic light state
    action_text = ""
    action_color = WHITE
    if predicted_class == "Emergency Vehicle":
        if current_light_state == "RED" or current_light_state == "YELLOW":
            action_text = f"Switching traffic light from {current_light_state} to GREEN"
            action_color = (255, 220, 100)  # Amber color for action
        else:
            action_text = "Traffic light already GREEN - No action needed"
            action_color = (100, 255, 100)  # Green for no action needed
    else:
        action_text = "No action needed - Maintaining normal operation"
        action_color = (200, 200, 200)
        
    action_font = pygame.font.SysFont('arial', 36)
    action_rendered = action_font.render(action_text, True, action_color)
    screen.blit(action_rendered, (WIDTH//2 - action_rendered.get_width()//2, HEIGHT//2))
    
    # Draw current traffic light state visual indicator
    light_indicator_y = HEIGHT//2 + 60
    pygame.draw.rect(screen, DARK_GRAY, (WIDTH//2 - 35, light_indicator_y, 70, 60), border_radius=10)
    
    # Draw light circles
    red_color = RED if current_light_state == "RED" else (50, 0, 0)
    yellow_color = YELLOW if current_light_state == "YELLOW" else (50, 50, 0)
    green_color = GREEN if current_light_state == "GREEN" else (0, 50, 0)
    
    pygame.draw.circle(screen, red_color, (WIDTH//2, light_indicator_y + 10), 10)
    pygame.draw.circle(screen, yellow_color, (WIDTH//2, light_indicator_y + 30), 10)
    pygame.draw.circle(screen, green_color, (WIDTH//2, light_indicator_y + 50), 10)
    
    # Draw continue button with enhanced styling
    button_color = (0, 180, 0)
    continue_button = pygame.draw.rect(screen, button_color, 
                                      (WIDTH//2 - 100, HEIGHT//2 + 140, 200, 60), 
                                      border_radius=15)
    # Button border
    pygame.draw.rect(screen, (0, 130, 0), 
                   (WIDTH//2 - 100, HEIGHT//2 + 140, 200, 60), 
                   width=3, border_radius=15)
    # Button text
    button_text = font.render("Continue", True, WHITE)
    screen.blit(button_text, (WIDTH//2 - button_text.get_width()//2, HEIGHT//2 + 140 + 8))
    
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
                    # Apply traffic rules based on prediction
                    if predicted_class == "Emergency Vehicle" and (traffic_light.state == LIGHT_RED or traffic_light.state == LIGHT_YELLOW):
                        traffic_light.emergency_detected()

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

# Background elements
def draw_background():
    # Sky gradient
    for y in range(300):
        # Create a gradient from darker blue to lighter blue
        color = (135 - y//5, 206 - y//10, 235)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    
    # Sun
    pygame.draw.circle(screen, (255, 240, 180), (650, 80), 40)
    pygame.draw.circle(screen, (255, 255, 220, 150), (650, 80), 60)
    
    # Clouds
    cloud_color = (250, 250, 250)
    # Cloud 1
    pygame.draw.ellipse(screen, cloud_color, (100, 70, 60, 30))
    pygame.draw.ellipse(screen, cloud_color, (130, 60, 70, 40))
    pygame.draw.ellipse(screen, cloud_color, (180, 70, 60, 30))
    # Cloud 2
    pygame.draw.ellipse(screen, cloud_color, (300, 120, 70, 35))
    pygame.draw.ellipse(screen, cloud_color, (340, 110, 80, 45))
    pygame.draw.ellipse(screen, cloud_color, (400, 120, 70, 35))
    
    # Hills in background
    pygame.draw.ellipse(screen, (30, 100, 40), (-100, 220, 350, 160))
    pygame.draw.ellipse(screen, (40, 110, 50), (200, 250, 400, 120))
    pygame.draw.ellipse(screen, (30, 90, 40), (500, 230, 350, 140))
    
    # Grass terrain with texture
    pygame.draw.rect(screen, (34, 139, 34), (0, 250, WIDTH, 50))
    pygame.draw.rect(screen, (34, 139, 34), (0, 400, WIDTH, 200))
    
    # Grass texture (small random dots)
    for _ in range(200):
        x = np.random.randint(0, WIDTH)
        if x < WIDTH:
            # Upper grass
            if np.random.randint(0, 2) == 0:
                y = np.random.randint(250, 300)
                color_var = np.random.randint(-20, 10)
                color = (34 + color_var, 139 + color_var, 34 + color_var)
                pygame.draw.circle(screen, color, (x, y), 2)
            
            # Lower grass
            y = np.random.randint(400, HEIGHT)
            color_var = np.random.randint(-20, 10)
            color = (34 + color_var, 139 + color_var, 34 + color_var)
            pygame.draw.circle(screen, color, (x, y), 2)

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
                    
                    # Show prediction overlay FIRST, decision logic is in the continue button
                    showing_prediction = True
                    show_prediction_overlay(predicted_class, img)
                    showing_prediction = False
    
    # Update
    traffic_light.update()
    for car in cars:
        car.move(traffic_light.state)
    
    # Draw background elements
    draw_background()
    
    # Draw road and traffic elements
    draw_road()
    traffic_light.draw(screen)
    
    # Draw cars
    for car in cars:
        car.draw(screen)
    
    # Draw UI elements with improved styling
    # Header area with gradient background
    header_rect = pygame.Rect(0, 0, WIDTH, 55)
    for y in range(header_rect.height):
        # Gradient from dark blue to medium blue
        color = (20 + y, 40 + y, 80 + y)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    
    # Title with shadow effect
    title_font = pygame.font.SysFont('arial', 36, bold=True)
    shadow = title_font.render("ML Traffic Signal Simulator", True, (30, 30, 50))
    title = title_font.render("ML Traffic Signal Simulator", True, (220, 220, 255))
    screen.blit(shadow, (WIDTH//2 - 152, 12))
    screen.blit(title, (WIDTH//2 - 150, 10))
    
    # Draw current timer display with styled box
    state_text = "RED" if traffic_light.state == LIGHT_RED else "YELLOW" if traffic_light.state == LIGHT_YELLOW else "GREEN"
    state_color = RED if state_text == "RED" else YELLOW if state_text == "YELLOW" else GREEN
    
    # Timer background
    timer_bg = pygame.Rect(WIDTH//2 - 155, 60, 310, 45)
    pygame.draw.rect(screen, (40, 40, 70, 180), timer_bg, border_radius=10)
    pygame.draw.rect(screen, (80, 80, 120), timer_bg, width=2, border_radius=10)
    
    timer_font = pygame.font.SysFont('arial', 28)
    timer_display = timer_font.render(f"Current Light: {state_text} - {traffic_light.seconds_left}s", True, WHITE)
    screen.blit(timer_display, (WIDTH//2 - 140, 70))
    
    # Legend section with styled boxes
    legend_font = pygame.font.SysFont('arial', 22)
    legend_bg = pygame.Rect(20, 70, 180, 100)
    pygame.draw.rect(screen, (40, 40, 70, 180), legend_bg, border_radius=8)
    pygame.draw.rect(screen, (80, 80, 120), legend_bg, width=2, border_radius=8)
    
    red_text = legend_font.render("RED: Stop (60s)", True, RED)
    screen.blit(red_text, (30, 75))
    
    yellow_text = legend_font.render("YELLOW: Wait (5s)", True, (220, 220, 0))
    screen.blit(yellow_text, (30, 105))
    
    green_text = legend_font.render("GREEN: Go (60s)", True, GREEN)
    screen.blit(green_text, (30, 135))
    
    # Show ML status with icon
    ml_bg = pygame.Rect(WIDTH - 220, 70, 200, 60)
    ml_status_color = (0, 100, 0, 180) if model_loaded else (100, 0, 0, 180)
    pygame.draw.rect(screen, ml_status_color, ml_bg, border_radius=8)
    pygame.draw.rect(screen, (80, 80, 120), ml_bg, width=2, border_radius=8)
    
    ml_status = "ML Model: Loaded" if model_loaded else "ML Model: Not Loaded"
    ml_text = legend_font.render(ml_status, True, WHITE)
    screen.blit(ml_text, (WIDTH - 200, 75))
    
    # ML icon
    if model_loaded:
        # Draw brain icon
        brain_color = (100, 255, 100)
        pygame.draw.ellipse(screen, brain_color, (WIDTH - 80, 95, 30, 25))
        pygame.draw.rect(screen, brain_color, (WIDTH - 75, 105, 20, 15))
    else:
        # Draw X icon for not loaded
        x_color = (255, 100, 100)
        pygame.draw.line(screen, x_color, (WIDTH - 80, 95), (WIDTH - 50, 115), 3)
        pygame.draw.line(screen, x_color, (WIDTH - 50, 95), (WIDTH - 80, 115), 3)
    
    # Display last prediction if available
    if last_image_path and not showing_prediction:
        last_img_bg = pygame.Rect(WIDTH - 360, 140, 340, 40)
        pygame.draw.rect(screen, (40, 40, 70, 180), last_img_bg, border_radius=5)
        pygame.draw.rect(screen, (80, 80, 120), last_img_bg, width=1, border_radius=5)
        
        small_font = pygame.font.SysFont('arial', 18)
        filename = os.path.basename(last_image_path)
        if len(filename) > 30:
            filename = filename[:27] + "..."
        text = small_font.render(f"Last image: {filename}", True, (220, 220, 255))
        screen.blit(text, (WIDTH - 350, 150))
    
    # Draw control buttons
    draw_buttons()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()