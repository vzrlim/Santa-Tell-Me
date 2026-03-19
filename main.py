"""
Game Main Entrance - Santa Tell Me
"""
import pygame
import sys
import os

if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-10) 
    mode = ctypes.c_uint32()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value &= ~0x0040 
    kernel32.SetConsoleMode(handle, mode)

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE,
    STATE_MENU, STATE_STORY, STATE_LEVEL1, STATE_LEVEL2,
    STATE_GAME_OVER, STATE_VICTORY, STATE_RIDDLE, STATE_VIGNETTE,
    PLAYER_DATA, WHITE, NARRATIVE_DIR
)

from src.menu import run_menu
from src.story import run_story
from src.level1 import run_level1
from src.level2 import run_level2
from src.game_over import run_game_over
from src.riddle import run_riddle
from src.vignette import run_vignette
from src.utils import draw_text, load_image

def run_reincarnation_transition(screen, clock):
    """Throws the player back into the pixel world after a failed quiz."""
    bg_path = os.path.join(NARRATIVE_DIR, "reincarnation_bg.png")
    bg = load_image(bg_path, scale=(SCREEN_WIDTH, SCREEN_HEIGHT)) if os.path.exists(bg_path) else None
    timer = 3.5
    while timer > 0:
        dt = clock.tick(FPS) / 1000.0
        timer -= dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        screen.fill((0,0,0))
        if bg: screen.blit(bg, (0,0))
        draw_text(screen, "You are thrown back into the cold...", (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), size=36, color=WHITE, center=True, font_name="georgia")
        pygame.display.flip()

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    clock = pygame.time.Clock()

    state = STATE_MENU
    score = 0

    while True:
        if state == STATE_MENU:
            state = run_menu(screen, clock)
            score = 0
            PLAYER_DATA["loop_count"] = 1
            PLAYER_DATA["current_keyword"] = None

        elif state == STATE_STORY:
            state = run_story(screen, clock)

        elif state == STATE_LEVEL1:
            result = run_level1(screen, clock)
            state = result["next_state"]
            score = result.get("score", 0)

        elif state == STATE_LEVEL2:
            result = run_level2(screen, clock, score)
            state = result["next_state"]
            score = result.get("score", score)

        elif state == STATE_GAME_OVER:
            state = run_game_over(screen, clock, score, victory=False)

        elif state == STATE_VICTORY:
            # If they survived Loop 4, they skip the quiz and go straight to the final ending.
            if PLAYER_DATA["loop_count"] >= 4:
                state = STATE_VIGNETTE
            else:
                state = run_game_over(screen, clock, score, victory=True)

        elif state == STATE_RIDDLE:
            result_state = run_riddle(screen, clock)
            if result_state == "pass":
                state = STATE_VIGNETTE
            elif result_state == "fail":
                PLAYER_DATA["loop_count"] += 1
                run_reincarnation_transition(screen, clock)
                state = STATE_LEVEL1

        elif state == STATE_VIGNETTE:
            state = run_vignette(screen, clock)

        else:
            break

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"[ERROR] Engine Crash: {e}")
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)