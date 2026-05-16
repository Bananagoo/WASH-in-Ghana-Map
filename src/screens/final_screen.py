import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text, draw_panel, wrap_text
from src import config as C
from src.constants import SCREEN_TITLE

_BG          = (22, 62, 58)          # deep teal background
_HEADER_BG   = (15, 42, 40)          # darker teal header
_PANEL_BG    = (30, 80, 75)          # mid-teal panel
_PANEL_BDR   = C.GOLD
_TOKEN_BG    = (55, 130, 122)        # pill background
_TOKEN_BDR   = (180, 148, 80)        # pill border
_STAR_COL    = (210, 165, 50)        # decorative stars


def _draw_stars(surface, n=22):
    """Draw a handful of small decorative star crosses at fixed positions."""
    import hashlib
    w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
    for i in range(n):
        seed = hashlib.md5(str(i).encode()).digest()
        sx   = 40 + (seed[0] | seed[1] << 8) % (w - 80)
        sy   = 40 + (seed[2] | seed[3] << 8) % (h - 80)
        r    = 3 + seed[4] % 3
        col  = _STAR_COL if seed[5] % 2 == 0 else C.GOLD_LIGHT
        pygame.draw.line(surface, col, (sx - r, sy), (sx + r, sy), 1)
        pygame.draw.line(surface, col, (sx, sy - r), (sx, sy + r), 1)


class FinalScreen(BaseScreen):

    def on_enter(self):
        self._font_xl = FontCache.get(C.FONT_XL + 8)
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        txt  = self.game.text

        self._restart_btn = Button(
            pygame.Rect(w // 2 - 130, h - 70, 260, 50),
            txt.final_restart_button,
            self._font_md,
            colour=C.GOLD,
            hover_colour=C.RUST,
            text_colour=C.DARK_GREY,
        )
        self.game.audio.play("levelup")

    def handle_event(self, event: pygame.event.Event):
        if self._restart_btn.handle_event(event):
            self.game.audio.play("click")
            self.game.state.reset()
            self.game.state.go_to(SCREEN_TITLE)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, pygame.K_RETURN):
                self.game.audio.play("click")
                self.game.state.reset()
                self.game.state.go_to(SCREEN_TITLE)

    def draw(self, surface: pygame.Surface):
        txt   = self.game.text
        state = self.game.state
        w, h  = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # ── Background ────────────────────────────────────────────────────────
        surface.fill(_BG)
        _draw_stars(surface)

        # ── Header band ───────────────────────────────────────────────────────
        HEADER_H = 110
        pygame.draw.rect(surface, _HEADER_BG, pygame.Rect(0, 0, w, HEADER_H))
        pygame.draw.rect(surface, C.GOLD,     pygame.Rect(0, HEADER_H, w, 4))

        # Side accent bars
        pygame.draw.rect(surface, C.GOLD, pygame.Rect(0, 0, 5, HEADER_H))
        pygame.draw.rect(surface, C.GOLD, pygame.Rect(w - 5, 0, 5, HEADER_H))

        # Title
        title_s = self._font_xl.render(txt.final_title, True, C.GOLD_LIGHT)
        surface.blit(title_s, title_s.get_rect(center=(w // 2, 52)))

        # Subtitle line
        sub_s = self._font_xs.render(
            f"Field route complete  •  {len(state.collected_tokens)} tokens collected",
            True, C.TEAL_LIGHT
        )
        surface.blit(sub_s, sub_s.get_rect(center=(w // 2, 86)))

        y = HEADER_H + 18

        # ── Token recap pills ─────────────────────────────────────────────────
        tokens = state.collected_tokens
        if tokens:
            label_s = self._font_xs.render("FIELD NOTES COLLECTED", True, C.GOLD)
            surface.blit(label_s, label_s.get_rect(centerx=w // 2, top=y))
            y += label_s.get_height() + 8

            pill_pad_x = 10
            pill_pad_y = 5
            pill_gap   = 8
            pills = []
            for token in tokens:
                ts = self._font_xs.render(token, True, C.WHITE)
                pw = ts.get_width() + pill_pad_x * 2
                ph = ts.get_height() + pill_pad_y * 2
                pills.append((ts, pw, ph))

            max_row_w = w - C.PAD_LG * 4
            row_start = 0
            while row_start < len(pills):
                # Pack pills into a row
                row, row_w = [], 0
                i = row_start
                while i < len(pills):
                    ts, pw, ph = pills[i]
                    if row and row_w + pill_gap + pw > max_row_w:
                        break
                    row.append(pills[i])
                    row_w += (pill_gap if row else 0) + pw
                    i += 1

                row_h  = max(ph for _, _, ph in row)
                rx     = w // 2 - row_w // 2
                for ts, pw, ph in row:
                    pill_rect = pygame.Rect(rx, y, pw, row_h)
                    draw_panel(surface, pill_rect, _TOKEN_BG, _TOKEN_BDR, radius=4, border_w=1)
                    surface.blit(ts, (rx + pill_pad_x, y + (row_h - ts.get_height()) // 2))
                    rx += pw + pill_gap

                y += row_h + pill_gap
                row_start = i

            y += 10

        # ── Horizontal divider ────────────────────────────────────────────────
        pygame.draw.line(surface, C.GOLD,
                         (C.PAD_LG * 2, y), (w - C.PAD_LG * 2, y), 1)
        y += 14

        # ── Takeaway panel ────────────────────────────────────────────────────
        panel_w    = 760
        panel_x    = w // 2 - panel_w // 2
        max_w      = panel_w - C.PAD_LG * 2

        # Calculate required height
        total_h = C.PAD_LG
        for para in txt.final_takeaway:
            lines = wrap_text(para, self._font_sm, max_w)
            total_h += len(lines) * (self._font_sm.get_height() + 4) + 10
        total_h += C.PAD_LG

        panel_rect = pygame.Rect(panel_x, y, panel_w, total_h)
        draw_panel(surface, panel_rect, _PANEL_BG, _PANEL_BDR, radius=10)

        ty = y + C.PAD_LG
        for para in txt.final_takeaway:
            ty = draw_wrapped_text(
                surface, para, self._font_sm, C.WHITE,
                panel_x + C.PAD_LG, ty, max_w, line_spacing=4
            )
            ty += 10

        y = panel_rect.bottom + C.PAD

        # ── Credit line ───────────────────────────────────────────────────────
        credit_s = self._font_xs.render(txt.final_credit, True, C.TEAL_LIGHT)
        surface.blit(credit_s, credit_s.get_rect(centerx=w // 2, top=y))

        # ── Restart button ────────────────────────────────────────────────────
        self._restart_btn.draw(surface)

        hint_s = self._font_xs.render("Press  R  or  Enter  to play again", True, C.MID_GREY)
        surface.blit(hint_s, hint_s.get_rect(centerx=w // 2, bottom=h - 10))
