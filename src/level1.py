"""
Level 1: Cross Snow Forest - The Frosty Forest Run
"""
import pygame
import os
import random
import math
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, RED,
    SPRITES_DIR, ITEMS_DIR, BACKGROUNDS_DIR, UI_DIR, BGM_DIR, SFX_DIR,
    SANTA_HP, LEVEL1_DURATION, KILL_SCORE,
    SANTA_SPEED, MAGIC_BALL_SPEED, SNOWBALL_SPEED,
    BG_SCROLL_SPEED, WILDMAN_SPEED,
    WILDMAN_SPAWN_INTERVAL, WILDMAN_SPAWN_MIN,
    ROAD_LEFT, ROAD_RIGHT,
    ANIMATION_SPEED, SCREEN_SHAKE_DURATION, SCREEN_SHAKE_INTENSITY,
    SPRITESHEET_CONFIG,
    STATE_LEVEL2, STATE_GAME_OVER
)
from src.utils import (
    load_spritesheet, load_image, draw_text,
    Animator, ParticleEmitter, SnowfallSystem, ScreenShake
)

class Santa(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.sprites = {}
        self._load_sprites()
        self.state = "idle"
        self.animator = Animator(self.sprites["fronts"], speed=ANIMATION_SPEED)
        self.image = self.animator.get_frame()
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = SANTA_HP
        self.speed = SANTA_SPEED
        self.invincible_timer = 0
        self.attack_cooldown = 0
        self.is_dead = False
        self.death_finished = False

    def _load_sprites(self):
        scale = (80, 80)
        cfg = SPRITESHEET_CONFIG
        self.sprites["fronts"] = load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_fronts"][0]), cfg["santa_fronts"][1], scale)
        right_frames = load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_right"][0]), cfg["santa_right"][1], scale)
        self.sprites["right"] = right_frames
        self.sprites["left"] = [pygame.transform.flip(f, True, False) for f in right_frames]
        self.sprites["attack"] = load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_attack"][0]), cfg["santa_attack"][1], scale)
        self.sprites["hurt"] = load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_hurts"][0]), cfg["santa_hurts"][1], scale)
        self.sprites["dead"] = load_spritesheet(os.path.join(SPRITES_DIR, cfg["santa_dead"][0]), cfg["santa_dead"][1], (100, 80))

    def set_state(self, state):
        if state != self.state and not self.is_dead:
            self.state = state
            if state == "move_left": self.animator = Animator(self.sprites["left"], speed=ANIMATION_SPEED)
            elif state == "move_right": self.animator = Animator(self.sprites["right"], speed=ANIMATION_SPEED)
            elif state == "attack": self.animator = Animator(self.sprites["attack"], speed=0.1, loop=False)
            elif state == "hurt": self.animator = Animator(self.sprites["hurt"], speed=0.1, loop=False)
            elif state == "dead": self.animator = Animator(self.sprites["dead"], speed=0.2, loop=False); self.is_dead = True
            else: self.animator = Animator(self.sprites["fronts"], speed=ANIMATION_SPEED)

    def take_damage(self):
        if self.invincible_timer <= 0 and not self.is_dead:
            self.hp -= 1
            self.invincible_timer = 1.0
            if self.hp <= 0: self.set_state("dead")
            else: self.set_state("hurt")
            return True
        return False

    def update(self, dt, keys):
        if self.is_dead:
            self.animator.update(dt)
            self.image = self.animator.get_frame()
            if self.animator.finished: self.death_finished = True
            return

        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)

        moving = False
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            if self.state not in ("attack", "hurt"): self.set_state("move_left")
            moving = True
        elif keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            if self.state not in ("attack", "hurt"): self.set_state("move_right")
            moving = True

        if not moving and self.state not in ("attack", "hurt", "dead"):
            self.set_state("idle")

        self.rect.clamp_ip(pygame.Rect(ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
        if self.state in ("attack", "hurt") and self.animator.finished:
            self.set_state("idle")

        self.animator.update(dt)
        self.image = self.animator.get_frame()

    def draw(self, surface, offset=(0, 0)):
        if self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2 == 0: return
        surface.blit(self.image, (self.rect.x + offset[0], self.rect.y + offset[1]))

class MagicBall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image(os.path.join(ITEMS_DIR, "santa_magic.png"), scale=(24, 24))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = MAGIC_BALL_SPEED

    def update(self, dt): self.rect.y -= self.speed
    def draw(self, surface, offset=(0, 0)): surface.blit(self.image, (self.rect.x + offset[0], self.rect.y + offset[1]))

class SnowBall(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = load_image(os.path.join(ITEMS_DIR, "wildmen_snow.png"), scale=(20, 20))
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = float(x), float(y)
        dx, dy = target_x - x, target_y - y
        dist = max(1, math.sqrt(dx * dx + dy * dy))
        self.vx, self.vy = (dx / dist) * SNOWBALL_SPEED, (dy / dist) * SNOWBALL_SPEED

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
    def draw(self, surface, offset=(0, 0)): surface.blit(self.image, (self.rect.x + offset[0], self.rect.y + offset[1]))

class Wildman(pygame.sprite.Sprite):
    SAFE_ZONE_Y = 150
    def __init__(self, side, santa_y):
        super().__init__()
        self._load_sprites()
        self.side = side
        if side == "right":
            for key in self.sprites: self.sprites[key] = [pygame.transform.flip(f, True, False) for f in self.sprites[key]]

        self.state = "run"
        self.animator = Animator(self.sprites["run"], speed=ANIMATION_SPEED)
        self.image = self.animator.get_frame()

        start_x = -50 if side == "left" else SCREEN_WIDTH + 50
        road_mid = (ROAD_LEFT + ROAD_RIGHT) // 2
        self.target_x = random.randint(ROAD_LEFT + 20, road_mid) if side == "left" else random.randint(road_mid, ROAD_RIGHT - 20)

        min_y, max_y = 80, SCREEN_HEIGHT * 2 // 3
        safe_lo, safe_hi = santa_y - self.SAFE_ZONE_Y, santa_y + self.SAFE_ZONE_Y
        valid_ranges = []
        if min_y < safe_lo: valid_ranges.append((min_y, int(safe_lo)))
        if safe_hi < max_y: valid_ranges.append((int(safe_hi), max_y))
        if valid_ranges:
            chosen = random.choice(valid_ranges)
            start_y = random.randint(chosen[0], chosen[1])
        else: start_y = min_y

        self.rect = self.image.get_rect(center=(start_x, start_y))
        self.x, self.y = float(self.rect.centerx), float(self.rect.centery)
        self.speed = WILDMAN_SPEED
        self.is_dead, self.death_finished = False, False
        self.idle_timer, self.throw_count, self.max_throws, self.lifetime = 0, 0, random.randint(3, 5), 0

    def _load_sprites(self):
        scale, cfg = (70, 70), SPRITESHEET_CONFIG
        self.sprites = {
            "run": load_spritesheet(os.path.join(SPRITES_DIR, cfg["wildman_run"][0]), cfg["wildman_run"][1], scale),
            "attack": load_spritesheet(os.path.join(SPRITES_DIR, cfg["wildman_attack"][0]), cfg["wildman_attack"][1], scale),
            "dead": load_spritesheet(os.path.join(SPRITES_DIR, cfg["wildman_dead"][0]), cfg["wildman_dead"][1], scale)
        }

    def set_state(self, new_state):
        if new_state != self.state:
            self.state = new_state
            if new_state == "run": self.animator = Animator(self.sprites["run"], speed=ANIMATION_SPEED)
            elif new_state == "idle": self.animator = Animator(self.sprites["run"][:1], speed=1.0)
            elif new_state == "attack": self.animator = Animator(self.sprites["attack"], speed=0.15, loop=False)
            elif new_state == "dead": self.animator = Animator(self.sprites["dead"], speed=0.15, loop=False); self.is_dead = True

    def die(self): self.set_state("dead")

    def update(self, dt, santa_rect):
        self.animator.update(dt)
        self.image = self.animator.get_frame()
        self.lifetime += dt

        if self.is_dead:
            self.y += BG_SCROLL_SPEED
            self.rect.center = (int(self.x), int(self.y))
            if self.animator.finished: self.death_finished = True
            return None

        if self.state == "run":
            dx = self.target_x - self.x
            if abs(dx) > 5:
                self.x += self.speed if dx > 0 else -self.speed
                self.rect.center = (int(self.x), int(self.y))
            else:
                self.x = self.target_x
                self.rect.center = (int(self.x), int(self.y))
                self.set_state("idle")
                self.idle_timer = random.uniform(0.3, 0.8)
        elif self.state == "idle":
            self.y += BG_SCROLL_SPEED
            self.rect.center = (int(self.x), int(self.y))
            self.idle_timer -= dt
            in_safe_zone = abs(self.y - santa_rect.centery) < self.SAFE_ZONE_Y
            if self.idle_timer <= 0 and not in_safe_zone:
                self.set_state("attack")
                return "throw"
        elif self.state == "attack":
            self.y += BG_SCROLL_SPEED
            self.rect.center = (int(self.x), int(self.y))
            if self.animator.finished:
                self.throw_count += 1
                if self.throw_count >= self.max_throws:
                    self.death_finished = True
                    return None
                self.set_state("idle")
                self.idle_timer = random.uniform(1.5, 3.0)
        if self.lifetime > 20: self.death_finished = True
        return None

    def draw(self, surface, offset=(0, 0)): surface.blit(self.image, (self.rect.x + offset[0], self.rect.y + offset[1]))

class HUD:
    def __init__(self):
        self.heart_full = load_image(os.path.join(UI_DIR, "heart_full.png"), scale=(32, 32))
        self.heart_empty = load_image(os.path.join(UI_DIR, "heart_empty.png"), scale=(32, 32))
        self.kill_icon = load_image(os.path.join(UI_DIR, "kill_icon.png"), scale=(32, 32))

    def draw(self, surface, hp, max_hp, kills, time_left):
        for i in range(max_hp):
            x, y = 10 + i * 36, 10
            surface.blit(self.heart_full if i < hp else self.heart_empty, (x, y))
        surface.blit(self.kill_icon, (SCREEN_WIDTH - 120, 10))
        draw_text(surface, str(kills), (SCREEN_WIDTH - 82, 12), size=28, color=WHITE)
        minutes, seconds = int(time_left) // 60, int(time_left) % 60
        draw_text(surface, f"{minutes}:{seconds:02d}", (SCREEN_WIDTH // 2, 12), size=28, color=WHITE, center=True)

def run_level1(screen, clock):
    pygame.mixer.music.stop()
    level_bgm = os.path.join(BGM_DIR, "level1_bgm.mp3")
    if os.path.exists(level_bgm):
        pygame.mixer.music.load(level_bgm)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

    bg = load_image(os.path.join(BACKGROUNDS_DIR, "forest_bg.png")).convert()
    bg_height, bg_y = bg.get_height(), 0.0
    city_gate = load_image(os.path.join(BACKGROUNDS_DIR, "city_gate.png")).convert()
    SEAM_H, _bg_w = 16, bg.get_width()

    bg_seam = pygame.Surface((_bg_w, SEAM_H))
    bg_seam.blit(bg, (0, 0), (0, bg_height - SEAM_H, _bg_w, SEAM_H))
    for _row in range(SEAM_H):
        _row_surf = pygame.Surface((_bg_w, 1))
        _row_surf.blit(bg, (0, 0), (0, _row, _bg_w, 1))
        _row_surf.set_alpha(int(255 * _row / SEAM_H))
        bg_seam.blit(_row_surf, (0, _row))

    gate_seam = pygame.Surface((_bg_w, SEAM_H))
    gate_seam.blit(city_gate, (0, 0), (0, bg_height - SEAM_H, _bg_w, SEAM_H))
    for _row in range(SEAM_H):
        _row_surf = pygame.Surface((_bg_w, 1))
        _row_surf.blit(bg, (0, 0), (0, _row, _bg_w, 1))
        _row_surf.set_alpha(int(255 * _row / SEAM_H))
        gate_seam.blit(_row_surf, (0, _row))

    santa = Santa((ROAD_LEFT + ROAD_RIGHT) // 2, SCREEN_HEIGHT - 100)
    snowfall, particle_emitter, screen_shake, hud = SnowfallSystem(count=80), ParticleEmitter(), ScreenShake(), HUD()
    wildmen, magic_balls, snowballs = [], [], []

    score, kills, time_elapsed, spawn_timer = 0, 0, 0, 0
    current_spawn_interval = WILDMAN_SPAWN_INTERVAL
    level_complete, game_over, game_over_delay = False, False, 2.0
    bg_phase, gate_draw_y, GATE_STOP_Y = "scrolling", 0.0, int(SCREEN_HEIGHT * 0.35)

    sfx = {}
    shoot_path, hurt_path = os.path.join(SFX_DIR, "magic_shoot.wav"), os.path.join(SFX_DIR, "santa_hurt.wav")
    if os.path.exists(shoot_path): sfx["shoot"] = pygame.mixer.Sound(shoot_path); sfx["shoot"].set_volume(0.3)
    if os.path.exists(hurt_path): sfx["hurt"] = pygame.mixer.Sound(hurt_path); sfx["hurt"].set_volume(0.4)

    class _EmptyKeys:
        def __getitem__(self, key): return 0
    _empty_keys = _EmptyKeys()

    while True:
        dt = clock.tick(FPS) / 1000.0
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(500)
                    return {"next_state": STATE_GAME_OVER, "score": score}
                if event.key == pygame.K_w and not santa.is_dead and santa.attack_cooldown <= 0 and bg_phase not in ("gate_entering", "gate_reached"):
                    santa.set_state("attack")
                    santa.attack_cooldown = 0.3
                    magic_balls.append(MagicBall(santa.rect.centerx, santa.rect.top))
                    if "shoot" in sfx: sfx["shoot"].play()

        if game_over or level_complete:
            game_over_delay -= dt
            if game_over_delay <= 0:
                pygame.mixer.music.fadeout(500)
                return {"next_state": STATE_LEVEL2 if level_complete else STATE_GAME_OVER, "score": score}

        time_elapsed += dt
        time_left = max(0, LEVEL1_DURATION - time_elapsed)
        current_spawn_interval = max(WILDMAN_SPAWN_MIN, WILDMAN_SPAWN_INTERVAL - (time_elapsed / LEVEL1_DURATION) * (WILDMAN_SPAWN_INTERVAL - WILDMAN_SPAWN_MIN))

        if bg_phase == "scrolling" and not santa.is_dead:
            spawn_timer += dt
            if spawn_timer >= current_spawn_interval:
                spawn_timer = 0
                wildmen.append(Wildman(random.choice(["left", "right"]), santa.rect.centery))

        if bg_phase == "scrolling":
            bg_y = (bg_y + BG_SCROLL_SPEED) % (bg_height * 2)
            if time_left <= 0 and not santa.is_dead:
                bg_phase, gate_draw_y = "gate_entering", float(int(bg_y) % bg_height - 2 * bg_height - 1)
        elif bg_phase == "gate_entering":
            bg_y += BG_SCROLL_SPEED
            gate_draw_y += BG_SCROLL_SPEED
            if gate_draw_y >= 0: gate_draw_y, bg_phase = 0.0, "gate_reached"
        elif bg_phase == "gate_reached":
            if not santa.is_dead and not level_complete:
                santa.rect.y -= santa.speed * 0.5
                santa.rect.clamp_ip(pygame.Rect(ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
                if santa.rect.centery <= GATE_STOP_Y:
                    santa.rect.centery, level_complete = GATE_STOP_Y, True

        santa.update(dt, _empty_keys if bg_phase == "gate_reached" else keys)
        if santa.death_finished and not game_over: game_over = True

        for ball in magic_balls[:]:
            ball.update(dt)
            if ball.rect.bottom < 0: magic_balls.remove(ball)

        for sb in snowballs[:]:
            sb.update(dt)
            if sb.rect.top > SCREEN_HEIGHT or sb.rect.bottom < 0 or sb.rect.left > SCREEN_WIDTH or sb.rect.right < 0:
                snowballs.remove(sb)

        for wm in wildmen[:]:
            if wm.update(dt, santa.rect) == "throw":
                snowballs.append(SnowBall(wm.rect.centerx, wm.rect.centery, santa.rect.centerx, santa.rect.centery))
            if wm.death_finished or wm.rect.top > SCREEN_HEIGHT + 100:
                wildmen.remove(wm)

        for ball in magic_balls[:]:
            for wm in wildmen[:]:
                if not wm.is_dead and ball.rect.colliderect(wm.rect):
                    wm.die(); magic_balls.remove(ball); kills += 1; score += KILL_SCORE
                    particle_emitter.emit(wm.rect.centerx, wm.rect.centery, 12, color=(200, 200, 255), speed_range=(30, 100))
                    break

        if not santa.is_dead:
            for sb in snowballs[:]:
                if sb.rect.colliderect(santa.rect):
                    snowballs.remove(sb)
                    if santa.take_damage():
                        screen_shake.start(SCREEN_SHAKE_DURATION, SCREEN_SHAKE_INTENSITY)
                        particle_emitter.emit(santa.rect.centerx, santa.rect.centery, 8, color=(255, 255, 255), speed_range=(40, 120))
                        if "hurt" in sfx: sfx["hurt"].play()

        snowfall.update(dt)
        particle_emitter.update(dt)
        screen_shake.update(dt)
        shake_offset = screen_shake.get_offset()

        if bg_phase == "scrolling":
            scroll_offset = int(bg_y) % bg_height
            start_y = scroll_offset - bg_height - 1
            for i in range(3): screen.blit(bg, (shake_offset[0], start_y + i * bg_height + shake_offset[1]))
            seam_y = start_y + bg_height - SEAM_H // 2
            if -SEAM_H < seam_y < SCREEN_HEIGHT: screen.blit(bg_seam, (shake_offset[0], seam_y + shake_offset[1]))
        elif bg_phase == "gate_entering":
            scroll_offset = int(bg_y) % bg_height
            start_y = scroll_offset - bg_height - 1
            for i in range(3): screen.blit(bg, (shake_offset[0], start_y + i * bg_height + shake_offset[1]))
            screen.blit(city_gate, (shake_offset[0], int(gate_draw_y) + shake_offset[1]))
            seam_y = start_y + bg_height - SEAM_H // 2
            if -SEAM_H < seam_y < SCREEN_HEIGHT: screen.blit(bg_seam, (shake_offset[0], seam_y + shake_offset[1]))
            gate_seam_y = int(gate_draw_y) + bg_height - SEAM_H // 2
            if -SEAM_H < gate_seam_y < SCREEN_HEIGHT: screen.blit(gate_seam, (shake_offset[0], gate_seam_y + shake_offset[1]))
        elif bg_phase == "gate_reached":
            screen.blit(city_gate, (shake_offset[0], shake_offset[1]))

        for wm in wildmen: wm.draw(screen, shake_offset)
        santa.draw(screen, shake_offset)
        for ball in magic_balls: ball.draw(screen, shake_offset)
        for sb in snowballs:
            for i in range(3):
                pygame.draw.circle(screen, (200, 200, 220), (int(sb.x - sb.vx * i * 3 + shake_offset[0]), int(sb.y - sb.vy * i * 3 + shake_offset[1])), max(1, 4 - i))
            sb.draw(screen, shake_offset)

        snowfall.draw(screen)
        particle_emitter.draw(screen, shake_offset)
        hud.draw(screen, santa.hp, SANTA_HP, kills, time_left)

        draw_text(screen, f"Score: {score}", (SCREEN_WIDTH // 2, 45), size=22, color=(255, 215, 0), center=True)

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100)); screen.blit(overlay, (0, 0))
            draw_text(screen, "GAME OVER", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), size=64, color=RED, center=True)
        elif level_complete:
            draw_text(screen, "LEVEL COMPLETE!", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), size=64, color=(255, 215, 0), center=True)

        pygame.display.flip()