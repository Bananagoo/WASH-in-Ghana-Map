import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src.assets import load_image, load_image_fit, stop_placeholder, token_badge, THEME_COLOURS
from src.animation import TokenCoinEffect
from src import config as C
from src.constants import SCREEN_ROUTE


# Category name → colour (for pill tags) — matches updated categories.json names
_CAT_COLOURS = {
    "Health & Wellbeing":                (200,  70,  70),
    "Infrastructure & Technology":        (80,  120, 185),
    "Governance, Finance & Institutions": (130,  80, 185),
    "Culture, History & Place":           (195, 145,  50),
    "Gender, Equity & Safety":            (200,  95, 155),
    "Climate, Environment & Ecosystems":  (55,  160,  85),
    "Livelihoods & Economy":              (165, 120,  55),
    "Data, Knowledge & Collaboration":    (47,  140, 130),
}

# Secondary image display size (for Stop 9 treatment diagram)
_SEC_IMG_W = 560
_SEC_IMG_H = 300


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

        self._stop = None
        self._token_collected = False
        self._stop_image: pygame.Surface = None
        self._secondary_image: pygame.Surface = None
        self._token_badge: pygame.Surface = None

        self._fade_alpha = 200.0
        self._scroll_y = 0
        self._content_max_scroll = 0
        self._coin_effect: TokenCoinEffect = None

    def set_stop(self, stop):
        self._stop = stop
        state = self.game.state
        self._token_collected = state.is_stop_completed(stop.id)
        self._collect_btn.visible = not self._token_collected

        self._stop_image = load_image_fit(stop.image, self.IMG_W, self.IMG_H) if stop.image else None
        self._secondary_image = (
            load_image_fit(stop.secondary_image, _SEC_IMG_W, _SEC_IMG_H)
            if stop.secondary_image else None
        )
        self._token_badge = (load_image(stop.token_image, (36, 36))
                             if stop.token_image else None)
        self._fade_alpha = 200.0
        self._scroll_y = 0
        self._content_max_scroll = 0

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
            elif event.key == pygame.K_DOWN:
                self._scroll_y = min(self._scroll_y + 30, self._content_max_scroll)
            elif event.key == pygame.K_UP:
                self._scroll_y = max(self._scroll_y - 30, 0)
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_y = max(0, min(self._scroll_y - event.y * 24, self._content_max_scroll))

    def _collect_token(self):
        if not self._stop:
            return
        self.game.state.mark_stop_complete(self._stop.id, self._stop.token)
        self.game.audio.play("collect")
        self._token_collected = True
        self._collect_btn.visible = False
        # Spawn coin animation in the center of the screen
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        badge = token_badge(self._stop.token, size=80)
        self._coin_effect = TokenCoinEffect(badge, (w // 2, h // 2), target_size=80)

    def update(self, dt: float):
        if self._fade_alpha > 0:
            self._fade_alpha = max(0.0, self._fade_alpha - 220 * dt / 0.35)
        if self._coin_effect:
            self._coin_effect.update(dt)
            if self._coin_effect.done:
                self._coin_effect = None

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

        # ── Top section: image (left) + token / categories / what-happened (right) ──
        img_x, img_y = pad, 80
        img_rect = pygame.Rect(img_x, img_y, self.IMG_W, self.IMG_H)

        if self._stop_image:
            iw, ih = self._stop_image.get_size()
            ix = img_x + (self.IMG_W - iw) // 2
            fitted_rect = pygame.Rect(ix, img_y, iw, ih)
            surface.blit(self._stop_image, (ix, img_y))
            pygame.draw.rect(surface, C.GOLD, fitted_rect, width=2, border_radius=4)
        else:
            ph = stop_placeholder(self.IMG_W, self.IMG_H,
                                   stop.icon_label, stop.visual_theme, self._font_lg)
            surface.blit(ph, img_rect)

        right_x = img_x + self.IMG_W + pad
        right_w  = w - right_x - pad

        badge_surf = (self._token_badge
                      if self._token_badge
                      else token_badge(stop.token, size=40, bg_colour=C.GOLD))
        surface.blit(badge_surf, (right_x, img_y))

        tok_s = self._font_md.render(stop.token, True, C.TEAL_DARK)
        surface.blit(tok_s, (right_x + 48, img_y + 10))

        # WASH focus label
        pill_y = img_y + 50
        if stop.wash_focus:
            wf_lbl = self._font_xs.render("WASH FOCUS", True, C.MID_GREY)
            surface.blit(wf_lbl, (right_x, pill_y))
            wf_val = self._font_xs.render(stop.wash_focus, True, C.DARK_GREY)
            surface.blit(wf_val, (right_x + wf_lbl.get_width() + 6, pill_y))
            pill_y += wf_lbl.get_height() + 4

        # Category pills
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

        pill_y += 28

        # What Happened (top-right brief summary)
        wh_y = pill_y
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

        # ── Scrollable content area ───────────────────────────────────────
        BOTTOM_BAR = 80
        content_top = section_top + 2
        content_bottom = h - BOTTOM_BAR
        clip_rect = pygame.Rect(0, content_top, w, content_bottom - content_top)
        surface.set_clip(clip_rect)

        y = content_top + 8 - self._scroll_y

        def section(label, body, text_col=C.DARK_GREY):
            nonlocal y
            lbl = self._font_xs.render(label.upper(), True, C.MID_GREY)
            surface.blit(lbl, (pad, y))
            y += lbl.get_height() + 2
            y = draw_wrapped_text(surface, body, self._font_sm, text_col,
                                  pad, y, w - pad * 2, line_spacing=4)
            y += C.PAD_SM

        section("Key Learning", stop.key_learning, C.TEAL_DARK)
        section("Key Concepts", stop.course_concept)

        # Field Note box
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

        # Secondary image (treatment process diagram — Stop 9)
        if self._secondary_image:
            sec_lbl = self._font_xs.render("TREATMENT PROCESS", True, C.MID_GREY)
            surface.blit(sec_lbl, (pad, y))
            y += sec_lbl.get_height() + 4
            siw, sih = self._secondary_image.get_size()
            six = pad + (_SEC_IMG_W - siw) // 2
            surface.blit(self._secondary_image, (six, y))
            pygame.draw.rect(surface, C.TEAL, pygame.Rect(six, y, siw, sih), 2, border_radius=4)
            y += sih + C.PAD_SM
            desc = ("Intake and pumping → Coagulation (alum) → Flocculation → "
                    "Filtration → Chlorination → Quality assessment before distribution.")
            y = draw_wrapped_text(surface, desc, self._font_xs, C.MID_GREY,
                                  pad, y, w - pad * 2, line_spacing=3)
            y += C.PAD_SM

        # References
        if stop.references:
            ref_lbl = self._font_xs.render("REFERENCES", True, C.MID_GREY)
            surface.blit(ref_lbl, (pad, y))
            y += ref_lbl.get_height() + 4
            pygame.draw.line(surface, C.LIGHT_GREY, (pad, y), (w - pad, y))
            y += 4
            for ref in stop.references:
                ref_text = ref
                y = draw_wrapped_text(
                    surface, ref_text, self._font_xs, C.MID_GREY,
                    pad, y, w - pad * 2, line_spacing=2,
                )
                y += 3

        y += C.PAD
        self._content_max_scroll = max(0, y + self._scroll_y - content_bottom)
        surface.set_clip(None)

        # Scroll indicator
        if self._content_max_scroll > 0:
            scroll_hint = self._font_xs.render(
                "↑↓ scroll or use mouse wheel", True, C.MID_GREY)
            surface.blit(scroll_hint,
                         (w // 2 - scroll_hint.get_width() // 2, content_bottom - 18))

        # ── Bottom buttons ────────────────────────────────────────────────
        if self._token_collected:
            done_s = self._font_md.render(f"{stop.token} collected!", True, C.TEAL_DARK)
            tr = done_s.get_rect(center=(w // 2, h - 48))
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

        # ── Token coin collection animation ───────────────────────────────
        if self._coin_effect:
            self._coin_effect.draw(surface)

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
