"""
1950s Kitchen VN & Prophecy - Santa Tell Me
"""
import pygame
import os
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, 
    WHITE, MAROON, NARRATIVE_DIR, STATE_LEVEL1, PLAYER_DATA
)
from src.utils import draw_text, load_image

PROPHECY = [
    "Mind the colors, bold and bright,",
    "But do not trust your given sight.",
    "The first thought in your little head,",
    "Is just a trap where fools are led.",
    "",
    "A proper child will memorize,",
    "The secrets hidden in plain eyes.",
    "And when the universe keeps score,",
    "The only answer here is Four.",
    "",
    "Five pieces make a human whole,",
    "Four to shed to keep the soul.",
    "The brave are sweet and quickly chewed,",
    "While witty souls are bitter food."
]

def _build_dialogue():
    return {
    "start": [
        ("Mom", f"Happy birthday, sweetheart! Look at you, already {PLAYER_DATA['age']} years old. I made your favorite. Go on, take a bite."),
        ("Choice", "Take a bite", "I'm not hungry")
    ],
    "branch_1": [ 
        ("Mom", "Good child. Eat up."),
        ("Dad", "You're awfully quiet today, kiddo."),
        ("Choice", "I heard a noise outside.", "Why are you staring at me?")
    ],
    "branch_2": [ 
        ("Mom", "We don't waste food in this house."),
        ("Choice", "The cake looks... cold.", "[Try to leave the table]")
    ],
    "end_CRUEL": [ 
        ("Dad", "Just the winter wind. It can be CRUEL to those who wander off. Best stay inside with us.")
    ],
    "end_ANGER": [ 
        ("Dad", "Now, don't let your ANGER ruin this wonderful morning. We are a happy family.")
    ],
    "end_FROST": [ 
        ("Mom", "Don't be ungrateful. If it tastes a little bitter, darling, it's just the FROST.")
    ],
    "end_SOOTY": [ 
        ("Mom", "Sit down. Stay away from the fireplace, you'll get your new clothes all SOOTY.")
    ],
    "viewfinder": [
        ("Dad", "Before you ruin the mood, we got you a special present."),
        ("Dad", "Take a look inside, kiddo."),
        ("Prompt", "[Look Inside]")
    ]
    }

def render_dialogue_text(screen, speaker, text, box_rect):
    font_normal = pygame.font.SysFont("georgia", 24)
    font_bold = pygame.font.SysFont("georgia", 24, bold=True)
    screen.blit(font_bold.render(f"{speaker}:", True, (200, 180, 150)), (box_rect.x + 20, box_rect.y + 20))
    words = text.split(" ")
    x, y = box_rect.x + 20, box_rect.y + 60
    for word in words:
        clean_word = word.strip(".,!?")
        col = MAROON if clean_word in ["CRUEL", "ANGER", "FROST", "SOOTY"] else WHITE
        rendered_word = font_bold.render(word + " ", True, col) if clean_word in ["CRUEL", "ANGER", "FROST", "SOOTY"] else font_normal.render(word + " ", True, col)
        if x + rendered_word.get_width() > box_rect.right - 20:
            x, y = box_rect.x + 20, y + 30
        screen.blit(rendered_word, (x, y))
        x += rendered_word.get_width()

