# PROJECT_STRUCTURE.md
## Santa Tell Me — Complete File Map & Developer Handover Guide

---

## DIRECTORY STRUCTURE

```
Santa_Tell_Me/
│
├── README.md                        ← Full design doc, narrative, rules, mechanics
├── PROJECT_STRUCTURE.md             ← This file. File map + dev handover
├── main.py                          ← State machine entry point (REPLACED from original)
│
├── src/
│   ├── settings.py                  ← Global constants + PLAYER_DATA shared state (REPLACED)
│   ├── utils.py                     ← Sprite tools, particles, animation (KEEP — original)
│   ├── menu.py                      ← Cover page, mic check removed, direct to title
│   ├── story.py                     ← 1950s kitchen VN + dual-lens viewfinder effect
│   ├── riddle.py                    ← Sphinx chalkboard riddle session (Pass/Fail logic)
│   ├── vignette.py                  ← Degrading family photo ending screens
│   ├── game_over.py                 ← Hijacked game over + valour/wit routing
│   ├── level1.py                    ← Frosty Forest Run pixel game (DO NOT TOUCH)
│   └── level2.py                    ← Present Delivery Maze pixel game (DO NOT TOUCH)
│
└── assets/
    ├── sprites/                     ← All pixel game sprites (DO NOT TOUCH)
    │   ├── santa/                   (fronts, right, attack, hurts, dead, floating)
    │   ├── wildman/                 (run, attack, dead)
    │   └── hunter/                  (walk, attack)
    │
    ├── items/                       ← Pixel game items (DO NOT TOUCH)
    │   ├── santa_magic.png          
    │   ├── wildmen_snow.png         
    │   ├── santa_hourglass.png      
    │   └── christmass_tree.png      
    │
    ├── backgrounds/                 ← Pixel game backgrounds (DO NOT TOUCH)
    │   ├── forest_bg.png            
    │   ├── maze_bg.png
    │   └── city_gate.png            
    │
    ├── ui/                          ← Pixel game HUD elements (DO NOT TOUCH)
    │   ├── heart_full.png
    │   ├── heart_empty.png
    │   └── kill_icon.png
    │
    ├── audio/                       ← Pixel game audio (DO NOT TOUCH)
    │   ├── bgm/
    │   │   ├── menu_bgm.mp3         
    │   │   ├── level1_bgm.mp3
    │   │   └── level2_bgm.mp3
    │   └── sfx/
    │       ├── magic_shoot.wav
    │       ├── santa_hurt.wav
    │       ├── item_pickup.wav
    │       ├── level_clear.wav
    │       ├── hunter_die.wav
    │       └── game_over.wav
    │
    └── narrative/                   ← 1950s horror assets (STRICTLY .png & .mp3/.ogg)
        ├── music_box.mp3            ← Music-box Santa Tell Me cover
        ├── kitchen.png              ← 1950s kitchen, slightly wrong
        ├── reincarnation_bg.png     ← Red view-master forest overlay for failing quizzes
        ├── family_loop1.png         ← Portrait: MC's eyes scribbled out in red
        ├── family_loop2.png         ← Portrait: eyes + no mouth (smooth skin blur)
        ├── family_loop3.png         ← Portrait: face/torso chemically dissolved
        └── family_loop_final.png    ← Portrait: MC completely absent
```

---

## FILE-BY-FILE RESPONSIBILITIES

### `main.py` — State Machine

Manages the complete game state loop and Reincarnation logic.

```
run_menu() ──► STATE_STORY ──► STATE_LEVEL1 ──► STATE_LEVEL2
                                  ▲                  │
                                  │                  ▼
                                  │           STATE_GAME_OVER
                                  │             (Valour) ──► STATE_MENU (Run Dead)
                                  │                  │
                                  │             (Wit) ▼
                                  │           STATE_RIDDLE
                                  │                  │
                 (Fail Quiz) ─────┴────────── (Pass Quiz)
                (Loop Count +1)                      ▼
               (reincarnation_bg)              STATE_VIGNETTE
                                                     │
                                                     ▼
                                                 STATE_MENU (Run Dead)
```

### `src/settings.py` — Global Constants & Shared State

* Contains `MAROON`, `PINE_GREEN`, `VINTAGE_YELLOW` — 1950s colour palette.
* Sets all state string constants.
* `PLAYER_DATA` dict controls the narrative persistence:

```python
PLAYER_DATA = {
    "name": "child",          # Trap for dialogue and math questions
    "age": "10",              # Trap for math questions (answer is always 4)
    "loop_count": 1,          # Increments only if they FAIL a quiz and reincarnate
    "current_keyword": None   # CRUEL/ANGER/FROST/SOOTY (Locked in story.py)
}
```

