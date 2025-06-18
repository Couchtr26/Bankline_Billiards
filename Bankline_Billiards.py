import pygame
import math
import random
import time

player_name = "AI"
shot_taken = False
foul_committed = False  # Track foul occurrence per shot

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

# Fonts
FONT = pygame.font.SysFont("arial", 18)

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

# Game state
cue_ball = pygame.Rect(*CUE_BALL_POS, BALL_RADIUS*2, BALL_RADIUS*2)
object_ball = pygame.Rect(*OBJECT_BALL_POS, BALL_RADIUS*2, BALL_RADIUS*2)
cue_velocity = [0.0, 0.0]
object_velocity = [0.0, 0.0]
hit_detected_post = False
cue_hit_object = False
object_in_motion = False
score = 0
fouls = 0
turn = 1
practice_mode = False
current_posts = STANDARD_POSTS

friction = 0.98
velocity_threshold = 0.1

def move_ball(ball, velocity):
    ball.x += velocity[0]
    ball.y += velocity[1]

def bounce_ball(ball, velocity):
    if ball.left <= 0:
        ball.left = 0
        velocity[0] = -velocity[0]
    if ball.right >= WIDTH:
        ball.right = WIDTH
        velocity[0] = -velocity[0]
    if ball.top <= 0:
        ball.top = 0
        velocity[1] = -velocity[1]
    if ball.bottom >= HEIGHT:
        ball.bottom = HEIGHT
        velocity[1] = -velocity[1]

def detect_post_hit(ball):
    global cue_velocity, object_velocity
    for post in current_posts:
        post_radius = BUMPER_POST_RADIUS if current_posts == BUMPER_POSTS else STANDARD_POST_RADIUS
        dist = math.hypot(ball.centerx - post[0], ball.centery - post[1])
        min_dist = post_radius + BALL_RADIUS
        if dist <= min_dist:
            dx = ball.centerx - post[0]
            dy = ball.centery - post[1]
            dist = max(dist, 0.001)  # avoid division by zero
            nx, ny = dx / dist, dy / dist
            
            # Push ball outside the post so it doesn't get stuck
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.y += ny * overlap
            
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

def is_off_table(ball):
    return ball.left < 0 or ball.right > WIDTH or ball.top < 0 or ball.bottom > HEIGHT

def collide_balls(ball1, vel1, ball2, vel2):
    dx = ball2.centerx - ball1.centerx
    dy = ball2.centery - ball1.centery
    dist = math.hypot(dx, dy)
    min_dist = BALL_RADIUS * 2
    
    if dist == 0:
        return vel1, vel2
    
    # Normalize vector between balls
    nx = dx / dist
    ny = dy / dist
    
    # Relative velocity in normal direction
    dvx = vel1[0] - vel2[0]
    dvy = vel1[1] - vel2[1]
    vn = dvx * nx + dvy * ny
    
    # If balls are moving apart, do nothing
    if vn > 0:
        return vel1, vel2
    
    # Calculate impulse for elastic collision
    impulse = -2 * vn / 2
    
    # Update velocities
    vel1_new = [vel1[0] + impulse * nx, vel1[1] + impulse * ny]
    vel2_new = [vel2[0] - impulse * nx, vel2[1] - impulse * ny]
    
    # Positional correction to prevent overlap
    overlap = min_dist - dist
    correction_x = nx * overlap / 2
    correction_y = ny * overlap / 2
    
    ball1.x -= correction_x
    ball1.y -= correction_y
    ball2.x += correction_x
    ball2.y += correction_y
    
    return vel1_new, vel2_new

def handle_collision():
    dx = cue_ball.centerx - object_ball.centerx
    dy = cue_ball.centery - object_ball.centery
    dist = math.hypot(dx, dy)
    return dist <= BALL_RADIUS * 2

def reset_balls(reset_cue=True):
    global cue_velocity, object_velocity, object_in_motion, hit_detected_post, cue_hit_object, foul_committed
    if reset_cue:
        cue_ball.center = CUE_BALL_POS
    object_ball.center = OBJECT_BALL_POS
    cue_velocity = [0.0, 0.0]
    object_velocity = [0.0, 0.0]
    object_in_motion = False
    hit_detected_post = False
    cue_hit_object = False
    foul_committed = False

def draw_table():
    WIN.fill(GREEN)
    for pocket in POCKETS:
        pygame.draw.circle(WIN, BLACK, pocket, POCKET_RADIUS)
    for post in current_posts:
        post_radius = BUMPER_POST_RADIUS if current_posts == BUMPER_POSTS else STANDARD_POST_RADIUS
        pygame.draw.circle(WIN, RED, post, post_radius)
    pygame.draw.circle(WIN, WHITE, cue_ball.center, BALL_RADIUS)
    pygame.draw.circle(WIN, BLUE, object_ball.center, BALL_RADIUS)
    if (abs(cue_velocity[0]) < velocity_threshold and abs(cue_velocity[1]) < velocity_threshold and
        abs(object_velocity[0]) < velocity_threshold and abs(object_velocity[1]) < velocity_threshold):
        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(WIN, YELLOW, cue_ball.center, (mx, my), 2)
    WIN.blit(FONT.render(f"Score: {score}", True, WHITE), (10, 10))
    WIN.blit(FONT.render(f"Fouls: {fouls}", True, WHITE), (10, 30))
    WIN.blit(FONT.render(f"Turn: {'You' if turn == 1 else 'AI'}", True, WHITE), (10, 50))
    pygame.display.update()

