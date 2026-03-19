"""
Ending Degradation Photos
"""
import pygame
import os
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, NARRATIVE_DIR, STATE_MENU, PLAYER_DATA
from src.utils import draw_text, load_image

def _run_final_ending(screen, clock):
    """The real ending — MC erased from family photo. '...at what cost?'"""
    bg_path = os.path.join(NARRATIVE_DIR, "family_loop_final.png")
    bg = load_image(bg_path, scale=(SCREEN_WIDTH, SCREEN_HEIGHT)) if os.path.exists(bg_path) else None

    LINES = [
        "The house is very quiet now.",
        "Mom and Dad are smiling at the photograph.",
        "There is a gap where someone used to stand.",
        "They do not seem to notice.",
        "",
        "...at what cost?"
    ]

    alpha = 0
    fade_in = True
    done = False

    while not done:
        dt = clock.tick(FPS) / 1000.0
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and not fade_in:
                done = True

        if fade_in:
            alpha = min(255, alpha + 40 * dt)
            if alpha >= 255:
                fade_in = False

        if bg:
            bg.set_alpha(int(alpha))
            screen.blit(bg, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(alpha * 0.75)))
        screen.blit(overlay, (0, 0))

        font_reg  = pygame.font.SysFont("georgia", 24)
        font_big  = pygame.font.SysFont("georgia", 42, bold=True)
        y = SCREEN_HEIGHT // 2 - 120
        for line in LINES:
            if not line:
                y += 20; continue
            f = font_big if line.startswith("...") else font_reg
            col = (160, 20, 20) if line.startswith("...") else (200, 200, 200)
            s = f.render(line, True, col)
            s.set_alpha(int(alpha))
            screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, y))
            y += f.get_linesize() + 6

        if not fade_in:
            hint = pygame.font.SysFont("courier", 16).render("[Press any key to exit]", True, (60, 60, 60))
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 40))

        pygame.display.flip()

def run_vignette(screen, clock):
    VIGNETTES = {
        1: ["The living room was so bright when I pulled the toy away.", "I tried to walk toward the kitchen, but my shoulder caught the doorframe.", "Dad asked if I was clumsy or just sleepy.", "I told him the snow glare was playing tricks on my eyes.", "I told myself that. I will tell myself that tomorrow, too."],
        2: ["'Are you going to eat your cake, sweetheart?' Mom's smile was pinned.", "I opened my mouth to tell her I wasn't hungry.", "I felt the shape of the words on my tongue.", "'Well? Don't be rude,' Dad said, tapping his coffee mug.", "I screamed that I was sorry. They just kept waiting for a sound."],
        3: ["There was a toy. It was red, I think. Plastic.", "Mom gave me something sweet. Or did she say it was bitter?", "I know there were rules. Four of them? No, four is just a number.", "It's my birthday, but I don't know how old I am.", "The old man in the red suit was laughing. I can't remember my name."],
    }
    
    loop = PLAYER_DATA["loop_count"]
    
    # If they hit loop 4, run the final ending and return to menu immediately
    if loop >= 4:
        _run_final_ending(screen, clock)
        return STATE_MENU
        
    lines = VIGNETTES[loop]
    
    bg_path = os.path.join(NARRATIVE_DIR, f"family_loop{loop}.png")
    bg = load_image(bg_path, scale=(SCREEN_WIDTH, SCREEN_HEIGHT)) if os.path.exists(bg_path) else None

    alpha = 0
    fade_in = True

    while True:
        dt = clock.tick(FPS) / 1000.0
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            # On ENTER, the run is officially over. Return to the Main Menu.
            # The loop count logic is handled by main.py if they failed earlier.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not fade_in:
                return STATE_MENU

        if fade_in:
            alpha += 50 * dt
            if alpha >= 255:
                alpha = 255
                fade_in = False

        if bg:
            bg.set_alpha(int(alpha))
            screen.blit(bg, (0,0))
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(alpha * 0.7)))
        screen.blit(overlay, (0,0))

        font = pygame.font.SysFont("georgia", 24)
        for i, line in enumerate(lines):
            text_surf = font.render(line, True, (200, 200, 200))
            text_surf.set_alpha(int(alpha))
            rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, (SCREEN_HEIGHT // 2 - 100) + (i * 40)))
            screen.blit(text_surf, rect)

        if not fade_in:
            hint = pygame.font.SysFont("courier", 16).render("[Press ENTER to end the session]", True, (60, 60, 60))
            screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, SCREEN_HEIGHT - 40))

        pygame.display.flip()