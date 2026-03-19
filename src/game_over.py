"""
Hijacked Game Over / Tally Screens / Riddle Engine - Santa Tell Me
"""
import pygame
import random
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WHITE, RED, MAROON, VINTAGE_YELLOW,
    STATE_MENU, STATE_RIDDLE
)
from src.utils import draw_text

def apply_glitch(screen):
    """Creates a raw CRT screen-tear effect."""
    for _ in range(8):
        y = random.randint(0, SCREEN_HEIGHT)
        h = random.randint(10, 40)
        slice_rect = pygame.Rect(0, y, SCREEN_WIDTH, h)
        try:
            slice_surf = screen.subsurface(slice_rect).copy()
            if random.choice([True, False]):
                slice_surf.fill((50, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(slice_surf, (random.randint(-30, 30), y))
            pygame.draw.line(screen, (0,0,0), (0, y+h//2), (SCREEN_WIDTH, y+h//2), random.randint(1,3))
        except ValueError: pass

def run_game_over(screen, clock, score, victory=False):
    pygame.mixer.music.stop()
    
    phase_timer = 2.5  # Time before the hijack triggers (NO BUTTONS)
    hijack_triggered = False
    glitch_timer = 4.0 # Time the horror stays on screen before advancing

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit

        screen.fill((10, 10, 30))

        if not hijack_triggered:
            phase_timer -= dt
            if phase_timer <= 0:
                hijack_triggered = True

            # NORMAL BORING UI
            title = "VICTORY! Merry Christmas!" if victory else "GAME OVER"
            color = VINTAGE_YELLOW if victory else RED
            draw_text(screen, title, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3), size=50, color=color, center=True)
            draw_text(screen, f"Total Score: {score}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), size=30, color=WHITE, center=True)
        else:
            # THE HORROR TAKES OVER
            glitch_timer -= dt
            apply_glitch(screen)
            
            if not victory:
                # VALOUR ROUTE (Died)
                screen.fill((50, 0, 0), special_flags=pygame.BLEND_RGB_ADD) 
                draw_text(screen, "Such a brave little soul. You fought well.", (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20), size=32, color=RED, center=True, font_name="georgia")
                draw_text(screen, "Valour tastes... so sweet.", (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20), size=36, color=MAROON, center=True, font_name="georgia")
                if glitch_timer <= 0:
                    return STATE_MENU # Die-die game over. Back to menu.
            else:
                # WIT ROUTE (Passed Pixel Game)
                fake_score = random.randint(1111, 9999) if glitch_timer > 0.5 else 4
                draw_text(screen, "VICTORY MELTING", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3), size=50, color=(100,100,100), center=True)
                draw_text(screen, f"Total Score: {fake_score}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), size=30, color=VINTAGE_YELLOW, center=True)
                draw_text(screen, "You escaped... how cunning. Let us test that wit.", (SCREEN_WIDTH//2, SCREEN_HEIGHT - 100), size=28, color=WHITE, center=True, font_name="georgia")
                
                if glitch_timer <= 0:
                    return STATE_RIDDLE # Push to Sphinx quiz

        pygame.display.flip()