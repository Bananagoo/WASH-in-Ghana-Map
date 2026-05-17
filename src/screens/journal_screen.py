import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src import config as C
from src.constants import SCREEN_ROUTE, SCREEN_MAP, SCREEN_WASH_MAP


class JournalScreen(BaseScreen):
    def on_enter(self):
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        txt = self.game.text

        self._back_btn = Button(
            pygame.Rect(C.PAD, h - 62, 160, C.BUTTON_HEIGHT),
            txt.journal_back_button,
            self._font_sm,
            colour=C.MID_GREY,
            hover_colour=C.DARK_GREY,
        )
        self._map_btn = Button(
            pygame.Rect(w - 240 - C.PAD, h - 62, 240, C.BUTTON_HEIGHT),
            "Build Systems Map →",
            self._font_sm,
        )

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

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        state = self.game.state
        stops = self.game.stops
        txt = self.game.text
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # Header
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, 60))
        pygame.draw.rect(surface, C.GOLD, pygame.Rect(0, 56, w, 4))
        hdr = self._font_lg.render(txt.journal_title, True, C.WHITE)
        surface.blit(hdr, (C.PAD_LG, 14))

        count_s = self._font_sm.render(
            f"{len(state.collected_tokens)} of {len(stops)} tokens collected",
            True, C.GOLD_LIGHT
        )
        surface.blit(count_s, (w - count_s.get_width() - C.PAD_LG, 20))

        # Token cards
        if not state.collected_tokens:
            empty_s = self._font_md.render(txt.journal_empty, True, C.MID_GREY)
            surface.blit(empty_s, empty_s.get_rect(center=(w // 2, h // 2)))
        else:
            # Build lookup from token name → stop
            stops_by_token = {s.token: s for s in stops}

            cols = 3
            card_w = (w - C.PAD_LG * (cols + 1)) // cols
            card_h = 110
            x_start = C.PAD_LG
            y_start = 80

            for i, token in enumerate(state.collected_tokens):
                col = i % cols
                row = i // cols
                cx = x_start + col * (card_w + C.PAD_LG)
                cy = y_start + row * (card_h + C.PAD)

                card_rect = pygame.Rect(cx, cy, card_w, card_h)
                pygame.draw.rect(surface, C.PANEL_COLOUR, card_rect, border_radius=8)
                pygame.draw.rect(surface, C.GOLD, card_rect, width=1, border_radius=8)

                stop = stops_by_token.get(token)
                if stop:
                    num_s = self._font_xs.render(f"Stop {stop.id}", True, C.MID_GREY)
                    surface.blit(num_s, (cx + 10, cy + 8))

                    tok_s = self._font_sm.render(token, True, C.TEAL_DARK)
                    surface.blit(tok_s, (cx + 10, cy + 26))

                    cat_s = self._font_xs.render(
                        stop.primary_category, True, C.RUST
                    )
                    surface.blit(cat_s, (cx + 10, cy + 50))

                    title_lines = _wrap(stop.title, self._font_xs, card_w - 20)
                    ty = cy + 68
                    for line in title_lines[:2]:
                        ls = self._font_xs.render(line, True, C.DARK_GREY)
                        surface.blit(ls, (cx + 10, ty))
                        ty += self._font_xs.get_height() + 2

        # Buttons
        self._back_btn.draw(surface)
        if state.all_stops_complete():
            self._map_btn.draw(surface)


def _wrap(text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if font.size(test)[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines
