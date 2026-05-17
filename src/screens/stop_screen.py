import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src.assets import load_image, stop_placeholder, token_badge, THEME_COLOURS
from src import config as C
from src.constants import SCREEN_ROUTE


# Category name → colour (for pill tags)
_CAT_COLOURS = {
    "Health":                 (200,  70,  70),
    "Infrastructure":         (80,  120, 185),
    "Governance":             (130,  80, 185),
    "Culture":                (195, 145,  50),
    "Gender":                 (200,  95, 155),
    "Climate":                (55,  160,  85),
    "Livelihoods":            (165, 120,  55),
    "Knowledge / Collaboration": (47, 140, 130),
}


class StopScreen(BaseScreen):
    IMG_W = 260
    IMG_H = 165

    def on_enter(self):
        self._font_xl = FontCache.get(C.FONT_XL)
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        txt  = self.game.text

        self._collect_btn = Button(
            pygame.Rect(w // 2 - 120, h - 70, 240, C.BUTTON_HEIGHT + 4),
            txt.stop_collect_button, self._font_md,
        )
        self._back_btn = Button(
            pygame.Rect(C.PAD, h - 70, 150, C.BUTTON_HEIGHT),
            txt.stop_back_button, self._font_sm,
            colour=C.MID_GREY, hover_colour=C.DARK_GREY,
        )

        # Stop data — set externally via set_stop() after on_enter
        self._stop = None
        self._token_collected = False
        self._stop_image: pygame.Surface = None
        self._token_badge: pygame.Surface = None

        # Fade-in overlay: starts opaque, drains to 0
        self._fade_alpha = 200.0

    def set_stop(self, stop):
        self._stop = stop
        state = self.game.state
        self._token_collected = state.is_stop_completed(stop.id)
        self._collect_btn.visible = not self._token_collected

        # Load images (fallback to None → placeholder drawn inline)
        self._stop_image = load_image(stop.image, (self.IMG_W, self.IMG_H)) if stop.image else None
        self._token_badge = (load_image(stop.token_image, (36, 36))
                             if stop.token_image else None)
        # Reset fade each time a new stop opens
        self._fade_alpha = 200.0

    def handle_event(self, event: pygame.event.Event):
        if self._back_btn.handle_event(event):
            self.game.audio.play("click")
            self.game.state.go_to(SCREEN_ROUTE)
            return
        if not self._token_collected and self._collect_btn.handle_event(event):
            self._collect_token()
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_b):
                self.game.state.go_to(SCREEN_ROUTE)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN) and not self._token_collected:
                self._collect_token()

    def _collect_token(self):
        if not self._stop:
            return
        self.game.state.mark_stop_complete(self._stop.id, self._stop.token)
        self.game.audio.play("collect")
        self._token_collected = True
        self._collect_btn.visible = False

    def update(self, dt: float):
        # Drain fade overlay
        if self._fade_alpha > 0:
            self._fade_alpha = max(0.0, self._fade_alpha - 220 * dt / 0.35)

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        if not self._stop:
            return

        stop = self._stop
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        pad  = C.PAD_LG

        # ── Header ──────────────────────────────────────────────────────
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, 70))
        pygame.draw.rect(surface, C.GOLD,      pygame.Rect(0, 66, w, 4))
        num_s = self._font_lg.render(
            f"Stop {stop.id} of {len(self.game.stops)}", True, C.GOLD_LIGHT)
        surface.blit(num_s, (pad, 8))
        _draw_fitted_line(surface, stop.title, C.WHITE, pad, 36,
                          w - pad * 2,
                          [self._font_md, self._font_sm, self._font_xs])

        # ── Top section: image (left) + token / categories (right) ──────
        img_x, img_y = pad, 80
        img_rect = pygame.Rect(img_x, img_y, self.IMG_W, self.IMG_H)

        if self._stop_image:
            surface.blit(self._stop_image, img_rect)
            pygame.draw.rect(surface, C.GOLD, img_rect, width=2, border_radius=4)
        else:
            ph = stop_placeholder(self.IMG_W, self.IMG_H,
                                   stop.icon_label, stop.visual_theme, self._font_lg)
            surface.blit(ph, img_rect)

        # Token badge + name
        right_x = img_x + self.IMG_W + pad
        right_w  = w - right_x - pad

        badge_surf = (self._token_badge
                      if self._token_badge
                      else token_badge(stop.token, size=40, bg_colour=C.GOLD))
        surface.blit(badge_surf, (right_x, img_y))

        tok_s = self._font_md.render(stop.token, True, C.TEAL_DARK)
        surface.blit(tok_s, (right_x + 48, img_y + 10))

        # Category pills
        pill_y = img_y + 50
        px = right_x
        for cat in stop.main_categories:
            cat_col = _CAT_COLOURS.get(cat, C.TEAL)
            cat_s   = self._font_xs.render(cat, True, C.WHITE)
            pw = cat_s.get_width() + 14
            if px + pw > w - pad:
                px = right_x
                pill_y += 26
            pill_rect = pygame.Rect(px, pill_y, pw, 22)
            pygame.draw.rect(surface, cat_col,  pill_rect, border_radius=11)
            surface.blit(cat_s, cat_s.get_rect(center=pill_rect.center))
            px += pw + 6

        # What Happened (new optional field)
        wh_y = img_y + 92
        if stop.what_happened:
            wh_lbl = self._font_xs.render("WHAT HAPPENED", True, C.MID_GREY)
            surface.blit(wh_lbl, (right_x, wh_y))
            wh_y += wh_lbl.get_height() + 2
            wh_y = draw_wrapped_text(
                surface, stop.what_happened, self._font_xs, C.DARK_GREY,
                right_x, wh_y, right_w, line_spacing=3,
            )

        # ── Divider ──────────────────────────────────────────────────────
        section_top = max(img_y + self.IMG_H + 10, wh_y + 6)
        pygame.draw.line(surface, C.LIGHT_GREY, (pad, section_top), (w - pad, section_top))
        y = section_top + 10

        # ── Content sections ─────────────────────────────────────────────
        def section(label, body, text_col=C.DARK_GREY, bold=False):
            nonlocal y
            lbl = self._font_xs.render(label.upper(), True, C.MID_GREY)
            surface.blit(lbl, (pad, y))
            y += lbl.get_height() + 2
            font = self._font_sm
            y = draw_wrapped_text(surface, body, font, text_col,
                                  pad, y, w - pad * 2, line_spacing=4)
            y += C.PAD_SM

        section("Key Learning", stop.key_learning, C.TEAL_DARK)
        section("Course Concept", stop.course_concept)

        if stop.systems_insight:
            section("Systems Insight", stop.systems_insight, C.RUST)

        # ── Field Note box ────────────────────────────────────────────────
        note_lbl = self._font_xs.render("FIELD NOTE", True, C.MID_GREY)
        surface.blit(note_lbl, (pad, y))
        y += note_lbl.get_height() + 4

        note_lines = _wrap(stop.reflection, self._font_sm, w - pad * 2 - C.PAD * 2)
        note_h = len(note_lines) * (self._font_sm.get_height() + 4) + C.PAD * 2
        note_rect = pygame.Rect(pad, y, w - pad * 2, note_h)
        pygame.draw.rect(surface, C.PANEL_COLOUR, note_rect, border_radius=6)
        pygame.draw.rect(surface, C.GOLD, note_rect, width=2, border_radius=6)
        ny = y + C.PAD
        for line in note_lines:
            ls = self._font_sm.render(line, True, C.DARK_GREY)
            surface.blit(ls, (pad + C.PAD, ny))
            ny += self._font_sm.get_height() + 4
        y = note_rect.bottom + C.PAD_SM

        # Reading tie (new optional field)
        if stop.reading_tie:
            rt_lbl = self._font_xs.render("READING TIE  ", True, C.MID_GREY)
            surface.blit(rt_lbl, (pad, y))
            y = draw_wrapped_text(
                surface, stop.reading_tie, self._font_xs, C.MID_GREY,
                pad + rt_lbl.get_width(), y,
                w - pad * 2 - rt_lbl.get_width(),
                line_spacing=3,
            )

        # ── Bottom buttons ────────────────────────────────────────────────
        if self._token_collected:
            done_s = self._font_md.render(f"{stop.token} collected!", True, C.TEAL_DARK)
            tr = done_s.get_rect(center=(w // 2, h - 48))
            # Draw small checkmark to the left of the text
            ck_x, ck_y = tr.left - 14, tr.centery
            pygame.draw.lines(surface, C.TEAL, False,
                              [(ck_x - 5, ck_y),
                               (ck_x - 1, ck_y + 5),
                               (ck_x + 7, ck_y - 5)], 2)
            surface.blit(done_s, tr)
        else:
            self._collect_btn.draw(surface)

        self._back_btn.draw(surface)
        hint = self._font_xs.render("Esc / B — back  |  Space — collect token",
                                     True, C.LIGHT_GREY)
        surface.blit(hint, (w - hint.get_width() - pad, h - 18))

        # ── Fade-in overlay ───────────────────────────────────────────────
        if self._fade_alpha > 0:
            fade = pygame.Surface((w, h))
            fade.fill(C.BG_COLOUR)
            fade.set_alpha(int(self._fade_alpha))
            surface.blit(fade, (0, 0))


def _wrap(text, font, max_w):
    max_w = int(max_w * 0.78)
    words = text.split()
    lines, cur = [], []
    for word in words:
        test = " ".join(cur + [word])
        if font.size(test)[0] <= max_w:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _draw_fitted_line(surface, text, colour, x, y, max_w, fonts):
    for font in fonts:
        if font.size(text)[0] <= max_w:
            surface.blit(font.render(text, True, colour), (x, y))
            return

    font = fonts[-1]
    ellipsis = "..."
    trimmed = text
    while trimmed and font.size(trimmed + ellipsis)[0] > max_w:
        trimmed = trimmed[:-1].rstrip()
    surface.blit(font.render(trimmed + ellipsis, True, colour), (x, y))
