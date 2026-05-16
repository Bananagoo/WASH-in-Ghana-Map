# Mapping WASH: A Systems Journey Through Ghana

A browser-playable Python/Pygame knowledge mobilization game for SYDE 599.

---

## Setup

### Requirements

- Python 3.9+
- `pip install pygame pygbag`

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

### Run locally

From inside the `wash_game/` directory:

```bash
python3 main.py
```

The game window will open at 1024×720. Press F11 to toggle fullscreen.

---

## How to play

1. **Title screen** — read the intro, press Space or click Start.
2. **Route screen** — click the highlighted (rust-coloured) stop to visit it.
3. **Stop screen** — read the field note, then click "Collect Token."
4. Repeat for all 16 stops, in order.
5. Once all tokens are collected, the **Systems Map** unlocks.
6. Select a token from the left panel, then click a category box to place it.
7. Place all 16 tokens and click "Finish Map."
8. **Feedback screen** — see your score vs. the primary categories.
9. **Final screen** — read the course takeaway, restart if you like.

---

## Editing content

### Edit stop content, tokens, reflections

Open `data/stops.json`.

Each stop has these editable fields:

| Field | What it is |
|---|---|
| `title` | Stop title shown in the header |
| `token` | Token name collected at this stop |
| `icon_label` | Short uppercase label (placeholder for icon) |
| `emoji` | Emoji shown alongside token (optional) |
| `main_categories` | List of applicable system categories |
| `primary_category` | The "correct" category used for scoring |
| `purpose` | Why this stop is in the course |
| `key_learning` | Main takeaway sentence |
| `course_concept` | Course framework/terminology |
| `reflection` | First-person field note shown in the field note box |
| `route_position` | `{x, y}` pixel position on the route screen |

### Edit system categories

Open `data/categories.json`.

Each category has:

| Field | What it is |
|---|---|
| `id` | Internal ID used for scoring |
| `name` | Display name |
| `description` | Shown on hover (future feature) |
| `color` | `[R, G, B]` for the category card |
| `map_position` | `{x, y}` pixel position on the systems map screen |

### Edit all UI strings

Open `data/game_text.json`.

This file controls:
- Title, subtitle, course credit
- Tutorial paragraph text
- All button labels
- Feedback messages (by score band: perfect / high / mid / low)
- Final takeaway paragraphs

**You never need to edit Python files to change game content.**

### Add or remove a stop

1. Add or remove an entry in `data/stops.json`.
2. That's it. The game reads stop count dynamically.

---

## Project structure

```
wash_game/
  main.py                   Entry point
  requirements.txt
  README.md
  data/
    stops.json              All 16 stop definitions
    categories.json         8 system categories
    game_text.json          All UI strings
  src/
    config.py               Colours, sizes, layout constants
    constants.py            Screen name strings
    models.py               Dataclasses: Stop, Category, GameText
    data_loader.py          Reads JSON → dataclass objects
    state.py                GameState: progression, placements, score
    game.py                 Main Game class, async run loop
    ui.py                   Button, Panel, text-wrap helpers
    screens/
      base_screen.py        BaseScreen interface
      title_screen.py
      route_screen.py
      stop_screen.py
      journal_screen.py
      systems_map_screen.py
      feedback_screen.py
      final_screen.py
  assets/
    images/                 (empty — add sprites here)
    fonts/                  (empty — add .ttf files here)
    audio/                  (empty — add .ogg/.wav here)
  docs/
    content_plan.md         Full game design spec
    implementation_notes.md Developer notes
```

---

## Future pygbag build (GitHub Pages)

pygbag packages the game for browser play via WebAssembly.

```bash
# From inside wash_game/
pygbag main.py
```

This creates a `build/web/` folder. Upload the contents to GitHub Pages.

**Notes for pygbag compatibility:**
- The main loop uses `async def` + `await asyncio.sleep(0)` — already in place.
- All file paths use relative references via `os.path` — already in place.
- No blocking `input()` calls.
- Uses `pygame.font.SysFont` with a generic family name for font fallback.
- pygbag requires Python 3.11+ for best results; test locally with the same version you'll build with.
- If you add audio, use `.ogg` format (not `.mp3`) for browser compatibility.

---

## Testing checklist

- [ ] Title screen appears; Start button and Space/Enter both work
- [ ] Route screen shows 16 stops; stop 1 is highlighted, others locked
- [ ] Clicking stop 1 opens the stop detail screen
- [ ] Stop screen shows title, token, categories, purpose, key learning, concept, field note
- [ ] "Collect Token" button works; returns to route; stop 1 now shows completed
- [ ] Stop 2 is now unlocked; repeat for a few stops
- [ ] Journal icon in route panel updates as tokens are collected
- [ ] After all 16: Systems Map button appears on route screen
- [ ] Systems Map: selecting a token and clicking a category places it
- [ ] All tokens placed → "Finish Map" appears
- [ ] Feedback screen shows score, per-token comparison table
- [ ] Scroll works on feedback table if needed
- [ ] "See Final Reflection" navigates to final screen
- [ ] Final screen shows takeaway text and credit
- [ ] "Play Again" / R resets and returns to title
- [ ] F11 toggles fullscreen
