import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache
from src.assets import token_badge
from src import config as C
from src.constants import SCREEN_ROUTE, SCREEN_WASH_MAP

_HEADER_H  = 60
_BOTTOM_H  = 70
_COLS      = 4
_CARD_W    = 220
_CARD_H    = 88
_PAD_X     = 18
_PAD_Y     = 14

_PLACEHOLDER_BG  = (215, 210, 200)
_PLACEHOLDER_BDR = (180, 172, 158)
_COLLECTED_BDR   = C.GOLD


class JournalScreen(BaseScreen):
    def on_enter(self):
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        txt = self.game.text

        self._back_btn = Button(
            pygame.Rect(C.PAD, h - _BOTTOM_H + 16, 160, C.BUTTON_HEIGHT),
            txt.journal_back_button,
            self._font_sm,
            colour=C.MID_GREY,
            hover_colour=C.DARK_GREY,
        )
        self._map_btn = Button(
            pygame.Rect(w - 260 - C.PAD, h - _BOTTOM_H + 16, 260, C.BUTTON_HEIGHT),
            "Build WASH Systems Diagram →",
            self._font_sm,
        )

        # Pre-render token badges for all stops
        stops = self.game.stops
        self._badges = {
            s.token: token_badge(s.token, size=48)
            for s in stops if s.token
        }

        self._scroll_y = 0
        self._max_scroll = 0

    def handle_event(self, event: pygame.event.Event):
        if self._back_btn.handle_event(event):
            self.game.state.go_back()
            return
        state = self.game.state
        if state.all_stops_complete() and self._map_btn.handle_event(event):
            state.go_to(SCREEN_WASH_MAP)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_b):
                self.game.state.go_back()
            elif event.key == pygame.K_DOWN:
                self._scroll_y = min(self._scroll_y + 30, self._max_scroll)
            elif event.key == pygame.K_UP:
                self._scroll_y = max(self._scroll_y - 30, 0)
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_y = max(0, min(
                self._scroll_y - event.y * 24, self._max_scroll))

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        state = self.game.state
        stops = self.game.stops
        txt   = self.game.text
        w, h  = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # ── Header ────────────────────────────────────────────────────────
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, _HEADER_H - 4))
        pygame.draw.rect(surface, C.GOLD,      pygame.Rect(0, _HEADER_H - 4, w, 4))
        hdr = self._font_lg.render(txt.journal_title, True, C.WHITE)
        surface.blit(hdr, (C.PAD_LG, 14))

        count_s = self._font_sm.render(
            f"{len(state.collected_tokens)} of {len(stops)} tokens collected",
            True, C.GOLD_LIGHT,
        )
        surface.blit(count_s, (w - count_s.get_width() - C.PAD_LG, 20))

        # ── Grid ──────────────────────────────────────────────────────────
        collected = set(state.collected_tokens)
        grid_w    = _COLS * _CARD_W + (_COLS - 1) * _PAD_X
        x_start   = (w - grid_w) // 2
        y_start   = _HEADER_H + _PAD_Y

        content_top    = _HEADER_H
        content_bottom = h - _BOTTOM_H
        clip_rect      = pygame.Rect(0, content_top, w, content_bottom - content_top)
        surface.set_clip(clip_rect)

        for i, stop in enumerate(stops):
            col = i % _COLS
            row = i // _COLS
            cx  = x_start + col * (_CARD_W + _PAD_X)
            cy  = y_start + row * (_CARD_H + _PAD_Y) - self._scroll_y

            card_rect = pygame.Rect(cx, cy, _CARD_W, _CARD_H)
            is_collected = stop.token in collected

            if is_collected:
                pygame.draw.rect(surface, C.PANEL_COLOUR, card_rect, border_radius=8)
                pygame.draw.rect(surface, _COLLECTED_BDR, card_rect, width=2, border_radius=8)

                badge = self._badges.get(stop.token)
                if badge:
                    surface.blit(badge, (cx + 8, cy + (_CARD_H - 48) // 2))

                # Stop number + token name + category
                tx = cx + 8 + 48 + 10
                num_s = self._font_xs.render(f"Stop {stop.id}", True, C.MID_GREY)
                surface.blit(num_s, (tx, cy + 10))

                tok_s = self._font_sm.render(stop.token, True, C.TEAL_DARK)
                surface.blit(tok_s, (tx, cy + 10 + num_s.get_height() + 2))

                avail_w = _CARD_W - tx + cx - 8
                cat = stop.primary_category or ""
                # Truncate category if too long
                cat_s = self._font_xs.render(cat, True, C.RUST)
                if cat_s.get_width() > avail_w:
                    while cat and self._font_xs.size(cat + "…")[0] > avail_w:
                        cat = cat[:-1]
                    cat_s = self._font_xs.render(cat + "…", True, C.RUST)
                surface.blit(cat_s, (tx, cy + _CARD_H - cat_s.get_height() - 10))

            else:
                # Grey placeholder
                pygame.draw.rect(surface, _PLACEHOLDER_BG, card_rect, border_radius=8)
                pygame.draw.rect(surface, _PLACEHOLDER_BDR, card_rect, width=1, border_radius=8)

                q_s = self._font_lg.render("?", True, _PLACEHOLDER_BDR)
                surface.blit(q_s, (cx + 8 + (48 - q_s.get_width()) // 2,
                                   cy + (_CARD_H - q_s.get_height()) // 2))

                num_s = self._font_xs.render(f"Stop {stop.id}", True, (150, 142, 128))
                surface.blit(num_s, (cx + 8 + 48 + 10, cy + 10))

                locked_s = self._font_xs.render("Not yet collected", True, (170, 160, 142))
                surface.blit(locked_s, (cx + 8 + 48 + 10,
                                        cy + 10 + num_s.get_height() + 4))

        # Calculate max scroll
        n_rows = (len(stops) + _COLS - 1) // _COLS
        total_h = y_start + n_rows * (_CARD_H + _PAD_Y) - _PAD_Y
        self._max_scroll = max(0, total_h - content_bottom)

        surface.set_clip(None)

        if self._max_scroll > 0:
            sc_s = self._font_xs.render("↑↓ scroll", True, C.MID_GREY)
            surface.blit(sc_s, sc_s.get_rect(
                right=w - C.PAD, bottom=content_bottom - 4))

        # ── Bottom bar ────────────────────────────────────────────────────
        pygame.draw.line(surface, C.LIGHT_GREY,
                         (0, h - _BOTTOM_H), (w, h - _BOTTOM_H), 1)
        self._back_btn.draw(surface)
        if state.all_stops_complete():
            self._map_btn.draw(surface)
