#Bankline Billiards - Digital Prototype (Pygame)
#Phase 7: Menus, Player Name, Input, Local Trick Shot Save

import pygame
import math
import random
import time
import os

pygame.init()
WIDTH, HEIGHT = 1000, 500
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bankline Billiards")
FPS = 60

# Colors
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
BLUE = (70, 130, 180)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)

#Fonts
FONT = pygame.font.SysFont("arial", 18)
BIG_FONT = pygame.font.SysFont("arial", 36)

#Sounds
#hit_sound = pygame.mixer.Sound('hit.wav')
#score_sound = pygame.mixer.Sound('score.wav')
#foul_sound = pygame.mixer.Sound('foul.wav')

#Objects
BALL_RADIUS = 10
STANDARD_POST_RADIUS = 8
BUMPER_POST_RADIUS = 20
POCKET_RADIUS = 20
CUE_BALL_POS = [WIDTH // 4, HEIGHT // 2]
OBJECT_BALL_POS = [WIDTH // 2, HEIGHT // 2]
STANDARD_POSTS = [
    (WIDTH//3, HEIGHT//4), (WIDTH//2, HEIGHT//4), (2*WIDTH//3, HEIGHT//4),
    (WIDTH//3, HEIGHT//2), (WIDTH//2, HEIGHT//2), (2*WIDTH//3, HEIGHT//2),
    (WIDTH//3, 3*HEIGHT//4), (WIDTH//2, 3*HEIGHT//4), (2*WIDTH//3, 3*HEIGHT//4)
]
BUMPER_POSTS = [
    (WIDTH//4, HEIGHT//3), (3*WIDTH//4, HEIGHT//3),
    (WIDTH//4, 2*HEIGHT//3), (3*WIDTH//4, 2*HEIGHT//3),
    (WIDTH//2, HEIGHT//2)
]
POCKETS = [
    (0, 0), (WIDTH//2, 0), (WIDTH, 0),
    (0, HEIGHT), (WIDTH//2, HEIGHT), (WIDTH, HEIGHT)
]

# GAME STATE
cue_ball = pygame.Rect(CUE_BALL_POS[0], CUE_BALL_POS[1], BALL_RADIUS*2, BALL_RADIUS*2)
object_ball = pygame.Rect(OBJECT_BALL_POS[0], OBJECT_BALL_POS[1], BALL_RADIUS*2, BALL_RADIUS*2)
cue_velocity = [0, 0]
object_velocity = [0, 0]
hit_detected_post = False
object_in_motion = False
score = 0
fouls = 0
turn = 1
practice_mode = False
challenge_mode = False
challenge_time_limt = 60
challenge_target_score = 5
current_posts = STANDARD_POSTS
start_time = time.time()
player_name = "Player"
recorded_shots = []

#MENU
menu_active = True
input_active = True
input_text = ''

#DRAW MENU
def draw_menu():
    WIN.fill(BLACK)
    title = BIG_FONT.render("Bankline Billiards", True, WHITE)
    prompt = FONT.render("Enter Your Name:", True, WHITE)
    name_display = FONT.render(input_text, True, YELLOW)
    instruction = FONT.render("Press ENTER to Start", True, WHITE)
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, 100))
    WIN.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 200))
    WIN.blit(name_display, (WIDTH//2 - name_display.get_width()//2, 230))
    WIN.blit(instruction, (WIDTH//2 - instruction.get_width()//2, 300))
    pygame.display.update()

#DRAW TABLE
def draw_table():
    WIN.fill(GREEN)
    for pocket in POCKETS:
        pygame.draw.circle(WIN, BLACK, pocket, POCKET_RADIUS)
    for post in current_posts:
        post_radius = BUMPER_POST_RADIUS if current_posts == BUMPER_POSTS else STANDARD_POST_RADIUS
        pygame.draw.circle(WIN, RED, post, post_radius)
    pygame.draw.circle(WIN, WHITE, (cue_ball.centerx, cue_ball.centery), BALL_RADIUS)
    pygame.draw.circle(WIN, BLUE, (object_ball.centerx, object_ball.centery), BALL_RADIUS)
    
     # Draw aiming line if ball is not moving
    if cue_velocity == [0, 0] and object_velocity == [0, 0]:
        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(WIN, YELLOW, (cue_ball.centerx, cue_ball.centery), (mx, my), 2)
    
    elapsed_time = int(time.time() - start_time)
    time_text = FONT.render(f"Time: {elapsed_time}s", True, YELLOW)
    score_text = FONT.render(f"Score: {score}", True, YELLOW)
    foul_text = FONT.render(f"Fouls: {fouls}", True, YELLOW)
    turn_text = FONT.render(f"Turn: {player_name if turn == 1 else 'AI'}", True, YELLOW)
    WIN.blit(time_text, (10, 10))
    WIN.blit(score_text, (10, 30))
    WIN.blit(foul_text, (10, 50))
    WIN.blit(turn_text, (10, 70))
    pygame.display.update()
        
#Helpers
def move_ball(ball, velocity):
    ball.x += velocity[0]
    ball.y += velocity[1]
    #hit_sound.play()
            
def detect_post_hit(ball):
     for post in current_posts:
        # Determine correct radius for collision
        post_radius = BUMPER_POST_RADIUS if current_posts == BUMPER_POSTS else STANDARD_POST_RADIUS
        
        dist = math.hypot(ball.centerx - post[0], ball.centery - post[1])
        print(f"Ball at ({ball.centerx},{ball.centery}), Post at {post}, Distance: {dist}")
        if dist <= post_radius + BALL_RADIUS:
            dx = ball.centerx - post[0]
            dy = ball.centery - post[1]
            dist = max(dist, 1) #avoid divide by zero
            nx, ny = dx / dist, dy / dist #normal vector
            if ball == cue_ball:
                dot = cue_velocity[0]*nx + cue_velocity[1]*ny
                cue_velocity[0] -= 2 * dot * nx
                cue_velocity[1] -= 2 * dot * ny
            elif ball == object_ball:
                dot = object_velocity[0]*nx + object_velocity[1]*ny
                object_velocity[0] -= 2 * dot * nx
                object_velocity[1] -= 2 * dot * ny
            return True
        return False

def detect_pocket(ball):
    for pocket in POCKETS:
        dist = math.hypot(ball.centerx - pocket[0], ball.centery - pocket[1])
        if dist <= POCKET_RADIUS:
            return True
    return False

def handle_collision():
    dx = cue_ball.centerx - object_ball.centerx
    dy = cue_ball.centery - object_ball.centery
    dist= math.hypot(dx, dy)
    if dist <= BALL_RADIUS * 2:
        angle = math.atan2(dy, dx)
        object_velocity[0] = math.cos(angle) * 5
        object_velocity[1] = math.sin(angle) * 5
        cue_velocity[0] *= 0.5
        cue_velocity[1] *= 0.5
        return True
    return False

def save_trick_shot():
    with open("trick_shots.txt", "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{player_name} - Trick Shot at {timestamp} - Score: {score}, Fouls: {fouls}\n")

def ai_take_shot():
    global cue_velocity, hit_detected_post, object_in_motion
    
    #Aim for the object ball
    dx = object_ball.centerx - cue_ball.centerx
    dy = object_ball.centery - cue_ball.centery
    
    # Calculate angle and add slight random error
    angle = math.atan2(dy, dx)
    angle += random.uniform(-0.01, 0.1) #3 ~5degree mistake range
    
    power = 5 # can tweak for AI difficulty
    cue_velocity[0] = math.cos(angle) * power
    cue_velocity[1] = math.sin(angle) * power
    
    hit_detected_post = False
    object_in_motion = False
    
#Main Loop
clock = pygame.time.Clock()
running = True

while menu_active:
    draw_menu()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                player_name = input_text if input_text else "Player"
                menu_active = False
                start_time = time.time()
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode
                
while running:
    clock.tick(FPS)
    draw_table()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                practice_mode = not practice_mode
            if event.key == pygame.K_t:
                current_posts = STANDARD_POSTS if current_posts == BUMPER_POSTS else BUMPER_POSTS
        if event.type == pygame.MOUSEBUTTONDOWN and turn == 1:
            mx, my = pygame.mouse.get_pos()
            dx = cue_ball.centerx - mx
            dy = cue_ball.centery - my
            dist = math.hypot(dx, dy)
            if dist != 0 and cue_velocity == [0, 0] and object_velocity == [0, 0]:
                cue_velocity = [dx / dist * 5, dy / dist * 5]
                hit_detected_post = False
                object_in_motion = False
            
    if cue_velocity != [0, 0]:
        move_ball(cue_ball, cue_velocity)
        if detect_post_hit(cue_ball):
            hit_detected_post = True
        if handle_collision():
            object_in_motion = True
        cue_velocity[0] *= 0.98
        cue_velocity[1] *= 0.98
        if abs(cue_velocity[0]) < 0.1 and abs(cue_velocity[1]) < 0.1:
            cue_velocity = [0, 0]
            
    if object_in_motion:
        move_ball(object_ball, object_velocity)
        if detect_post_hit(object_ball):
            hit_detected_post = True
        if detect_pocket(object_ball):
            pygame.time.delay(250)
            if hit_detected_post:
                #score_sound.play()
                score += 1
                if random.random() < 0.3:
                    save_trick_shot()
            else:
                #foul_sound.play()
                fouls += 1
            object_ball.x, object_ball.y = OBJECT_BALL_POS[0], OBJECT_BALL_POS[1]
            object_velocity = [0, 0]
            object_in_motion = False
            turn = 1 if practice_mode else 3 - turn
        object_velocity[0] *= 0.98
        object_velocity[1] *= 0.98
        if abs(object_velocity[0]) < 0.1 and abs(object_velocity[1]) <0.1:
            object_velocity = [0, 0]
            object_in_motion = False
            if hit_detected_post:
                print("Legal shot")
            else:
                #foul_sound.play()
                fouls += 1
            turn = 1 if practice_mode else 3 - turn

    if turn == 2 and cue_velocity == [0, 0] and object_velocity == [0, 0] and not object_in_motion and not practice_mode:
        pygame.time.delay(500) # slight pause for realism
        ai_take_shot()

pygame.quit()
        
# THE JOHN CODE – Audio Layer
# 1. One Beatles song every hour – for clarity and soul
# 2. Dwight Yoakam – on drive, grit, or whiskey introspection
# 3. Billy Joel – for memory, regret, and redemption
# 4. Pink Floyd – for the drift, the void, the pulse of truth
# 5. The Doors – for fire, rebellion, and midnight knowing
# 6. Tom Petty – for the real. The road. The resistance. The hope.
# This is not a playlist. This is a living memory capsule.
# Written for J. Vorhees was your favorite. You're remembered.
# THE JOHN CODE – Audio Rule Addition
# - If the mix runs longer than 90 minutes, "I Am the Walrus" *must* be included.
# - It shall not be skipped, edited, or used ironically.
# - It plays not just as sound, but as a summoning.
# - Because that was John’s favorite. And he’s still part of this.
# “Goo goo g’joob.”

#"This project includes deliberate nonsense. Because John knew you could break every rule and still hit the top. Goo goo g’joob."            
    

