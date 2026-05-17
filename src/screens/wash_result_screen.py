import json
import os
import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src.assets import token_badge
from src import config as C
from src.constants import SCREEN_WASH_MAP

_HEADER_H = 65
_BOTTOM_H = 65
_BADGE_SZ = 32

_TAKEAWAY = [
    (
        "Your diagram may not match mine exactly, and that is part of the point. "
        "Each token came from one field moment, but most tokens connect to more "
        "than one part of the WASH system. WASH in Ghana is shaped by health, "
        "infrastructure, governance, culture, gender, climate, livelihoods, and "
        "knowledge at the same time."
    ),
    (
        "The final diagram shows that improving WASH systems cannot start and end "
        "with building more infrastructure. Lasting change also needs education, "
        "support, and mobilization. Communities need knowledge they can understand, "
        "question, and use. Local leaders, students, health workers, engineers, "
        "women's groups, farmers, and policymakers all hold pieces of the system. "
        "When those groups are supported and mobilized together, WASH becomes more "
        "than a service to deliver. It becomes a shared system people can protect, "
        "adapt, and improve."
    ),
]

_CAT_COLOURS = {
    "health":         (200,  70,  70),
    "infrastructure": (80,  120, 185),
    "governance":     (130,  80, 185),
    "culture":        (195, 145,  50),
    "gender":         (200,  95, 155),
    "climate":        (55,  160,  85),
    "livelihoods":    (165, 120,  55),
    "knowledge":      (47,  140, 130),
}


