import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src import config as C
from src.constants import SCREEN_FINAL, SCREEN_TITLE


class FeedbackScreen(BaseScreen):
    ROW_H = 26

    def on_enter(self):
        self._font_xl = FontCache.get(C.FONT_XL)
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        txt = self.game.text

        self._next_btn = Button(
            pygame.Rect(w - 240 - C.PAD, h - 60, 240, C.BUTTON_HEIGHT),
            txt.feedback_next_button,
            self._font_sm,
        )
        self._restart_btn = Button(
            pygame.Rect(C.PAD, h - 60, 140, C.BUTTON_HEIGHT),
            txt.feedback_restart_button,
            self._font_sm,
            colour=C.MID_GREY,
            hover_colour=C.DARK_GREY,
        )

        self._scroll_y = 0
        self._scroll_max = 0
        self._build_rows()

    def _build_rows(self):
        state = self.game.state
        cats_by_id = {c.id: c for c in self.game.categories}
        self._rows = []
        for stop in self.game.stops:
            placed_id = state.map_placements.get(stop.token, "")
            placed_name = cats_by_id.get(placed_id, None)
            placed_name = placed_name.name if placed_name else "(not placed)"
            correct = placed_id and self._get_primary_cat_id(stop) == placed_id
            self._rows.append({
                "token": stop.token,
                "placed": placed_name,
                "primary": stop.primary_category,
                "correct": correct,
            })

    def _get_primary_cat_id(self, stop) -> str:
        for cat in self.game.categories:
            if cat.name.lower() == stop.primary_category.lower():
                return cat.id
        return ""

    def _feedback_message(self) -> str:
        pct = self.game.state.score_pct or 0
        msgs = self.game.text.feedback_messages
        if pct == 100:
            return msgs["perfect"]
        elif pct >= 75:
            return msgs["high"]
        elif pct >= 50:
            return msgs["mid"]
        else:
            return msgs["low"]

    def handle_event(self, event: pygame.event.Event):
        state = self.game.state
        if self._next_btn.handle_event(event):
            state.go_to(SCREEN_FINAL)
            return
        if self._restart_btn.handle_event(event):
            state.reset()
            state.go_to(SCREEN_TITLE)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                state.go_to(SCREEN_FINAL)
            if event.key == pygame.K_r:
                state.reset()
                state.go_to(SCREEN_TITLE)
            if event.key == pygame.K_DOWN:
                self._scroll_y = min(self._scroll_y + 30, self._scroll_max)
            if event.key == pygame.K_UP:
                self._scroll_y = max(self._scroll_y - 30, 0)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_y = max(0, min(self._scroll_y - event.y * 20, self._scroll_max))

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        state = self.game.state
        txt = self.game.text
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # Header
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, 60))
        pygame.draw.rect(surface, C.GOLD, pygame.Rect(0, 56, w, 4))
        hdr = self._font_lg.render(txt.feedback_title, True, C.WHITE)
        surface.blit(hdr, (C.PAD_LG, 14))

        y = 74

        # Score block
        score_pct = state.score_pct or 0
        score_col = C.TEAL_DARK if score_pct >= 50 else C.RUST
        score_s = self._font_xl.render(f"{score_pct}%", True, score_col)
        surface.blit(score_s, (C.PAD_LG, y))

        detail_s = self._font_sm.render(
            f"{state.score} / {len(self.game.stops)} {txt.feedback_correct_label}",
            True, C.DARK_GREY
        )
        surface.blit(detail_s, (C.PAD_LG + score_s.get_width() + 12,
                                y + score_s.get_height() - detail_s.get_height()))

        y += score_s.get_height() + 4

        # Feedback message
        y = draw_wrapped_text(
            surface, self._feedback_message(), self._font_sm, C.DARK_GREY,
            C.PAD_LG, y, w - C.PAD_LG * 2, line_spacing=5
        )
        y += 4
        note_s = self._font_xs.render(txt.feedback_messages["note"], True, C.MID_GREY)
        surface.blit(note_s, (C.PAD_LG, y))
        y += note_s.get_height() + C.PAD

        # --- Table ---
        table_top = y
        col_widths = [180, 200, 200, 60]
        headers = [txt.feedback_token_column,
                   txt.feedback_your_column,
                   txt.feedback_key_column,
                   ""]
        col_x = [C.PAD_LG,
                 C.PAD_LG + col_widths[0],
                 C.PAD_LG + col_widths[0] + col_widths[1],
                 C.PAD_LG + col_widths[0] + col_widths[1] + col_widths[2]]

        # Header row
        pygame.draw.rect(surface, C.PANEL_COLOUR,
                         pygame.Rect(C.PAD_LG - 4, table_top, sum(col_widths) + 8, self.ROW_H))
        for i, hdr_text in enumerate(headers):
            hs = self._font_xs.render(hdr_text.upper(), True, C.MID_GREY)
            surface.blit(hs, (col_x[i] + 4, table_top + 6))
        table_top += self.ROW_H

        # Clipping for scroll
        clip_rect = pygame.Rect(0, table_top, w, h - table_top - 70)
        surface.set_clip(clip_rect)

        row_y = table_top - self._scroll_y
        for i, row in enumerate(self._rows):
            bg = C.WHITE if i % 2 == 0 else C.OFF_WHITE
            pygame.draw.rect(surface, bg,
                             pygame.Rect(C.PAD_LG - 4, row_y, sum(col_widths) + 8, self.ROW_H))

            tok_s = self._font_xs.render(row["token"], True, C.DARK_GREY)
            placed_s = self._font_xs.render(row["placed"], True,
                                            C.TEAL_DARK if row["correct"] else C.RUST)
            primary_s = self._font_xs.render(row["primary"], True, C.MID_GREY)
            check_s = self._font_sm.render("✓" if row["correct"] else "✗", True,
                                           C.TEAL_DARK if row["correct"] else C.RUST)

            surface.blit(tok_s,     (col_x[0] + 4, row_y + 5))
            surface.blit(placed_s,  (col_x[1] + 4, row_y + 5))
            surface.blit(primary_s, (col_x[2] + 4, row_y + 5))
            surface.blit(check_s,   (col_x[3] + 4, row_y + 4))
            row_y += self.ROW_H

        self._scroll_max = max(0, row_y + self._scroll_y - clip_rect.bottom)
        surface.set_clip(None)

        if self._scroll_max > 0:
            hint_s = self._font_xs.render("↑↓ or scroll to see all rows", True, C.MID_GREY)
            surface.blit(hint_s, (w // 2 - hint_s.get_width() // 2, h - 78))

        self._next_btn.draw(surface)
        self._restart_btn.draw(surface)
