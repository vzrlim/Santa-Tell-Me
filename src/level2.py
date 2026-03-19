"""
Level 2: Present Delivery Mission — Maze Escape
"""
import pygame
import random
import math
import os
from collections import deque

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    SPRITES_DIR, ITEMS_DIR, BACKGROUNDS_DIR, UI_DIR, BGM_DIR, SFX_DIR,
    STATE_GAME_OVER, STATE_VICTORY,
    LEVEL2_TIMER, TIME_BONUS, HUNTER_PATHFIND_INTERVAL, ANIMATION_SPEED,
    MAZE_GRID, MAZE_COLS, MAZE_ROWS, MAZE_TILE_SIZE,
    SPRITESHEET_CONFIG,
    SANTA_MAZE_SPEED, HUNTER_SPEED_PPS,
    SANTA_DISPLAY, HUNTER_DISPLAY, TREE_DISPLAY, HOURGLASS_DISPLAY,
    SANTA_HITBOX, HUNTER_COUNT, HUNTER_ATTACK_RANGE, HOURGLASS_COUNT,
    HUNTER_KILL_SCORE, ATTACK_RANGE, ATTACK_COOLDOWN
)
from src.utils import load_spritesheet, load_image, draw_text, Animator, ParticleEmitter

TILE = MAZE_TILE_SIZE
_SAFE_CELLS = None