def run_story(screen, clock):
    pygame.mixer.music.stop()
    for _bgm_candidate in (
        os.path.join(NARRATIVE_DIR, "music_box.mp3"),
        os.path.join(NARRATIVE_DIR, "music_box.ogg"),
    ):
        if os.path.exists(_bgm_candidate):
            try:
                pygame.mixer.music.load(_bgm_candidate)
                pygame.mixer.music.set_volume(0.25)
                pygame.mixer.music.play(-1)
            except Exception:
                pass
            break

    DIALOGUE = _build_dialogue()
    bg_path = os.path.join(NARRATIVE_DIR, "kitchen.png")
    bg = load_image(bg_path, scale=(SCREEN_WIDTH, SCREEN_HEIGHT)) if os.path.exists(bg_path) else None

    phase = "dialogue" if PLAYER_DATA["loop_count"] > 1 else "prophecy"
    prophecy_alpha, vf_timer = 0, 0.0
    blink_alpha, blink_dir = 255, -1
    current_node, line_idx = "start", 0

    while True:
        dt = clock.tick(FPS) / 1000.0
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); raise SystemExit
            if phase == "prophecy" and event.type == pygame.KEYDOWN: phase = "blink"
            if phase == "dialogue" and event.type == pygame.MOUSEBUTTONDOWN:
                line = DIALOGUE[current_node][line_idx]
                if line[0] == "Choice":
                    mouse_pos = pygame.mouse.get_pos()
                    rect_a = pygame.Rect(SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT - 170, 600, 50)
                    rect_b = pygame.Rect(SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT - 100, 600, 50)
                    if rect_a.collidepoint(mouse_pos):
                        if current_node == "start": current_node = "branch_1"
                        elif current_node == "branch_1": current_node = "end_CRUEL"; PLAYER_DATA["current_keyword"] = "CRUEL"
                        elif current_node == "branch_2": current_node = "end_FROST"; PLAYER_DATA["current_keyword"] = "FROST"
                        line_idx = 0
                    elif rect_b.collidepoint(mouse_pos):
                        if current_node == "start": current_node = "branch_2"
                        elif current_node == "branch_1": current_node = "end_ANGER"; PLAYER_DATA["current_keyword"] = "ANGER"
                        elif current_node == "branch_2": current_node = "end_SOOTY"; PLAYER_DATA["current_keyword"] = "SOOTY"
                        line_idx = 0
                elif line[0] == "Prompt": phase = "viewfinder_zoom"; vf_timer = 0.0
                else:
                    line_idx += 1
                    if line_idx >= len(DIALOGUE[current_node]) and current_node.startswith("end_"):
                        current_node, line_idx = "viewfinder", 0

        if phase == "prophecy":
            prophecy_alpha = min(255, prophecy_alpha + 40 * dt)
            font = pygame.font.SysFont("courier", 20)
            start_y = SCREEN_HEIGHT // 2 - (len(PROPHECY) * 25) // 2
            for i, line in enumerate(PROPHECY):
                surf = font.render(line, True, (150, 150, 150))
                surf.set_alpha(int(prophecy_alpha))
                screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + (i * 25))))
        elif phase == "blink":
            if bg: screen.blit(bg, (0, 0))
            blink_alpha += (200 * dt * blink_dir)
            if blink_alpha <= 0: blink_dir, phase = 1, "dialogue"
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 0)); overlay.set_alpha(max(0, min(255, int(blink_alpha))))
            screen.blit(overlay, (0, 0))
        elif phase == "dialogue":
            if bg: screen.blit(bg, (0, 0))
            line = DIALOGUE[current_node][line_idx]
            box_rect = pygame.Rect(100, SCREEN_HEIGHT - 200, SCREEN_WIDTH - 200, 180)
            pygame.draw.rect(screen, (10, 10, 10), box_rect)
            pygame.draw.rect(screen, (50, 50, 50), box_rect, 2)
            if line[0] == "Choice":
                r_a, r_b = pygame.Rect(SCREEN_WIDTH//2-300, SCREEN_HEIGHT-170, 600, 50), pygame.Rect(SCREEN_WIDTH//2-300, SCREEN_HEIGHT-100, 600, 50)
                m = pygame.mouse.get_pos()
                for r, txt in [(r_a, line[1]), (r_b, line[2])]:
                    pygame.draw.rect(screen, (60, 20, 20) if r.collidepoint(m) else (30, 30, 30), r)
                    pygame.draw.rect(screen, (100, 100, 100), r, 1)
                    draw_text(screen, txt, r.center, size=24, center=True)
            elif line[0] == "Prompt": draw_text(screen, line[1], box_rect.center, size=32, color=MAROON, center=True)
            else: render_dialogue_text(screen, line[0], line[1], box_rect)
        elif phase == "viewfinder_zoom":
            vf_timer += dt
            if bg: screen.blit(bg, (0, 0))
            
            # The Dual-Lens View-Master Transition
            prog = min(vf_timer / 2.0, 1.0)
            black = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            black.fill((0, 0, 0))
            
            # Max radius is slightly larger than half the screen width to cover corners initially
            max_r = int((SCREEN_WIDTH / 2) * 1.2)
            # The radius shrinks as prog approaches 1.0
            current_r = int(max_r * (1.0 - (prog ** 1.5)))
            
            if current_r > 0:
                # Left eye
                pygame.draw.circle(black, (1, 1, 1), (int(SCREEN_WIDTH * 0.25), SCREEN_HEIGHT//2), current_r)
                # Right eye
                pygame.draw.circle(black, (1, 1, 1), (int(SCREEN_WIDTH * 0.75), SCREEN_HEIGHT//2), current_r)
                black.set_colorkey((1, 1, 1))
                
            screen.blit(black, (0, 0))
            
            if prog >= 1.0: 
                pygame.mixer.music.stop()
                return STATE_LEVEL1
                
        pygame.display.flip()