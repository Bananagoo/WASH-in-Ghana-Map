import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, draw_wrapped_text, FontCache, draw_panel
from src import config as C
from src.constants import SCREEN_ROUTE

# Deep ocean-blue palette for the title screen
_BG          = (16, 36, 72)          # deep navy blue
_HEADER_BG   = (22, 65, 128)         # vivid navy header (visible on dark bg)
_PANEL_BG    = (22, 50, 92)          # medium blue panel
_PANEL_BDR   = (95, 155, 215)        # sky-blue border
_STRIP_GOLD  = (210, 165, 50)        # gold accent stripe (unchanged)
_STRIP_BLUE  = (65, 120, 195)        # blue accent stripe
_DOT         = (28, 58, 108)         # subtle darker-navy dots


def _draw_dot_pattern(surface, rect, colour, spacing=28):
    for gy in range(rect.top + spacing // 2, rect.bottom, spacing):
        for gx in range(rect.left + spacing // 2, rect.right, spacing):
            pygame.draw.circle(surface, colour, (gx, gy), 2)


class TitleScreen(BaseScreen):

    def on_enter(self):
        txt    = self.game.text
        w, h   = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        self._font_title = FontCache.get(C.FONT_XL + 10)
        self._font_sub   = FontCache.get(C.FONT_LG)
        self._font_md    = FontCache.get(C.FONT_MD)
        self._font_sm    = FontCache.get(C.FONT_SM)
        self._font_xs    = FontCache.get(C.FONT_XS)

        btn_w, btn_h = 240, 52
        self._start_btn = Button(
            pygame.Rect(w // 2 - btn_w // 2, h - 108, btn_w, btn_h),
            "Begin Field Survey",
            self._font_md,
            colour=C.GOLD,
            hover_colour=C.RUST,
            text_colour=C.DARK_GREY,
        )

        self._tutorial_lines = txt.tutorial
        self._title    = txt.title
        self._subtitle = txt.subtitle
        self._course   = txt.course

    def handle_event(self, event: pygame.event.Event):
        if self._start_btn.handle_event(event):
            self.game.audio.play("click")
            self.game.state.go_to(SCREEN_ROUTE)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.game.audio.play("click")
                self.game.state.go_to(SCREEN_ROUTE)

    def draw(self, surface: pygame.Surface):
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # ── Dark background with dot texture ──────────────────────────────────
        surface.fill(_BG)
        _draw_dot_pattern(surface, pygame.Rect(0, 0, w, h), _DOT)

        # ── Header band ───────────────────────────────────────────────────────
        HEADER_H = 196
        pygame.draw.rect(surface, _HEADER_BG, pygame.Rect(0, 0, w, HEADER_H))

        # Gold stripe under header
        pygame.draw.rect(surface, _STRIP_GOLD, pygame.Rect(0, HEADER_H, w, 5))
        # Blue accent stripe above gold
        pygame.draw.rect(surface, _STRIP_BLUE, pygame.Rect(0, HEADER_H - 3, w, 3))

        # Decorative side notches on header
        pygame.draw.rect(surface, _STRIP_GOLD, pygame.Rect(0, 0, 6, HEADER_H))
        pygame.draw.rect(surface, _STRIP_GOLD, pygame.Rect(w - 6, 0, 6, HEADER_H))

        # Title
        title_s = self._font_title.render(self._title, True, C.GOLD)
        surface.blit(title_s, title_s.get_rect(center=(w // 2, 72)))

        # Subtitle
        sub_s = self._font_sub.render(self._subtitle, True, C.WHITE)
        surface.blit(sub_s, sub_s.get_rect(center=(w // 2, 126)))

        # Course label
        course_s = self._font_xs.render(self._course, True, C.TEAL_LIGHT)
        surface.blit(course_s, course_s.get_rect(center=(w // 2, 164)))

        # ── Tutorial panel ────────────────────────────────────────────────────
        panel_w   = 740
        panel_x   = w // 2 - panel_w // 2
        panel_top = HEADER_H + 22
        panel_bot = h - 140
        panel_rect = pygame.Rect(panel_x, panel_top, panel_w, panel_bot - panel_top)
        draw_panel(surface, panel_rect, _PANEL_BG, _PANEL_BDR, radius=10)

        # "HOW TO PLAY" label
        how_s = self._font_xs.render("HOW TO PLAY", True, C.GOLD)
        surface.blit(how_s,
                     (panel_rect.left + C.PAD_LG, panel_rect.top + C.PAD))

        # Horizontal rule under label
        rule_y = panel_rect.top + C.PAD + how_s.get_height() + 6
        pygame.draw.line(surface, _PANEL_BDR,
                         (panel_rect.left + C.PAD_LG, rule_y),
                         (panel_rect.right - C.PAD_LG, rule_y), 1)

        max_w = panel_w - C.PAD_LG * 2
        ty = rule_y + 12
        for line in self._tutorial_lines:
            ty = draw_wrapped_text(
                surface, line, self._font_sm, C.OFF_WHITE,
                panel_rect.left + C.PAD_LG, ty, max_w, line_spacing=5,
            )
            ty += 6

        # ── Start button ──────────────────────────────────────────────────────
        self._start_btn.draw(surface)

        # Hint
        hint_s = self._font_xs.render("or press  Space / Enter", True, C.MID_GREY)
        surface.blit(hint_s, hint_s.get_rect(center=(w // 2, h - 38)))
