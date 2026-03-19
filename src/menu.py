"""
Game Start Page - Santa Tell Me (Analog Horror Menu)
"""
import pygame
import os
import math
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WHITE, RED, MAROON, VINTAGE_YELLOW, BACKGROUNDS_DIR, NARRATIVE_DIR, BGM_DIR,
    STATE_STORY, PLAYER_DATA
)
from src.utils import draw_text, load_image

def run_menu(screen, clock):
    bg_path = os.path.join(BACKGROUNDS_DIR, "forest_bg.png")
    bg = load_image(bg_path, scale=(SCREEN_WIDTH, SCREEN_HEIGHT)) if os.path.exists(bg_path) else None
    
    bgm_path = None
    candidates = [
        os.path.join(BGM_DIR, "menu_bgm.mp3"),
        os.path.join(BGM_DIR, "menu_bgm.ogg"),
        os.path.join(NARRATIVE_DIR, "music_box.mp3"),
        os.path.join(NARRATIVE_DIR, "music_box.ogg"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            bgm_path = candidate
            break
    
    if bgm_path:
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception: pass

    # Start directly at title, mic logic is completely gone
    phase = "title" 
    name_input = ""
    age_input = ""
    bgm_muted = False
    surveillance_timer = 0

    pygame.key.start_text_input()

    while True:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input()
                pygame.quit(); raise SystemExit
            
            if phase == "title":
                mute_rect = pygame.Rect(SCREEN_WIDTH - 150, 20, 130, 40)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if mute_rect.collidepoint(mouse_pos) and not bgm_muted:
                        pygame.mixer.music.set_volume(0.0)
                        bgm_muted = True
                        phase = "surveillance"; surveillance_timer = 8.0
                    else: phase = "input_name"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    phase = "input_name"
            
            elif phase == "input_name":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and name_input.strip():
                        PLAYER_DATA["name"] = name_input.strip()
                        phase = "input_age"
                    elif event.key == pygame.K_BACKSPACE: name_input = name_input[:-1]
                elif event.type == pygame.TEXTINPUT:
                    if len(name_input) < 25: name_input += event.text
            
            elif phase == "input_age":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and age_input.strip():
                        PLAYER_DATA["age"] = age_input.strip()
                        pygame.mixer.music.fadeout(1000)
                        pygame.key.stop_text_input()
                        return STATE_STORY 
                    elif event.key == pygame.K_BACKSPACE: age_input = age_input[:-1]
                elif event.type == pygame.TEXTINPUT:
                    if len(age_input) < 3 and event.text.isdigit():
                        age_input += event.text

        # --- DRAWING ---
        screen.fill((5, 5, 5))
        if phase == "title":
            if bg: screen.blit(bg, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200)); screen.blit(overlay, (0, 0))
            draw_text(screen, "Santa Tell Me", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3), size=80, color=VINTAGE_YELLOW, center=True, font_name="georgia")
            draw_text(screen, "are you really there...", (SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT // 3 + 70), size=28, color=(150, 150, 150), center=True, font_name="courier")
            draw_text(screen, "Use arrow keys to run. Do not look away.", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120), size=18, color=MAROON, center=True, font_name="courier")
            draw_text(screen, "[Press ENTER or Click to step inside]", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80), size=22, color=(100, 100, 100), center=True)
            mute_color = (100, 100, 100) if not bgm_muted else (50, 50, 50)
            mute_rect = pygame.Rect(SCREEN_WIDTH - 150, 20, 130, 40)
            pygame.draw.rect(screen, mute_color, mute_rect, 1)
            draw_text(screen, "MUTE BGM", mute_rect.center, size=18, color=mute_color, center=True)
        elif phase == "surveillance":
            screen.fill((0, 0, 0)); surveillance_timer -= dt
            pulse = abs(math.sin(surveillance_timer * 1.8)) * 0.6 + 0.2
            vign = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for ri in range(60, 0, -3):
                a = max(0, int((1 - ri / 60) * 80 * pulse))
                pygame.draw.rect(vign, (80, 0, 0, a), (ri * 10, ri * 5, SCREEN_WIDTH - ri * 20, SCREEN_HEIGHT - ri * 10), 4)
            screen.blit(vign, (0, 0))
            full1, full2, full3 = "...that's why I said this isn't for the weak-hearted.", "But we will let you proceed.", "In silence."
            elapsed = 8.0 - surveillance_timer   
            reveal1 = full1[:max(0, int(elapsed * 22))]
            reveal2 = full2[:max(0, int((elapsed - 2.5) * 22))] if elapsed > 2.5 else ""
            reveal3 = full3[:max(0, int((elapsed - 4.5) * 22))] if elapsed > 4.5 else ""
            f_courier = pygame.font.SysFont("courier", 26)
            for i, (text, col) in enumerate([(reveal1, (180, 20, 20)), (reveal2, (120, 10, 10)), (reveal3, (80, 5, 5))]):
                if text:
                    s = f_courier.render(text, True, col)
                    screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, SCREEN_HEIGHT // 2 - 30 + i * 50))
            if surveillance_timer <= 0: phase = "input_name"
        elif phase == "input_name":
            draw_text(screen, "Hi.", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60), size=32, color=WHITE, center=True)
            draw_text(screen, "What is your name?", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20), size=24, color=(150, 150, 150), center=True)
            draw_text(screen, name_input + "_", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30), size=36, color=VINTAGE_YELLOW, center=True)
        elif phase == "input_age":
            draw_text(screen, f"Hello, {PLAYER_DATA['name']}.", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60), size=32, color=WHITE, center=True)
            draw_text(screen, "How old are you turning today?", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20), size=24, color=(150, 150, 150), center=True)
            draw_text(screen, age_input + "_", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30), size=36, color=VINTAGE_YELLOW, center=True)
        pygame.display.flip()