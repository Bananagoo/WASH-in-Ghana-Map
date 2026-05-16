# Implementation Notes

## Architecture summary

The game uses a flat screen-manager pattern: `Game` holds a dict of all screen objects and calls `on_enter`, `on_exit`, `handle_event`, `update`, `draw` on whichever screen is currently active. Screen transitions are driven by `GameState.current_screen`; `Game.run()` checks for changes each frame and calls `_switch_to`.

No global state — every screen gets a reference to `Game` and reads from `game.state`, `game.stops`, `game.categories`, `game.text`.

## State design

`GameState` tracks:
- `completed_stop_ids` — set of stop IDs that have been collected
- `collected_tokens` — ordered list of token name strings (drives journal display order)
- `current_unlocked_id()` — always `len(completed_stop_ids) + 1`; simple linear progression
- `map_placements` — dict of token_name → category_id
- `score`, `score_pct` — computed by `calculate_score()` after map is finished

Calling `state.reset()` wipes all of the above and returns `current_screen` to `SCREEN_TITLE`.

## Adding a new screen

1. Create `src/screens/my_screen.py` with a class that inherits `BaseScreen`.
2. Add a constant in `src/constants.py`.
3. Add an entry in the `screen_map` dict in `src/game.py`.
4. Navigate to it via `game.state.go_to(MY_SCREEN_CONSTANT)`.

## Adjusting stop route positions

Edit `route_position: {x, y}` in `data/stops.json`. The route screen draws stops at those pixel coordinates with a y-offset of 30 (to clear the header). The current layout is a 4-column snake:

- Row 1 (y=160): Stops 1–4, left to right
- Row 2 (y=310): Stops 5–8, right to left
- Row 3 (y=460): Stops 9–12, left to right
- Row 4 (y=610): Stops 13–16, right to left

## Adjusting category positions on the systems map

Edit `map_position: {x, y}` in `data/categories.json`. The systems map screen applies a +30 x-offset and +70 y-offset to place cards below the header and right of the token list.

## Font handling

All fonts use `pygame.font.SysFont` with a comma-separated list of system fonts. This degrades gracefully — if Arial isn't available, Helvetica or the default pygame font is used. This is intentional for pygbag compatibility (no TTF bundling required for MVP).

To use a custom font later: load it with `pygame.font.Font("assets/fonts/myfont.ttf", size)` and update `FontCache.get()` in `src/ui.py`.

## pygbag notes

- `main.py` uses `asyncio.run(main())` and the game loop uses `await asyncio.sleep(0)` — this is the pygbag contract.
- pygbag cannot use blocking file I/O in the web build; for the browser version, JSON files may need to be bundled differently. For the MVP, local file I/O is fine.
- Test with `pygbag main.py` and open `http://localhost:8000` in the browser.