def _compute_safe_cells():
    global _SAFE_CELLS
    if _SAFE_CELLS is not None: return
    _SAFE_CELLS = set()
    for r in range(MAZE_ROWS):
        for c in range(MAZE_COLS):
            if all(0 <= c + dc < MAZE_COLS and 0 <= r + dr < MAZE_ROWS and MAZE_GRID[r + dr][c + dc] == 0 for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
                _SAFE_CELLS.add((c, r))

def is_wall(col, row):
    if col < 0 or col >= MAZE_COLS or row < 0 or row >= MAZE_ROWS: return True
    return MAZE_GRID[row][col] == 1

def pixel_to_cell(px, py): return int(px) // TILE, int(py) // TILE
def cell_center(col, row): return col * TILE + TILE // 2, row * TILE + TILE // 2
def all_path_cells():
    _compute_safe_cells()
    return sorted(_SAFE_CELLS)

def _simplify_path(path):
    if len(path) <= 2: return path
    result = [path[0]]
    for i in range(1, len(path) - 1):
        d1 = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        d2 = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        if d1 != d2: result.append(path[i])
    result.append(path[-1])
    return result

def bfs(sc, sr, gc, gr):
    if sc == gc and sr == gr: return []
    parent = {(sc, sr): None}
    queue = deque([(sc, sr)])
    while queue:
        col, row = queue.popleft()
        for dc, dr in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nc, nr = col + dc, row + dr
            if (nc, nr) not in parent and (nc, nr) in _SAFE_CELLS:
                parent[(nc, nr)] = (col, row)
                if nc == gc and nr == gr:
                    path = []
                    cur = (gc, gr)
                    while cur != (sc, sr):
                        path.append(cur)
                        cur = parent[cur]
                    path.reverse()
                    return _simplify_path(path)
                queue.append((nc, nr))
    return []

class Santa:
    def __init__(self, x, y, sprites):
        self.x, self.y = float(x), float(y)
        self.sprites = sprites
        self.direction, self.last_horizontal = 'down', 'right'
        self.charges = 0
        self.attack_cooldown = 0.0

    @property
    def rect(self):
        h = SANTA_HITBOX
        return pygame.Rect(int(self.x) - h, int(self.y) - h, h * 2, h * 2)

    def _passable(self, nx, ny):
        h = SANTA_HITBOX - 1
        for px, py in ((nx - h, ny - h), (nx + h, ny - h), (nx - h, ny + h), (nx + h, ny + h)):
            if is_wall(int(px) // TILE, int(py) // TILE): return False
        return True

    def update(self, dt, keys):
        dx = dy = 0
        if keys[pygame.K_LEFT]: dx, self.direction, self.last_horizontal = -SANTA_MAZE_SPEED, 'left', 'left'
        elif keys[pygame.K_RIGHT]: dx, self.direction, self.last_horizontal = SANTA_MAZE_SPEED, 'right', 'right'
        elif keys[pygame.K_UP]: dy, self.direction = -SANTA_MAZE_SPEED, 'up'
        elif keys[pygame.K_DOWN]: dy, self.direction = SANTA_MAZE_SPEED, 'down'
        moving = bool(dx or dy)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        if dx:
            nx = self.x + dx * dt
            if self._passable(nx, self.y): self.x = nx
        if dy:
            ny = self.y + dy * dt
            if self._passable(self.x, ny): self.y = ny
        anim_key = 'right' if self.direction in ('left', 'right') else self.direction
        if moving: self.sprites[anim_key].update(dt)
        else: self.sprites[anim_key].index = self.sprites[anim_key].timer = 0

    def draw(self, surface):
        anim_key = 'right' if self.direction in ('left', 'right') else self.direction
        frame = self.sprites[anim_key].get_frame()
        if self.direction == 'left' or (self.direction in ('up', 'down') and self.last_horizontal == 'left'):
            frame = pygame.transform.flip(frame, True, False)
        surface.blit(frame, frame.get_rect(center=(int(self.x), int(self.y))))

class Hunter:
    def __init__(self, x, y, walk_frames, attack_frames):
        self.x, self.y = float(x), float(y)
        self.walk_anim, self.attack_anim = Animator(walk_frames, ANIMATION_SPEED), Animator(attack_frames, ANIMATION_SPEED)
        self.attacking = False
        self.path, self.path_timer, self.facing_left = [], 0.0, False

    @property
    def rect(self):
        h = SANTA_HITBOX
        return pygame.Rect(int(self.x) - h, int(self.y) - h, h * 2, h * 2)

    @staticmethod
    def _passable(nx, ny):
        h = SANTA_HITBOX - 1
        for px, py in ((nx - h, ny - h), (nx + h, ny - h), (nx - h, ny + h), (nx + h, ny + h)):
            if is_wall(int(px) // TILE, int(py) // TILE): return False
        return True

    def update(self, dt, santa_x, santa_y):
        self.path_timer -= dt
        if self.path_timer <= 0:
            sc, sr = pixel_to_cell(santa_x, santa_y)
            hc, hr = pixel_to_cell(self.x, self.y)
            
            # --- AI NERF ---
            # Only track perfectly if within 400px. Otherwise, wander randomly to break the swarm.
            dist_to_santa = math.hypot(santa_x - self.x, santa_y - self.y)
            if dist_to_santa < 400:
                target_c, target_r = sc, sr
            else:
                target_c, target_r = random.choice(all_path_cells())
                
            new_path = bfs(hc, hr, target_c, target_r)
            
            while new_path:
                wc, wr = new_path[0]
                wx, wy = cell_center(wc, wr)
                if math.hypot(wx - self.x, wy - self.y) < TILE * 0.5: new_path.pop(0)
                else: break
            if new_path: self.path = new_path
            self.path_timer = HUNTER_PATHFIND_INTERVAL
            
        if self.path:
            tc, tr = self.path[0]
            tx, ty = cell_center(tc, tr)
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            step = HUNTER_SPEED_PPS * dt
            if dist <= step:
                if self._passable(tx, ty):
                    self.x, self.y = float(tx), float(ty)
                    if abs(dx) > abs(dy): self.facing_left = dx < 0
                self.path.pop(0)
            else:
                nx, ny = self.x + dx / dist * step, self.y + dy / dist * step
                if self._passable(nx, ny): self.x, self.y = nx, ny
                elif self._passable(nx, self.y): self.x = nx
                elif self._passable(self.x, ny): self.y = ny
                else: self.path, self.path_timer = [], 0.0
                if abs(dx) > abs(dy): self.facing_left = dx < 0
        self.attacking = math.hypot(santa_x - self.x, santa_y - self.y) < HUNTER_ATTACK_RANGE
        if self.attacking: self.attack_anim.update(dt)
        else: self.attack_anim.reset(); self.walk_anim.update(dt)

    def draw(self, surface):
        frame = self.attack_anim.get_frame() if self.attacking else self.walk_anim.get_frame()
        if self.facing_left: frame = pygame.transform.flip(frame, True, False)
        surface.blit(frame, frame.get_rect(center=(int(self.x), int(self.y))))

class Hourglass:
    def __init__(self, x, y, image):
        self.x, self.base_y, self.y = float(x), float(y), float(y)
        self.image, self.phase, self.collected = image, random.uniform(0, math.pi * 2), False

    @property
    def rect(self):
        hw, hh = HOURGLASS_DISPLAY[0] // 2, HOURGLASS_DISPLAY[1] // 2
        return pygame.Rect(self.x - hw, self.y - hh, HOURGLASS_DISPLAY[0], HOURGLASS_DISPLAY[1])

    def update(self, dt):
        self.phase += dt * 3.0
        self.y = self.base_y + math.sin(self.phase) * 3

    def draw(self, surface):
        glow_r = int(HOURGLASS_DISPLAY[0] + math.sin(self.phase) * 2)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 220, 80, 55), (glow_r, glow_r), glow_r)
        surface.blit(glow, (int(self.x) - glow_r, int(self.y) - glow_r))
        surface.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))