def ai_take_shot():
    global cue_velocity, hit_detected_post, object_in_motion, shot_taken
    
    dx = object_ball.centerx - cue_ball.centerx
    dy = object_ball.centery - cue_ball.centery
    angle = math.atan2(dy, dx)
    angle += random.uniform(-0.5, 0.5)
    
    power = 5
    cue_velocity[0] = math.cos(angle) * power
    cue_velocity[1] = math.sin(angle) * power
    
    hit_detected_post = False
    object_in_motion = False
    shot_taken = True  

clock = pygame.time.Clock()
running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                practice_mode = not practice_mode
            elif event.key == pygame.K_t:
                current_posts = STANDARD_POSTS if current_posts == BUMPER_POSTS else BUMPER_POSTS
        elif event.type == pygame.MOUSEBUTTONDOWN and turn == 1:
            mx, my = pygame.mouse.get_pos()
            dx = mx - cue_ball.centerx
            dy = my - cue_ball.centery
            dist = math.hypot(dx, dy)
            if (dist != 0 and
                abs(cue_velocity[0]) < velocity_threshold and abs(cue_velocity[1]) < velocity_threshold and
                abs(object_velocity[0]) < velocity_threshold and abs(object_velocity[1]) < velocity_threshold):
                power = min(dist / 10, 15)
                cue_velocity = [-(dx / dist) * power, -(dy / dist) * power]
                shot_taken = True
                hit_detected_post = False
                cue_hit_object = False
                object_in_motion = False
                foul_committed = False

    # Move cue ball
    if not (abs(cue_velocity[0]) < velocity_threshold and abs(cue_velocity[1]) < velocity_threshold):
        move_ball(cue_ball, cue_velocity)
        bounce_ball(cue_ball, cue_velocity)
        if detect_post_hit(cue_ball):
            hit_detected_post = True
        if handle_collision():
            cue_hit_object = True
            cue_velocity, object_velocity = collide_balls(cue_ball, cue_velocity, object_ball, object_velocity)
            object_in_motion = True

        cue_velocity[0] *= friction
        cue_velocity[1] *= friction
        if abs(cue_velocity[0]) < velocity_threshold:
            cue_velocity[0] = 0.0
        if abs(cue_velocity[1]) < velocity_threshold:
            cue_velocity[1] = 0.0

        if abs(object_velocity[0]) < velocity_threshold and abs(object_velocity[1]) < velocity_threshold:
            object_velocity = [0.0, 0.0]
            object_in_motion = False

    # Move object ball
    if object_in_motion:
        move_ball(object_ball, object_velocity)
        bounce_ball(object_ball, object_velocity)
        if detect_post_hit(object_ball):
            hit_detected_post = True
        if detect_pocket(object_ball):
            pygame.time.delay(250)
            if hit_detected_post:
                score += 1
            else:
                fouls += 1
                foul_committed = True
            reset_balls()
            turn = 1 if practice_mode else 3 - turn
            shot_taken = False
        else:
            object_velocity[0] *= friction
            object_velocity[1] *= friction
            if abs(object_velocity[0]) < velocity_threshold:
                object_velocity[0] = 0.0
            if abs(object_velocity[1]) < velocity_threshold:
                object_velocity[1] = 0.0

            if abs(object_velocity[0]) < velocity_threshold and abs(object_velocity[1]) < velocity_threshold:
                object_velocity = [0.0, 0.0]
                object_in_motion = False

                # Foul if no post hit during the shot
                if not hit_detected_post:
                    fouls += 1
                    foul_committed = True
                    reset_balls()
                turn = 1 if practice_mode else 3 - turn
                shot_taken = False

    # Switch turn when both balls stopped, shot was taken, and no foul committed
    if (abs(cue_velocity[0]) < velocity_threshold and abs(cue_velocity[1]) < velocity_threshold and
        abs(object_velocity[0]) < velocity_threshold and abs(object_velocity[1]) < velocity_threshold and
        shot_taken and not foul_committed):
        turn = 1 if practice_mode else 3 - turn
        shot_taken = False
        print(f"Turn switched to {'You' if turn == 1 else 'AI'}")

    # AI turn
    if (turn == 2 and
        abs(cue_velocity[0]) < velocity_threshold and abs(cue_velocity[1]) < velocity_threshold and
        abs(object_velocity[0]) < velocity_threshold and abs(object_velocity[1]) < velocity_threshold and
        not shot_taken and not practice_mode):
        ai_take_shot()

    # Foul checks if cue ball pockets or goes off table or object ball off table
    if detect_pocket(cue_ball) or is_off_table(cue_ball) or is_off_table(object_ball):
        fouls += 1
        foul_committed = True
        reset_balls()
        turn = 1 if practice_mode else 3 - turn
        shot_taken = False
        print(f"Foul occurred, turn switched to {'You' if turn == 1 else 'AI'}")

    draw_table()

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
    