def _load_key():
    path = os.path.join("data", "wash_map_key.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["answer_key"]


class WashResultScreen(BaseScreen):

    def on_enter(self):
        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        self._again_btn = Button(
            pygame.Rect(w // 2 - 120, h - _BOTTOM_H + 10, 240, 42),
            "Play Again",
            self._font_md,
            colour=C.TEAL, hover_colour=C.TEAL_DARK,
        )
        self._back_btn = Button(
            pygame.Rect(C.PAD, h - _BOTTOM_H + 14, 130, 36),
            "← Back",
            self._font_sm,
            colour=C.MID_GREY, hover_colour=C.DARK_GREY,
        )

        # Load answer key and build category name lookup
        self._key = _load_key()
        self._cat_names = {cat.id: cat.name for cat in self.game.categories}

        # Build token → key_category_id mapping
        self._token_key_cat: dict = {}
        for cat_id, tokens in self._key.items():
            for tok in tokens:
                self._token_key_cat[tok] = cat_id

        # Compute similarity score
        state  = self.game.state
        placements = state.wash_map_placements
        score  = 0
        for tok, placed_cat in placements.items():
            if self._token_key_cat.get(tok) == placed_cat:
                score += 1
        state.wash_similarity_score = score

        # Pre-render token badges
        self._badges = {
            tok: token_badge(tok, size=_BADGE_SZ)
            for tok in self.game.state.collected_tokens
        }

        # Scroll state for comparison panel
        self._scroll_y = 0
        self._max_scroll = 0

    def handle_event(self, event: pygame.event.Event):
        state = self.game.state

        if self._back_btn.handle_event(event):
            self.game.audio.play("click")
            state.go_to(SCREEN_WASH_MAP)
            return

        if self._again_btn.handle_event(event):
            self.game.audio.play("click")
            self.game.restart_to_title()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                state.go_to(SCREEN_WASH_MAP)
            elif event.key == pygame.K_DOWN:
                self._scroll_y = min(self._scroll_y + 30, self._max_scroll)
            elif event.key == pygame.K_UP:
                self._scroll_y = max(self._scroll_y - 30, 0)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_y = max(0, min(
                self._scroll_y - event.y * 24, self._max_scroll))

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        w, h  = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        state = self.game.state
        score = state.wash_similarity_score or 0

        # ── Header ────────────────────────────────────────────────────────
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, _HEADER_H - 4))
        pygame.draw.rect(surface, C.GOLD,      pygame.Rect(0, _HEADER_H - 4, w, 4))
        title_s = self._font_md.render("WASH Systems Diagram — Results", True, C.WHITE)
        surface.blit(title_s, title_s.get_rect(centerx=w // 2, centery=(_HEADER_H - 4) // 2))

        # ── Score banner (full width) ──────────────────────────────────────
        SCORE_H  = 52
        score_y0 = _HEADER_H
        pygame.draw.rect(surface, C.PANEL_COLOUR,
                         pygame.Rect(0, score_y0, w, SCORE_H))
        pygame.draw.line(surface, C.LIGHT_GREY,
                         (0, score_y0 + SCORE_H - 1), (w, score_y0 + SCORE_H - 1))

        score_s = self._font_lg.render(
            f"Your diagram is  {score} / 16  similar to mine.", True, C.TEAL_DARK)
        surface.blit(score_s, score_s.get_rect(
            centerx=w // 2, centery=score_y0 + SCORE_H // 2))

        # ── Two-column layout below score ─────────────────────────────────
        CONTENT_Y = score_y0 + SCORE_H + 4
        CONTENT_H = h - CONTENT_Y - _BOTTOM_H
        LEFT_W    = 590
        RIGHT_X   = LEFT_W + 8
        RIGHT_W   = w - RIGHT_X - C.PAD

        # Left panel: token comparison (scrollable)
        left_clip = pygame.Rect(0, CONTENT_Y, LEFT_W, CONTENT_H)
        surface.set_clip(left_clip)

        ROW_H   = 32
        TOKEN_W = 210  # badge + name column
        y = CONTENT_Y + 4 - self._scroll_y

        # Column headers
        hdr_col = (80, 95, 115)
        tok_hdr = self._font_xs.render("TOKEN", True, hdr_col)
        surface.blit(tok_hdr, (C.PAD, y))
        result_hdr = self._font_xs.render("RESULT", True, hdr_col)
        surface.blit(result_hdr, (C.PAD + TOKEN_W, y))
        y += self._font_xs.get_height() + 4
        pygame.draw.line(surface, C.LIGHT_GREY, (C.PAD, y), (LEFT_W - C.PAD, y))
        y += 3

        tokens_ordered = self.game.state.collected_tokens
        for tok in tokens_ordered:
            placed_cat = state.wash_map_placements.get(tok, "")
            key_cat    = self._token_key_cat.get(tok, "")
            match      = placed_cat == key_cat and placed_cat != ""

            row_rect = pygame.Rect(C.PAD, y, LEFT_W - C.PAD * 2, ROW_H)
            if tokens_ordered.index(tok) % 2 == 0:
                pygame.draw.rect(surface, (240, 237, 228), row_rect, border_radius=4)

            # Badge
            badge = self._badges.get(tok)
            if badge:
                surface.blit(badge, (C.PAD + 2, y + ROW_H // 2 - _BADGE_SZ // 2))

            # Token name
            name_s = self._font_xs.render(tok, True, C.DARK_GREY)
            surface.blit(name_s, name_s.get_rect(
                midleft=(C.PAD + _BADGE_SZ + 6, y + ROW_H // 2)))

            # Result text
            if match:
                result_text = "Similar placement"
                result_col  = C.TEAL_DARK
            else:
                key_name    = self._cat_names.get(key_cat, key_cat)
                result_text = f"I placed this under {key_name}."
                result_col  = (160, 110, 30)

            result_s = self._font_xs.render(result_text, True, result_col)
            rx = C.PAD + TOKEN_W
            avail = LEFT_W - rx - C.PAD
            if result_s.get_width() > avail:
                # Wrap to two lines
                words = result_text.split()
                line1, line2 = [], []
                for word in words:
                    test = " ".join(line1 + [word])
                    if self._font_xs.size(test)[0] <= avail:
                        line1.append(word)
                    else:
                        line2.append(word)
                s1 = self._font_xs.render(" ".join(line1), True, result_col)
                s2 = self._font_xs.render(" ".join(line2), True, result_col)
                surface.blit(s1, (rx, y + ROW_H // 2 - self._font_xs.get_height()))
                surface.blit(s2, (rx, y + ROW_H // 2))
            else:
                surface.blit(result_s, result_s.get_rect(midleft=(rx, y + ROW_H // 2)))

            y += ROW_H

        total_rows_h = y + self._scroll_y - (CONTENT_Y + 4)
        self._max_scroll = max(0, total_rows_h - CONTENT_H)
        surface.set_clip(None)

        # Scroll indicator for left panel
        if self._max_scroll > 0:
            sc_s = self._font_xs.render("scroll to see more", True, C.MID_GREY)
            surface.blit(sc_s, (C.PAD, h - _BOTTOM_H - sc_s.get_height() - 4))

        # Divider between panels
        pygame.draw.line(surface, C.LIGHT_GREY,
                         (RIGHT_X - 4, CONTENT_Y), (RIGHT_X - 4, h - _BOTTOM_H), 1)

        # Right panel: takeaway text
        take_y = CONTENT_Y + 4
        take_lbl = self._font_xs.render("FINAL TAKEAWAY", True, C.MID_GREY)
        surface.blit(take_lbl, (RIGHT_X, take_y))
        take_y += take_lbl.get_height() + 4
        pygame.draw.line(surface, C.LIGHT_GREY,
                         (RIGHT_X, take_y), (RIGHT_X + RIGHT_W, take_y))
        take_y += 8

        for para in _TAKEAWAY:
            take_y = draw_wrapped_text(
                surface, para, self._font_sm, C.DARK_GREY,
                RIGHT_X, take_y, RIGHT_W, line_spacing=5,
            )
            take_y += 12

        # ── Bottom bar ────────────────────────────────────────────────────
        pygame.draw.line(surface, C.LIGHT_GREY, (0, h - _BOTTOM_H), (w, h - _BOTTOM_H), 1)
        self._again_btn.draw(surface)
        self._back_btn.draw(surface)
