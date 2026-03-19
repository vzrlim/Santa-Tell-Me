"""
Sphinx Chalkboard Riddle Session - Santa Tell Me
"""
import pygame
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, VINTAGE_YELLOW, PLAYER_DATA
from src.utils import draw_text

def _draw_wrapped(screen, text, cx, y, font, color, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        if font.size(cur + w)[0] > max_w:
            lines.append(cur.strip()); cur = w + " "
        else: cur += w + " "
    lines.append(cur.strip())
    for line in lines:
        s = font.render(line, True, color)
        screen.blit(s, (cx - s.get_width()//2, y)); y += font.get_linesize()

def run_riddle(screen, clock):
    KEYWORDS = {
        "SOOTY": {"ui": "S _ _ T _", "q": ["He comes down the chimney in the dead of night to visit good children. Who is he?", "What is the true color of a burning memory once the warm fire dies?"]},
        "ANGER": {"ui": "A N _ E _", "q": ["It sits at the very top of the tree, watching over the family with wings of white. What is it?", "What is the one thing your father told you would ruin this perfectly wonderful morning?"]},
        "FROST": {"ui": "F _ _ S T", "q": ["A table full of sweet treats and hot food, gathered around by family on Christmas day. What is it?", "What crawls across the bedroom window to trap the warmth inside with us?"]},
        "CRUEL": {"ui": "C _ _ _ L", "q": ["A sweet song sung by a choir in the winter wind, bringing joy to those who hear it. What is it?", "How does the world treat a child who refuses to listen to their mother and father?"]}
    }
    
    MATH_BANK = [
        "If Santa has nine reindeer but only four to pull your sled to the grave, how many are left in the cold?",
        "Four lit candles on a birthday cake. Four heavy walls in a quiet room. How many days until you stop screaming?",
        "A human has five parts. If you give your eyes, your voice, your memory, and your form to the man in red... how many parts are left for your soul?",
        "Mom, Dad, and You sitting at the table. If a jolly old visitor slides down the chimney to join you, how many plates do we need?",
        "Count the corners of a gift box. Now subtract the number of parents who actually love you. What is the final sum?",
        "On a scale of one to four, how happy are you to belong to us forever?"
    ]

    kw = PLAYER_DATA.get("current_keyword", "CRUEL")
    math_pool = random.sample(MATH_BANK, 2)
    session_questions = [
        {"type": "kw", "q": random.choice(KEYWORDS[kw]["q"]), "ui": KEYWORDS[kw]["ui"], "ans": kw},
        {"type": "math", "q": math_pool[0], "ui": "Answer:", "ans": "4"},
        {"type": "math", "q": math_pool[1], "ui": "Answer:", "ans": "4"}
    ]
    
    q_idx, user_input, msg_timer = 0, "", 3.0
    narrator_msg = "Let us see if you can remember your manners."
    quiz_failed = False

    while True:
        dt = clock.tick(FPS) / 1000.0
        screen.fill((10, 15, 10))
        pygame.draw.rect(screen, (100, 70, 40), (20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-40), 10)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and msg_timer <= 0:
                if event.key == pygame.K_RETURN and user_input.strip():
                    is_correct = (user_input.strip().upper() == session_questions[q_idx]["ans"])
                    if not is_correct: quiz_failed = True
                    
                    if q_idx == 2: # Last question feedback
                        if not quiz_failed:
                            narrator_msg = "Your cunning appals me. But I will keep a token... since I am stuck here."
                        else:
                            narrator_msg = "How delightfully pure and dull. I will throw you back... amuse me in the snow."
                    else:
                        narrator_msg = "Oh... you have been paying attention." if is_correct else "Tsk. Blind little lamb."
                    
                    msg_timer = 3.5; user_input = ""; q_idx += 1
                elif event.key == pygame.K_BACKSPACE: user_input = user_input[:-1]
                elif event.unicode.isprintable(): user_input += event.unicode.upper()

        if msg_timer > 0:
            msg_timer -= dt
            draw_text(screen, narrator_msg, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), size=32, color=WHITE, center=True, font_name="georgia")
            if msg_timer <= 0 and q_idx >= 3:
                return "fail" if quiz_failed else "pass"
        else:
            q = session_questions[q_idx]
            draw_text(screen, f"Question {q_idx+1} of 3", (SCREEN_WIDTH//2, 100), size=24, color=(150,150,150), center=True)
            _draw_wrapped(screen, q["q"], SCREEN_WIDTH//2, 180, pygame.font.SysFont("georgia", 28), (255,255,255), SCREEN_WIDTH - 160)
            draw_text(screen, q["ui"], (SCREEN_WIDTH//2, 370), size=48, color=(200,200,200), center=True, font_name="courier")
            draw_text(screen, user_input + "_", (SCREEN_WIDTH//2, 460), size=48, color=VINTAGE_YELLOW, center=True, font_name="courier")
        pygame.display.flip()