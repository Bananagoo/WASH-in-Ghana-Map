import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache
from src.assets import token_badge
from src import config as C
from src.constants import SCREEN_ROUTE, SCREEN_WASH_RESULT

_CATEGORIES = [
    ("health",         "Health & Wellbeing",                (200,  70,  70)),
    ("infrastructure", "Infrastructure & Technology",        (80,  120, 185)),
    ("governance",     "Governance, Finance & Institutions", (130,  80, 185)),
    ("culture",        "Culture, History & Place",           (195, 145,  50)),
    ("gender",         "Gender, Equity & Safety",            (200,  95, 155)),
    ("climate",        "Climate, Environment & Ecosystems",  (55,  160,  85)),
    ("livelihoods",    "Livelihoods & Economy",              (165, 120,  55)),
    ("knowledge",      "Data, Knowledge & Collaboration",    (47,  140, 130)),
]

HEADER_H = 65
BOTTOM_H = 72
TRAY_W   = 165
PAD      = 12
BADGE_SZ = 36
SLOT_H   = 50
ITEM_H   = 46


class WashMapScreen(BaseScreen):

    def on_enter(self):
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        self._compare_btn = Button(
            pygame.Rect(w // 2 - 140, h - BOTTOM_H + 13, 280, 46),
            "Compare My Map →",
            self._font_md,
            colour=C.GOLD, hover_colour=C.RUST, text_colour=C.DARK_GREY,
        )
        self._back_btn = Button(
            pygame.Rect(PAD, h - BOTTOM_H + 18, 110, 36),
            "← Back",
            self._font_sm,
            colour=C.MID_GREY, hover_colour=C.DARK_GREY,
        )

        self._cards = self._build_cards()
        self._tray_scroll = 0
        self._tray_clip = pygame.Rect(0, HEADER_H + 22, TRAY_W, h - HEADER_H - BOTTOM_H - 22)

        self._drag_token: str = None
        self._drag_pos   = (0, 0)

        self._badges = {
            tok: token_badge(tok, size=BADGE_SZ)
            for tok in self.game.state.collected_tokens
        }

    def _build_cards(self):
        w, h   = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        cx0    = TRAY_W + PAD
        cy0    = HEADER_H + PAD
        area_w = w - cx0 - PAD
        area_h = h - HEADER_H - BOTTOM_H - PAD * 2

        col_gap = 10
        row_gap = 8
        card_w  = (area_w - col_gap) // 2
        card_h  = (area_h - 3 * row_gap) // 4

        label_h = self._font_xs.get_height()
        slot_lpad  = 14
        slot_rpad  = 8
        slot_avail = card_w - slot_lpad - slot_rpad
        slot_gap   = 8
        slot_w     = (slot_avail - slot_gap) // 2
        slot_y_off = 8 + label_h + 6   # from card top

        cards = []
        for i, (cat_id, cat_name, colour) in enumerate(_CATEGORIES):
            col = i % 2
            row = i // 2
            rx  = cx0 + col * (card_w + col_gap)
            ry  = cy0 + row * (card_h + row_gap)
            card_rect = pygame.Rect(rx, ry, card_w, card_h)
            slot_y    = ry + slot_y_off
            slots = [
                pygame.Rect(rx + slot_lpad, slot_y, slot_w, SLOT_H),
                pygame.Rect(rx + slot_lpad + slot_w + slot_gap, slot_y, slot_w, SLOT_H),
            ]
            cards.append({
                "cat_id":   cat_id,
                "cat_name": cat_name,
                "colour":   colour,
                "rect":     card_rect,
                "slots":    slots,
            })
        return cards

    # ── helpers ───────────────────────────────────────────────────────────────

    def _unplaced_tokens(self):
        placed = set(self.game.state.wash_map_placements.keys())
        return [t for t in self.game.state.collected_tokens if t not in placed]

    def _tray_item_rects(self):
        rects = {}
        y = HEADER_H + 22 + PAD - self._tray_scroll
        for tok in self._unplaced_tokens():
            rects[tok] = pygame.Rect(4, y, TRAY_W - 8, ITEM_H)
            y += ITEM_H + 4
        return rects

    def _tray_max_scroll(self):
        n       = len(self._unplaced_tokens())
        total_h = n * (ITEM_H + 4)
        visible = C.SCREEN_HEIGHT - HEADER_H - BOTTOM_H - 22
        return max(0, total_h - visible)

    def _tokens_in_cat(self, cat_id):
        p = self.game.state.wash_map_placements
        return [t for t, c in p.items() if c == cat_id]

    def _all_placed(self):
        return len(self.game.state.wash_map_placements) >= 16

    # ── events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        state = self.game.state

        if self._back_btn.handle_event(event):
            self.game.audio.play("click")
            state.go_to(SCREEN_ROUTE)
            return

        if self._all_placed() and self._compare_btn.handle_event(event):
            self.game.audio.play("transition")
            state.go_to(SCREEN_WASH_RESULT)
            return

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if self._tray_clip.collidepoint(mx, my):
                self._tray_scroll = max(0, min(
                    self._tray_scroll - event.y * 20,
                    self._tray_max_scroll(),
                ))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Pick up from tray
            for tok, r in self._tray_item_rects().items():
                if r.collidepoint(pos):
                    self._drag_token = tok
                    self._drag_pos   = pos
                    return
            # Pick up from a filled slot
            for card in self._cards:
                tokens = self._tokens_in_cat(card["cat_id"])
                for i, slot in enumerate(card["slots"]):
                    if slot.collidepoint(pos) and i < len(tokens):
                        tok = tokens[i]
                        del state.wash_map_placements[tok]
                        self._drag_token = tok
                        self._drag_pos   = pos
                        return

        if event.type == pygame.MOUSEMOTION and self._drag_token:
            self._drag_pos = event.pos

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not self._drag_token:
                return
            pos = event.pos
            # Try to drop on a card with a free slot
            for card in self._cards:
                if card["rect"].collidepoint(pos):
                    tokens = self._tokens_in_cat(card["cat_id"])
                    if len(tokens) < 2:
                        state.wash_map_placements[self._drag_token] = card["cat_id"]
                    # If card is full, token returns to tray (not placed)
                    break
            # Otherwise token silently returns to tray (wash_map_placements unchanged)
            self._drag_token = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._drag_token:
                    self._drag_token = None
                else:
                    state.go_to(SCREEN_ROUTE)

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        surface.fill(C.BG_COLOUR)
        w, h  = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        state = self.game.state

        # Header
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, HEADER_H - 4))
        pygame.draw.rect(surface, C.GOLD,      pygame.Rect(0, HEADER_H - 4, w, 4))
        title_s = self._font_md.render("Build the WASH Systems Map", True, C.WHITE)
        surface.blit(title_s, title_s.get_rect(centerx=w // 2, centery=(HEADER_H - 4) // 2))
        placed = len(state.wash_map_placements)
        count_s = self._font_xs.render(f"{placed} / 16 placed", True, C.GOLD_LIGHT)
        surface.blit(count_s, (PAD, (HEADER_H - 4) // 2 - count_s.get_height() // 2))

        # Tray panel
        tray_bg = pygame.Rect(0, HEADER_H, TRAY_W, h - HEADER_H - BOTTOM_H)
        pygame.draw.rect(surface, (22, 40, 70), tray_bg)
        pygame.draw.line(surface, C.GOLD, (TRAY_W, HEADER_H), (TRAY_W, h - BOTTOM_H), 2)
        lbl_s = self._font_xs.render("TOKENS", True, C.GOLD_LIGHT)
        surface.blit(lbl_s, (PAD, HEADER_H + 6))

        # Tray items (clipped)
        surface.set_clip(self._tray_clip)
        for tok, r in self._tray_item_rects().items():
            if tok == self._drag_token:
                continue
            pygame.draw.rect(surface, (35, 60, 100), r, border_radius=6)
            pygame.draw.rect(surface, C.GOLD, r, 1, border_radius=6)
            badge = self._badges.get(tok)
            if badge:
                surface.blit(badge, (r.left + 4, r.centery - BADGE_SZ // 2))
            name_s = self._font_xs.render(tok, True, C.OFF_WHITE)
            nx = r.left + BADGE_SZ + 8
            if name_s.get_width() > TRAY_W - BADGE_SZ - 18:
                name_s = self._font_xs.render(tok[:10] + "…", True, C.OFF_WHITE)
            surface.blit(name_s, name_s.get_rect(midleft=(nx, r.centery)))
        surface.set_clip(None)

        # Dimension cards
        for card in self._cards:
            self._draw_card(surface, card)

        # Bottom bar
        pygame.draw.line(surface, C.LIGHT_GREY, (0, h - BOTTOM_H), (w, h - BOTTOM_H), 1)
        if self._all_placed():
            self._compare_btn.draw(surface)
        else:
            hint_s = self._font_xs.render(
                "Place all 16 tokens to compare your map.", True, C.MID_GREY)
            surface.blit(hint_s, hint_s.get_rect(center=(w // 2, h - BOTTOM_H + BOTTOM_H // 2)))
        self._back_btn.draw(surface)

        # Drag ghost
        if self._drag_token:
            dx, dy = self._drag_pos
            badge = self._badges.get(self._drag_token)
            if badge:
                b = BADGE_SZ
                surface.blit(badge, (dx - b // 2, dy - b // 2))
                name_s = self._font_xs.render(self._drag_token, True, C.WHITE)
                surface.blit(name_s, (dx - name_s.get_width() // 2, dy + b // 2 + 2))

    def _draw_card(self, surface, card):
        rect     = card["rect"]
        colour   = card["colour"]
        cat_id   = card["cat_id"]
        cat_name = card["cat_name"]

        pygame.draw.rect(surface, (28, 48, 85), rect, border_radius=8)
        pygame.draw.rect(surface, colour, rect, 1, border_radius=8)

        # Left colour bar
        bar = pygame.Rect(rect.left + 2, rect.top + 2, 5, rect.height - 4)
        pygame.draw.rect(surface, colour, bar, border_radius=4)

        # Category name (truncated if needed)
        name_surf = self._font_xs.render(cat_name, True, colour)
        max_name_w = rect.width - 20
        if name_surf.get_width() > max_name_w:
            while cat_name and self._font_xs.size(cat_name + "…")[0] > max_name_w:
                cat_name = cat_name[:-1]
            name_surf = self._font_xs.render(cat_name + "…", True, colour)
        surface.blit(name_surf, (rect.left + 14, rect.top + 8))

        # Slots
        tokens = self._tokens_in_cat(cat_id)
        for i, slot in enumerate(card["slots"]):
            tok    = tokens[i] if i < len(tokens) else None
            is_dragging = tok and tok == self._drag_token

            if tok and not is_dragging:
                pygame.draw.rect(surface, (45, 80, 130), slot, border_radius=6)
                pygame.draw.rect(surface, colour, slot, 1, border_radius=6)
                badge = self._badges.get(tok)
                if badge:
                    surface.blit(badge, (slot.left + 4, slot.centery - BADGE_SZ // 2))
                avail_w = slot.width - BADGE_SZ - 14
                name_s  = self._font_xs.render(tok, True, C.OFF_WHITE)
                if name_s.get_width() > avail_w:
                    short = tok
                    while short and self._font_xs.size(short + "…")[0] > avail_w:
                        short = short[:-1]
                    name_s = self._font_xs.render(short + "…", True, C.OFF_WHITE)
                surface.blit(name_s, name_s.get_rect(
                    midleft=(slot.left + BADGE_SZ + 8, slot.centery)))
            else:
                # Empty or mid-drag — show droppable target
                pygame.draw.rect(surface, (15, 30, 55), slot, border_radius=6)
                pygame.draw.rect(surface, (60, 90, 120), slot, 1, border_radius=6)
                hint = self._font_xs.render("drop here", True, (60, 90, 120))
                surface.blit(hint, hint.get_rect(center=slot.center))
