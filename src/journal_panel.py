"""
Field Journal side panel — parchment notebook style.

Draw into the panel rect on the route screen.  No state is held here;
all data comes from the stops list and GameState passed to draw().
"""
import pygame

# ── Parchment palette ─────────────────────────────────────────────────────────
_PARCH       = (232, 218, 185)   # main background
_PARCH_DK    = (212, 198, 162)   # darker section / separator
_INK         = ( 78,  58,  35)   # dark brown ink for text/lines
_INK_MID     = (118,  95,  62)   # mid ink for secondary text
_INK_FAINT   = (165, 145, 112)   # faint for empty slots / hints

_CARD_COLL   = (248, 228, 152)   # collected token card: warm gold
_CARD_COLL_B = (195, 168,  85)   # card border collected
_CARD_EMPTY  = (215, 205, 182)   # empty slot: lighter parchment
_CARD_EMPTY_B= (178, 162, 132)   # empty border
_CHECK_COL   = ( 45, 140,  90)   # checkmark green
_LOCK_COL    = (155, 138, 112)   # lock text for unreached stops

# Decorative corner mark colour
_CORNER = (175, 152, 108)


def draw(surface: pygame.Surface,
         panel_rect: pygame.Rect,
         stops: list,
         state,
         font_sm: pygame.font.Font,
         font_xs: pygame.font.Font):
    """
    Render the parchment field-journal panel inside panel_rect.

    Sections:
      1. Parchment background + edge line
      2. "Field Journal" title header
      3. Progress counter
      4. Separator line
      5. Token cards (one per stop), truncated if panel too short
    """
    x  = panel_rect.left
    y0 = panel_rect.top
    w  = panel_rect.width
    h  = panel_rect.height

    # ── 1. Parchment background ───────────────────────────────────────────────
    pygame.draw.rect(surface, _PARCH, panel_rect)

    # Subtle horizontal ruled lines (like notebook paper)
    line_spacing = font_xs.get_height() + 4
    for ly in range(y0 + 58, y0 + h - 90, line_spacing):
        pygame.draw.line(surface, _PARCH_DK, (x + 8, ly), (x + w - 8, ly))

    # Left red margin line (classic notebook feel)
    pygame.draw.line(surface, (198, 148, 145),
                     (x + 20, y0 + 6), (x + 20, y0 + h - 4), 1)

    # Hole-punch circles (top of panel)
    for hx in (x + w // 2,):
        pygame.draw.circle(surface, _PARCH_DK, (hx, y0 + 10), 5)
        pygame.draw.circle(surface, _CORNER,   (hx, y0 + 10), 5, 1)

    # Edge line (left border already drawn by route_screen)

    # ── 2. Title ──────────────────────────────────────────────────────────────
    y = y0 + 22
    title = font_sm.render("Field Journal", True, _INK)
    surface.blit(title, (x + 24, y))
    y += title.get_height() + 2

    # Decorative underline
    pygame.draw.line(surface, _CORNER, (x + 22, y), (x + w - 10, y), 1)
    y += 6

    # ── 3. Progress counter ───────────────────────────────────────────────────
    collected = len(state.collected_tokens)
    total     = len(stops)
    prog_str  = f"{collected} of {total} tokens"
    prog_s    = font_xs.render(prog_str, True, _INK_MID)
    surface.blit(prog_s, (x + 24, y))
    y += prog_s.get_height() + 4

    # Mini progress bar
    bar_w = w - 36
    bar_h = 5
    pygame.draw.rect(surface, _CARD_EMPTY_B,
                     pygame.Rect(x + 24, y, bar_w, bar_h), border_radius=3)
    fill_w = int(bar_w * collected / max(total, 1))
    if fill_w > 0:
        pygame.draw.rect(surface, (188, 148, 62),
                         pygame.Rect(x + 24, y, fill_w, bar_h), border_radius=3)
    y += bar_h + 8

    # ── 4. Separator ──────────────────────────────────────────────────────────
    pygame.draw.line(surface, _CORNER, (x + 8, y), (x + w - 8, y), 1)
    y += 6

    # ── 5. Token cards ────────────────────────────────────────────────────────
    card_w = w - 30
    card_h = 20
    card_gap = 3
    # Reserve space for buttons below (roughly 110px from bottom)
    y_limit = y0 + h - 112

    for stop in stops:
        if y + card_h > y_limit:
            remaining = total - stop.id + 1
            if remaining > 0:
                more_s = font_xs.render(
                    f"…{remaining} more — see journal", True, _INK_FAINT)
                surface.blit(more_s, (x + 24, y + 4))
            break

        is_done = state.is_stop_completed(stop.id)

        if is_done:
            card_col  = _CARD_COLL
            border    = _CARD_COLL_B
            name      = stop.token
            if len(name) > 18:
                name = name[:17] + "…"
            text_col  = _INK
        else:
            is_current = (stop.id == state.current_unlocked_id()
                          and not state.all_stops_complete())
            card_col  = _CARD_EMPTY
            border    = (_CORNER if is_current else _CARD_EMPTY_B)
            name      = f"Stop {stop.id}"
            text_col  = (_INK_MID if is_current else _INK_FAINT)

        card_rect = pygame.Rect(x + 14, y, card_w, card_h)
        pygame.draw.rect(surface, card_col, card_rect, border_radius=3)
        pygame.draw.rect(surface, border,   card_rect, 1, border_radius=3)

        if is_done:
            # Drawn checkmark (avoids ✓ glyph rendering as a box)
            ck_x = x + 19
            ck_y = y + card_h // 2
            pygame.draw.lines(surface, _CHECK_COL, False,
                              [(ck_x - 4, ck_y),
                               (ck_x - 1, ck_y + 3),
                               (ck_x + 4, ck_y - 4)], 2)
            name_s = font_xs.render(name, True, text_col)
            surface.blit(name_s, (x + 30, y + 4))
        else:
            name_s = font_xs.render(name, True, text_col)
            surface.blit(name_s, (x + 18, y + 4))

        y += card_h + card_gap