def run_level2(screen, clock, score=0):
    pygame.mixer.music.stop()
    level_bgm = os.path.join(BGM_DIR, "level2_bgm.mp3")
    if os.path.exists(level_bgm):
        pygame.mixer.music.load(level_bgm)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

    cfg = SPRITESHEET_CONFIG
    santa_sprites = {
        'down': Animator(load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_floating"][0]), cfg["santa_floating"][1], SANTA_DISPLAY), ANIMATION_SPEED),
        'right': Animator(load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_right"][0]), cfg["santa_right"][1], SANTA_DISPLAY), ANIMATION_SPEED),
        'up': Animator(load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_floating"][0]), cfg["santa_floating"][1], SANTA_DISPLAY), ANIMATION_SPEED),
    }
    hunter_walk_frames = load_spritesheet(os.path.join(SPRITES_DIR, cfg["hunter_walk"][0]), cfg["hunter_walk"][1], HUNTER_DISPLAY)
    hunter_attack_frames = load_spritesheet(os.path.join(SPRITES_DIR, cfg["hunter_attack"][0]), cfg["hunter_attack"][1], HUNTER_DISPLAY)
    maze_bg = load_image(os.path.join(BACKGROUNDS_DIR, 'maze_bg.png'))
    tree_img, hg_img, kill_icon = load_image(os.path.join(ITEMS_DIR, 'christmass_tree.png'), TREE_DISPLAY), load_image(os.path.join(ITEMS_DIR, 'santa_hourglass.png'), HOURGLASS_DISPLAY), load_image(os.path.join(UI_DIR, 'kill_icon.png'), (28, 28))
    
    paths = all_path_cells()
    start_cell = next((c for c in paths if c[0] < MAZE_COLS // 4 and c[1] < MAZE_ROWS // 4), paths[0])
    sx, sy = cell_center(*start_cell)
    santa = Santa(sx, sy, santa_sprites)
    
    end_candidates = [(c, r) for c, r in paths if c > MAZE_COLS * 3 // 4 and r > MAZE_ROWS * 3 // 4]
    tree_x, tree_y = cell_center(*(random.choice(end_candidates) if end_candidates else paths[-1]))
    
    hunter_pool = [(c, r) for c, r in paths if math.hypot(c * TILE - sx, r * TILE - sy) > 300]
    random.shuffle(hunter_pool)
    hunters = [Hunter(*cell_center(*hunter_pool[i]), [f.copy() for f in hunter_walk_frames], [f.copy() for f in hunter_attack_frames]) for i in range(min(HUNTER_COUNT, len(hunter_pool)))]
    
    hg_pool = [(c, r) for c, r in paths if math.hypot(c * TILE - sx, r * TILE - sy) > 120 and math.hypot(c * TILE - tree_x, r * TILE - tree_y) > 80]
    random.shuffle(hg_pool)
    hourglasses = [Hourglass(*cell_center(*hg_pool[i]), hg_img) for i in range(min(HOURGLASS_COUNT, len(hg_pool)))]
    
    time_left, particles, hunter_kills, outcome, end_msg, result_delay = float(LEVEL2_TIMER), ParticleEmitter(), 0, None, '', 2.5
    sfx = {}
    for name, filename in (('pickup', 'item_pickup.wav'), ('clear', 'level_clear.wav'), ('over', 'game_over.wav'), ('attack', 'santa_attack.wav'), ('hunter_die', 'hunter_die.wav')):
        path = os.path.join(SFX_DIR, filename)
        if os.path.exists(path): sfx[name] = pygame.mixer.Sound(path)

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return {"next_state": STATE_GAME_OVER, "score": score}
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return {"next_state": STATE_GAME_OVER, "score": score}
            if event.type == pygame.KEYDOWN and event.key == pygame.K_w and outcome is None and santa.charges > 0 and santa.attack_cooldown <= 0:
                nearest, nearest_dist = None, ATTACK_RANGE
                for h in hunters:
                    d = math.hypot(h.x - santa.x, h.y - santa.y)
                    if d <= nearest_dist: nearest_dist, nearest = d, h
                if nearest:
                    hunters.remove(nearest); score, hunter_kills, santa.charges, santa.attack_cooldown = score + HUNTER_KILL_SCORE, hunter_kills + 1, santa.charges - 1, ATTACK_COOLDOWN
                    particles.emit(nearest.x, nearest.y, 40, color=(255, 100, 50), speed_range=(60, 200))
                    if 'hunter_die' in sfx: sfx['hunter_die'].play()
                if 'attack' in sfx: sfx['attack'].play()
        
        if outcome is None:
            santa.update(dt, pygame.key.get_pressed())
            for h in hunters: h.update(dt, santa.x, santa.y)
            for hg in hourglasses: hg.update(dt)
            time_left = max(0.0, time_left - dt)
            
            for h in hunters:
                if santa.rect.colliderect(h.rect): outcome, end_msg = 'game_over', 'Caught by Hunter!'; break
            for hg in hourglasses[:]:
                if santa.rect.colliderect(hg.rect):
                    hg.collected, time_left, santa.charges = True, time_left + TIME_BONUS, santa.charges + 1
                    particles.emit(hg.x, hg.y, 25, color=(255, 220, 80))
                    if 'pickup' in sfx: sfx['pickup'].play()
            hourglasses = [hg for hg in hourglasses if not hg.collected]
            
            if outcome is None and santa.rect.colliderect(tree_img.get_rect(center=(tree_x, tree_y))):
                outcome, end_msg, score = 'victory', 'Gift Delivered!', score + int(time_left) * 10
                if 'clear' in sfx: sfx['clear'].play()
                _spawn_fireworks(particles)
            if time_left <= 0 and outcome is None: outcome, end_msg = 'game_over', "Time's Up!"
        else:
            result_delay -= dt
            if result_delay <= 0: return {"next_state": STATE_VICTORY if outcome == 'victory' else STATE_GAME_OVER, "score": score}
            
        particles.update(dt); screen.blit(maze_bg, (0, 0)); screen.blit(tree_img, tree_img.get_rect(center=(tree_x, tree_y)))
        for hg in hourglasses: hg.draw(screen)
        for h in hunters: h.draw(screen)
        santa.draw(screen); particles.draw(screen); _draw_hud(screen, time_left, score, santa.charges, hunter_kills, kill_icon, hg_img)
        
        if outcome:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 140)); screen.blit(overlay, (0, 0))
            draw_text(screen, end_msg, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40), size=68, color=((255, 220, 50) if outcome == 'victory' else (255, 80, 80)), center=True)
            if outcome == 'victory': draw_text(screen, f"Time Bonus: +{int(time_left) * 10} pts", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30), size=36, color=(255, 255, 180), center=True)
            draw_text(screen, f"Total Score: {score}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80), size=36, color=(255, 255, 255), center=True)
        pygame.display.flip()

def _spawn_fireworks(particles):
    for _ in range(5): particles.emit(random.randint(80, SCREEN_WIDTH-80), random.randint(80, SCREEN_HEIGHT-80), 30, color=random.choice([(255,80,80), (80,255,80), (80,80,255)]), speed_range=(60, 220))

def _draw_hud(surface, time_left, score, charges, hunter_kills, kill_icon, hg_img):
    bar = pygame.Surface((SCREEN_WIDTH, 44), pygame.SRCALPHA); bar.fill((0, 0, 0, 150)); surface.blit(bar, (0, 0))
    draw_text(surface, f"TIME {int(time_left)//60:02d}:{int(time_left)%60:02d}", (SCREEN_WIDTH // 2, 6), size=36, color=((255, 80, 80) if time_left < 30 else (255, 255, 255)), center=True)
    draw_text(surface, f"Score: {score}", (SCREEN_WIDTH - 150, 8), size=32, color=(255, 255, 255))
    draw_text(surface, f"Power x{charges}", (8, 10), size=24, color=((255, 220, 80) if charges > 0 else (150, 150, 150)))
    surface.blit(kill_icon, (90, 8)); draw_text(surface, f"x{hunter_kills}", (122, 10), size=28, color=(255, 180, 80))