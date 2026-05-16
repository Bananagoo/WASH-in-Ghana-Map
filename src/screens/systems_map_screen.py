import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src import config as C
from src.constants import SCREEN_FEEDBACK, SCREEN_ROUTE


class SystemsMapScreen(BaseScreen):
    CAT_W = 200
    CAT_H = 90
    TOKEN_H = 36
    TOKEN_W = 185

    def on_enter(self):
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        txt = self.game.text

        self._finish_btn = Button(
            pygame.Rect(w - 220 - C.PAD, h - 60, 220, C.BUTTON_HEIGHT),
            txt.map_finish_button,
            self._font_sm,
        )
        self._back_btn = Button(
            pygame.Rect(C.PAD, h - 60, 160, C.BUTTON_HEIGHT),
            txt.map_back_button,
            self._font_sm,
            colour=C.MID_GREY,
            hover_colour=C.DARK_GREY,
        )

        self._status_msg = txt.map_select_prompt
        self._categories = self.game.categories
        self._stops = self.game.stops
        self._selected_token = None   # token name string
        self._hovered_cat = None

        self._token_scroll = 0
        self._build_cat_rects()

    def _build_cat_rects(self):
        self._cat_rects = {}
        for cat in self._categories:
            cx = cat.map_position.x + 30      # shift right of token list
            cy = cat.map_position.y + 70      # below header
            rect = pygame.Rect(cx, cy, self.CAT_W, self.CAT_H)
            self._cat_rects[cat.id] = rect

    def _token_rects(self):
        rects = {}
        state = self.game.state
        x = C.PAD
        y = 70 + C.PAD
        for tok in state.collected_tokens:
            rects[tok] = pygame.Rect(x, y, self.TOKEN_W, self.TOKEN_H)
            y += self.TOKEN_H + 6
        return rects

    def handle_event(self, event: pygame.event.Event):
        state = self.game.state
        txt = self.game.text

        if self._back_btn.handle_event(event):
            state.go_to(SCREEN_ROUTE)
            return

        if state.all_tokens_placed() and self._finish_btn.handle_event(event):
            self._score_and_advance()
            return

        if event.type == pygame.MOUSEMOTION:
            self._hovered_cat = None
            mp = event.pos
            for cat_id, rect in self._cat_rects.items():
                if rect.collidepoint(mp):
                    self._hovered_cat = cat_id
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            tok_rects = self._token_rects()
            for tok, rect in tok_rects.items():
                if rect.collidepoint(mp):
                    self._selected_token = tok
                    self._status_msg = f'"{tok}" selected — click a category to place it.'
                    return

            if self._selected_token:
                for cat_id, rect in self._cat_rects.items():
                    if rect.collidepoint(mp):
                        state.place_token(self._selected_token, cat_id)
                        self._status_msg = txt.map_token_placed
                        self._selected_token = None
                        return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                state.go_to(SCREEN_ROUTE)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if state.all_tokens_placed():
                    self._score_and_advance()

    def _score_and_advance(self):
        cats_by_id = {c.id: c for c in self._categories}
        self.game.state.calculate_score(self._stops, cats_by_id)
        self.game.state.go_to(SCREEN_FEEDBACK)

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        state = self.game.state
        txt = self.game.text
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # Header
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, 60))
        pygame.draw.rect(surface, C.GOLD, pygame.Rect(0, 56, w, 4))
        hdr = self._font_lg.render(txt.map_title, True, C.WHITE)
        surface.blit(hdr, (C.PAD_LG, 14))

        placed_count = len(state.map_placements)
        total = len(state.collected_tokens)
        pc_s = self._font_sm.render(
            f"Placed: {placed_count} / {total}", True, C.GOLD_LIGHT
        )
        surface.blit(pc_s, (w - pc_s.get_width() - C.PAD_LG, 20))

        # Token list (left panel)
        token_panel = pygame.Rect(0, 60, self.TOKEN_W + C.PAD * 2, h - 80)
        pygame.draw.rect(surface, C.PANEL_COLOUR, token_panel)
        pygame.draw.line(surface, C.LIGHT_GREY,
                         (self.TOKEN_W + C.PAD * 2, 60),
                         (self.TOKEN_W + C.PAD * 2, h - 80))

        tok_label = self._font_xs.render("YOUR TOKENS — select one", True, C.MID_GREY)
        surface.blit(tok_label, (C.PAD, 68))

        tok_rects = self._token_rects()
        for tok, rect in tok_rects.items():
            placed_cat_id = state.map_placements.get(tok)
            if placed_cat_id:
                bg = C.TEAL_LIGHT
                border = C.TEAL
            elif tok == self._selected_token:
                bg = C.GOLD_LIGHT
                border = C.GOLD
            else:
                bg = C.WHITE
                border = C.LIGHT_GREY

            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, border, rect, width=1, border_radius=6)

            tok_s = self._font_xs.render(tok, True, C.DARK_GREY)
            surface.blit(tok_s, (rect.left + 8, rect.centery - tok_s.get_height() // 2))

            if placed_cat_id:
                cat_name = next((c.name for c in self._categories if c.id == placed_cat_id), "")
                ps = self._font_xs.render(f"→ {cat_name}", True, C.TEAL_DARK)
                if ps.get_width() < rect.width - 12:
                    y_offset = rect.centery - tok_s.get_height() // 2 + self._font_xs.get_height()
                    surface.blit(ps, (rect.left + 8, y_offset))

        # Category grid
        for cat in self._categories:
            rect = self._cat_rects[cat.id]
            placed_here = [t for t, c in state.map_placements.items() if c == cat.id]

            is_hover = (self._hovered_cat == cat.id and self._selected_token is not None)
            bg_alpha_rect = rect.inflate(2, 2)

            base_colour = tuple(min(255, v + 60) for v in cat.color)
            bg_colour = base_colour if is_hover else tuple(min(255, v + 100) for v in cat.color)
            pygame.draw.rect(surface, bg_colour, rect, border_radius=10)
            pygame.draw.rect(surface, cat.color, rect, width=2, border_radius=10)

            cat_name_s = self._font_sm.render(cat.name, True, C.WHITE)
            surface.blit(cat_name_s, (rect.left + 8, rect.top + 8))

            for i, tok in enumerate(placed_here):
                tok_s = self._font_xs.render(f"• {tok}", True, C.WHITE)
                ty = rect.top + 30 + i * 16
                if ty + 14 < rect.bottom:
                    surface.blit(tok_s, (rect.left + 8, ty))
                elif i == len(placed_here) - 1:
                    more_s = self._font_xs.render(f"+ more…", True, C.WHITE)
                    surface.blit(more_s, (rect.left + 8, ty))
                    break

        # Instructions / status
        inst_s = self._font_xs.render(
            txt.map_instructions if not self._selected_token else self._status_msg,
            True, C.MID_GREY
        )
        surface.blit(inst_s, (self.TOKEN_W + C.PAD * 3, h - 78))

        status_s = self._font_sm.render(self._status_msg, True, C.TEAL_DARK)
        surface.blit(status_s, (self.TOKEN_W + C.PAD * 3, h - 58))

        self._back_btn.draw(surface)
        if state.all_tokens_placed():
            self._finish_btn.draw(surface)
        else:
            remaining = total - placed_count
            rem_s = self._font_xs.render(
                f"Place {remaining} more token(s) to finish.", True, C.MID_GREY
            )
            surface.blit(rem_s, rem_s.get_rect(
                midright=(C.SCREEN_WIDTH - C.PAD, h - 42)
            ))