### `src/story.py` — 1950s Kitchen VN + Dual-Lens Viewfinder

* Skippable prophecy logic (only plays on Loop 1).
* True branching VN (2 choices → 4 keyword paths).
* Locks `PLAYER_DATA["current_keyword"]`.
* Features a mathematically calculated dual-lens shrink effect (simulating pushing your face into a View-Master) before entering Level 1.

### `src/riddle.py` — Sphinx Chalkboard Session

* 3 questions: 1 Instinct Trap (Keyword), 2 Math Traps (Answer is 4).
* Calculates Pass/Fail state.
* **Fail:** Narrator thinks you are a pure, dumb soul. Returns `"fail"` to `main.py`, which triggers the `reincarnation_bg.png` transition, adds +1 to the loop, and throws the player back to Level 1.
* **Pass:** You escape the pixel world, but lose a body part. Returns `"pass"` to `main.py`, which routes to `vignette.py`.

### `src/vignette.py` — Degrading Family Photo Endings

* Displays `family_loopX.png` based on the player's current loop count.
* If `loop_count >= 4` (survived 4 reincarnations), it auto-triggers the True Ending screen (`family_loop_final.png` + "...at what cost?").
* After displaying the toll (and pressing ENTER), kicks the player back to the `STATE_MENU`.

### `src/game_over.py` — Hijacked Tally Screens

* **Valour Route (victory=False):** Wait 2.5s. Screen tears with CRT static. Blood tint. Narrator eats your soul ("Valour tastes... so sweet"). Kicks directly to `STATE_MENU`.
* **Wit Route (victory=True):** Wait 2.5s. UI melts. Scores spin to 4. Narrator tests your wit ("Wit always tastes so bland"). Pushes to `STATE_RIDDLE`.
* No interactive "Retry" buttons. The traps spring automatically to catch the player off guard.

---

## TEAM OWNERSHIP SUMMARY

| Module | Owner | Status / Notes |
| --- | --- | --- |
| `main.py` | Lead Dev | **LOCKED.** Handles Reincarnation loop routing perfectly. |
| `settings.py` | Lead Dev | **LOCKED.** Mic globals removed. |
| `utils.py` | Shared | **LOCKED.** Includes `draw_text_wrapped` for long riddles. |
| `menu.py` | Horror Wrapper | **LOCKED.** Mic feature fully scrapped. Direct to Title. |
| `story.py` | Horror Wrapper | **LOCKED.** Dual-lens viewfinder effect added. Age bug fixed. |
| `riddle.py` | Horror Wrapper | **LOCKED.** Pass = Escape (Menu). Fail = Reincarnate (Level 1). |
| `vignette.py` | Horror Wrapper | **LOCKED.** Returns to menu after photo degradation. |
| `game_over.py` | Horror Wrapper | **LOCKED.** Valour = Menu. Wit = Riddle. No buttons. |
| `level1.py` | Pixel Game Team | **LOCKED.** Hunter AI nerfed slightly for balance. |
| `level2.py` | Pixel Game Team | **LOCKED.** |

---

## ASSET CREATION PROMPTS (For Nano Banana / Image Generators)

**`kitchen.png` (1280×720)**
> *1950s American kitchen interior, Christmas morning, photorealistic painting style. Warm but slightly off. A mother stands by the stove holding a birthday cake with lit candles, smiling too broadly. A father sits at the table reading a newspaper, eyes slightly too wide and unblinking. Christmas tree in background with tinsel and baubles. Radio on the counter. Formica table, linoleum floor. Warm yellow kitchen light. Slight vignette at edges. The scene feels festive but subtly wrong — too perfect, too still. Painted illustration style. 16:9.*

**`reincarnation_bg.png` (1280×720)**
> *2D visual novel background art, 1950s vintage analog horror style. A dark, eerie, heavily distorted view of a snowy forest path, seen as if looking through the twin circular lenses of a vintage red View-Master toy. The edges are pitch black and vignetted, the center shows a corrupted, CRT static-filled winter woods. Sepia and muted colors, unsettling liminal space vibe. 16:9.*

**`family_loop1.png` (1280×720)**
> *Vintage 1950s family portrait photograph, aged and slightly overexposed. A mother and father stand smiling in formal attire. Between them, a child stands — but the child's eyes have been violently scribbled over with thick red ballpoint pen, the marks frantic and deliberate. The rest of the photo is pristine. Sepia-toned edges, photographic grain. Portrait orientation subjects, landscape frame.*