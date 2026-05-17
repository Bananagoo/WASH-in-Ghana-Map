import math
import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache, draw_wrapped_text
from src.assets import token_badge
from src import config as C
from src.constants import SCREEN_ROUTE, SCREEN_WASH_RESULT

# Hub geometry
_HUB_CX   = 594   # centre x of diagram area
_HUB_CY   = 356   # centre y
_HUB_R    = 50    # hub circle radius
_NODE_R   = 205   # distance from hub centre to each dimension node
_CARD_W   = 140   # dimension card width
_CARD_H   = 104   # dimension card height

HEADER_H  = 65
BOTTOM_H  = 72
TRAY_W    = 165
PAD       = 10
BADGE_SZ  = 30
ITEM_H    = 44
SLOT_W    = 62    # each of the two slots per card
SLOT_H    = 36

# angle (deg, clockwise from top) → category
_CATEGORIES = [
    ("health",         "Health &\nWellbeing",               (200,  70,  70),   0),
    ("infrastructure", "Infrastructure &\nTechnology",       (80,  120, 185),  45),
    ("governance",     "Governance,\nFinance &\nInstitutions",(130,  80, 185), 90),
    ("culture",        "Culture, History\n& Place",          (195, 145,  50), 135),
    ("gender",         "Gender, Equity\n& Safety",           (200,  95, 155), 180),
    ("climate",        "Climate, Env. &\nEcosystems",        (55,  160,  85), 225),
    ("livelihoods",    "Livelihoods &\nEconomy",             (165, 120,  55), 270),
    ("knowledge",      "Data, Knowledge\n& Collaboration",   (47,  140, 130), 315),
]

_TOKEN_REMINDERS = {
    "Field Passport":  "The start of the journey and the importance of context.",
    "Test Strip":      "Invisible water risks revealed through testing.",
    "Sludge Truck":    "The sanitation chain after a toilet is used.",
    "Black Star Coin": "National development, public memory, and basic services.",
    "First Aid Cross": "WASH impacts on health systems and care access.",
    "Stream Stone":    "Water shaped by authority, land, and spiritual meaning.",
    "Toilet":          "Sanitation design connected to dignity and safety.",
    "Histogram":       "Data, monitoring, and accountability in WASH systems.",
    "Pipe Valve":      "Centralized treatment, skilled workers, and reliable infrastructure.",
    "Bar of Soap":     "Hygiene education and everyday disease prevention.",
    "Shell":           "Colonial history, memory, and inherited inequality.",
    "Fish":            "Food safety, women's livelihoods, and market pressure.",
    "Bamboo":          "Sacred groves, local knowledge, and environmental protection.",
    "Canopy Leaf":     "Forests, watersheds, and climate resilience.",
    "Camera":          "Photo-elicitation, lived experience, and climate risk.",
    "Cocoa Pod":       "Farming, livelihoods, water, and governance.",
}

# Slightly lighter background for the diagram area
_DIAGRAM_BG  = (240, 238, 230)
_TRAY_BG     = (22,  40,  70)
_CARD_BG     = (55,  90, 145)
_SLOT_FILLED = (70, 115, 185)
_SLOT_EMPTY  = (38,  65, 108)
_HUB_COL     = (22,  45,  95)
_LINE_COL    = (160, 165, 175)

_INTRO_LINES = [
    "You collected 16 tokens from your field survey.",
    "Drag each token from the left tray into the dimension card where you think it fits best.",
    "Each dimension has two slots.",
    "When all 16 tokens are placed, click  Compare My Diagram  to see how your",
    "arrangement compares to mine. You can drag tokens back out to move them.",
]


def _node_pos(angle_deg):
    θ = math.radians(angle_deg)
    return (int(_HUB_CX + _NODE_R * math.sin(θ)),
            int(_HUB_CY - _NODE_R * math.cos(θ)))


class WashMapScreen(BaseScreen):

    def on_enter(self):
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        self._compare_btn = Button(
            pygame.Rect(w // 2 - 140, h - BOTTOM_H + 13, 280, 46),
            "Compare My Diagram >",
            self._font_md,
            colour=C.GOLD, hover_colour=C.RUST, text_colour=C.DARK_GREY,
        )
        self._back_btn = Button(
            pygame.Rect(PAD, h - BOTTOM_H + 18, 110, 36),
            "< Back",
            self._font_sm,
            colour=C.MID_GREY, hover_colour=C.DARK_GREY,
        )
        self._help_btn = Button(
            pygame.Rect(w - 34, (HEADER_H - 4 - 28) // 2, 28, 28),
            "?",
            self._font_sm,
            colour=(95, 155, 215),
            hover_colour=C.GOLD_LIGHT,
            text_colour=C.DARK_GREY,
            border_radius=14,
        )
        self._start_btn = Button(
            pygame.Rect(w // 2 - 110, 0, 220, 40),  # y set in draw
            "Start Building",
            self._font_md,
            colour=C.GOLD, hover_colour=C.RUST, text_colour=C.DARK_GREY,
        )

        self._cards = self._build_cards()
        self._tray_scroll  = 0
        self._tray_clip    = pygame.Rect(0, HEADER_H + 22, TRAY_W, h - HEADER_H - BOTTOM_H - 22)

        self._drag_token: str = None
        self._drag_pos = (0, 0)
        self._hover_token: str = None

        self._badges = {
            tok: token_badge(tok, size=BADGE_SZ)
            for tok in self.game.state.collected_tokens
        }
        self._token_locations = {
            stop.token: stop.title for stop in self.game.stops if stop.token
        }

        # Show instructions on first entry per session
        if not hasattr(self, "_intro_shown"):
            self._intro_shown = False
        self._show_intro = not self._intro_shown

    # ── card geometry ──────────────────────────────────────────────────────────

    def _build_cards(self):
        cards = []
        for cat_id, cat_name, colour, angle_deg in _CATEGORIES:
            nx, ny   = _node_pos(angle_deg)
            card_rect = pygame.Rect(nx - _CARD_W // 2, ny - _CARD_H // 2, _CARD_W, _CARD_H)

            # Spoke endpoint: corner for diagonals, edge-midpoint for axis-aligned
            if angle_deg % 90 == 0:
                if angle_deg == 0:    spoke_end = (card_rect.centerx, card_rect.bottom)
                elif angle_deg == 90:  spoke_end = (card_rect.left,    card_rect.centery)
                elif angle_deg == 180: spoke_end = (card_rect.centerx, card_rect.top)
                else:                  spoke_end = (card_rect.right,   card_rect.centery)
            else:
                ex = card_rect.left  if nx > _HUB_CX else card_rect.right
                ey = card_rect.bottom if ny < _HUB_CY else card_rect.top
                spoke_end = (ex, ey)

            # Two slots: start past the 5px colour strip (strip ends at left+7, add 3px gap)
            slot_y = card_rect.top + _CARD_H - SLOT_H - 5
            slot_x = card_rect.left + 10
            slots = [
                pygame.Rect(slot_x,              slot_y, SLOT_W, SLOT_H),
                pygame.Rect(slot_x + SLOT_W + 4, slot_y, SLOT_W, SLOT_H),
            ]
            cards.append({
                "cat_id":    cat_id,
                "cat_name":  cat_name,
                "colour":    colour,
                "rect":      card_rect,
                "node":      (nx, ny),
                "spoke_end": spoke_end,
                "slots":     slots,
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
        return max(0, total_h - visible + PAD)

    def _tokens_in_cat(self, cat_id):
        p = self.game.state.wash_map_placements
        return [t for t, c in p.items() if c == cat_id]

    def _all_placed(self):
        return len(self.game.state.wash_map_placements) >= 16

    # ── events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        state = self.game.state

        # Intro popup intercepts all events
        if self._show_intro:
            if self._start_btn.handle_event(event):
                self._show_intro = False
                self._intro_shown = True
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._show_intro = False
                self._intro_shown = True
            return

        if self._help_btn.handle_event(event):
            self._show_intro = True
            return

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

        if event.type == pygame.MOUSEMOTION:
            if self._drag_token:
                self._drag_pos = event.pos
            else:
                # Hover detection for tooltips
                pos = event.pos
                hover = None
                for tok, r in self._tray_item_rects().items():
                    if r.collidepoint(pos):
                        hover = tok
                        break
                if not hover:
                    for card in self._cards:
                        tokens = self._tokens_in_cat(card["cat_id"])
                        for i, slot in enumerate(card["slots"]):
                            if slot.collidepoint(pos) and i < len(tokens):
                                hover = tokens[i]
                                break
                self._hover_token = hover
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for tok, r in self._tray_item_rects().items():
                if r.collidepoint(pos):
                    self._drag_token = tok
                    self._drag_pos   = pos
                    self._hover_token = None
                    return
            for card in self._cards:
                tokens = self._tokens_in_cat(card["cat_id"])
                for i, slot in enumerate(card["slots"]):
                    if slot.collidepoint(pos) and i < len(tokens):
                        tok = tokens[i]
                        del state.wash_map_placements[tok]
                        self._drag_token = tok
                        self._drag_pos   = pos
                        self._hover_token = None
                        return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not self._drag_token:
                return
            pos = event.pos
            for card in self._cards:
                if card["rect"].collidepoint(pos):
                    tokens = self._tokens_in_cat(card["cat_id"])
                    if len(tokens) < 2:
                        state.wash_map_placements[self._drag_token] = card["cat_id"]
                    break
            self._drag_token = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._drag_token:
                    self._drag_token = None
                else:
                    state.go_to(SCREEN_ROUTE)

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        w, h  = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        state = self.game.state

        # Background: lighter cream for diagram area, dark for tray
        surface.fill(_DIAGRAM_BG)
        pygame.draw.rect(surface, _TRAY_BG, pygame.Rect(0, HEADER_H, TRAY_W, h - HEADER_H - BOTTOM_H))

        # ── Header ────────────────────────────────────────────────────────────
        pygame.draw.rect(surface, C.TEAL_DARK, pygame.Rect(0, 0, w, HEADER_H - 4))
        pygame.draw.rect(surface, C.GOLD,      pygame.Rect(0, HEADER_H - 4, w, 4))
        title_s = self._font_md.render("Build the WASH Systems Diagram", True, C.WHITE)
        surface.blit(title_s, title_s.get_rect(centerx=w // 2, centery=(HEADER_H - 4) // 2))
        placed  = len(state.wash_map_placements)
        count_s = self._font_xs.render(f"{placed} / 16 placed", True, C.GOLD_LIGHT)
        surface.blit(count_s, (PAD, (HEADER_H - 4) // 2 - count_s.get_height() // 2))
        self._help_btn.draw(surface)

        # ── Tray ──────────────────────────────────────────────────────────────
        pygame.draw.line(surface, C.GOLD, (TRAY_W, HEADER_H), (TRAY_W, h - BOTTOM_H), 2)
        lbl_s = self._font_xs.render("TOKENS", True, C.GOLD_LIGHT)
        surface.blit(lbl_s, (PAD, HEADER_H + 6))

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
            nx_ = r.left + BADGE_SZ + 8
            avail = TRAY_W - BADGE_SZ - 18
            if name_s.get_width() > avail:
                t = tok
                while t and self._font_xs.size(t + "…")[0] > avail:
                    t = t[:-1]
                name_s = self._font_xs.render(t + "…", True, C.OFF_WHITE)
            surface.blit(name_s, name_s.get_rect(midleft=(nx_, r.centery)))
        surface.set_clip(None)

        # ── Hub-and-spoke diagram ──────────────────────────────────────────────
        # Connecting lines (drawn first, behind everything)
        for card in self._cards:
            pygame.draw.line(surface, _LINE_COL, (_HUB_CX, _HUB_CY), card["spoke_end"], 2)

        # Dimension cards
        for card in self._cards:
            self._draw_card(surface, card)

        # Hub centre circle
        pygame.draw.circle(surface, _HUB_COL, (_HUB_CX, _HUB_CY), _HUB_R)
        pygame.draw.circle(surface, C.GOLD, (_HUB_CX, _HUB_CY), _HUB_R, 2)
        hub1 = self._font_xs.render("WASH", True, C.GOLD_LIGHT)
        hub2 = self._font_xs.render("in Ghana", True, C.GOLD_LIGHT)
        surface.blit(hub1, hub1.get_rect(centerx=_HUB_CX, centery=_HUB_CY - 8))
        surface.blit(hub2, hub2.get_rect(centerx=_HUB_CX, centery=_HUB_CY + 8))

        # ── Tooltip (hover) ───────────────────────────────────────────────────
        if self._hover_token and _TOKEN_REMINDERS.get(self._hover_token):
            reminder  = _TOKEN_REMINDERS[self._hover_token]
            loc_name  = self._token_locations.get(self._hover_token, "")
            tip_rect  = pygame.Rect(TRAY_W + 8, h - BOTTOM_H - 66, w - TRAY_W - 16, 62)
            pygame.draw.rect(surface, (20, 38, 68), tip_rect, border_radius=6)
            pygame.draw.rect(surface, C.GOLD, tip_rect, 1, border_radius=6)
            ty_ = tip_rect.top + 6
            name_s = self._font_xs.render(self._hover_token, True, C.GOLD_LIGHT)
            surface.blit(name_s, (tip_rect.left + 8, ty_))
            if loc_name:
                loc_s = self._font_xs.render(f"  |  {loc_name}", True, C.TEAL_LIGHT)
                surface.blit(loc_s, (tip_rect.left + 8 + name_s.get_width(), ty_))
            ty_ += name_s.get_height() + 3
            draw_wrapped_text(
                surface, reminder, self._font_xs, C.OFF_WHITE,
                tip_rect.left + 8, ty_,
                tip_rect.width - 16, line_spacing=2,
            )

        # ── Bottom bar ────────────────────────────────────────────────────────
        pygame.draw.line(surface, C.LIGHT_GREY, (0, h - BOTTOM_H), (w, h - BOTTOM_H), 1)
        if self._all_placed():
            self._compare_btn.draw(surface)
        else:
            hint_s = self._font_xs.render(
                "Place all 16 tokens to compare your diagram.", True, C.MID_GREY)
            surface.blit(hint_s, hint_s.get_rect(center=(w // 2, h - BOTTOM_H + BOTTOM_H // 2)))
        self._back_btn.draw(surface)

        # ── Intro popup ───────────────────────────────────────────────────────
        if self._show_intro:
            self._draw_intro(surface)

        # ── Drag ghost ────────────────────────────────────────────────────────
        if self._drag_token:
            dx, dy = self._drag_pos
            badge  = self._badges.get(self._drag_token)
            if badge:
                b = BADGE_SZ
                surface.blit(badge, (dx - b // 2, dy - b // 2))
                name_s = self._font_xs.render(self._drag_token, True, C.DARK_GREY)
                surface.blit(name_s, (dx - name_s.get_width() // 2, dy + b // 2 + 2))

    def _draw_intro(self, surface: pygame.Surface):
        from src.ui import draw_panel
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        dim = pygame.Surface((w, h)).convert()
        dim.fill((8, 18, 38))
        dim.set_alpha(210)
        surface.blit(dim, (0, 0))

        pw, ph = 560, 310
        px = w // 2 - pw // 2
        py = h // 2 - ph // 2
        draw_panel(surface, pygame.Rect(px, py, pw, ph),
                   (22, 45, 95), (95, 155, 215), radius=12)

        ty = py + 18
        title_s = self._font_md.render("Build Your WASH Systems Diagram", True, C.GOLD)
        surface.blit(title_s, title_s.get_rect(centerx=w // 2, top=ty))
        ty += title_s.get_height() + 8
        pygame.draw.line(surface, (95, 155, 215),
                         (px + 20, ty), (px + pw - 20, ty), 1)
        ty += 10

        for line in _INTRO_LINES:
            ls = self._font_xs.render(line, True, C.OFF_WHITE)
            surface.blit(ls, ls.get_rect(centerx=w // 2, top=ty))
            ty += ls.get_height() + 6

        ty += 8
        self._start_btn.rect.top = ty
        self._start_btn.draw(surface)

        hint_s = self._font_xs.render("or press  Space / Enter", True, C.MID_GREY)
        surface.blit(hint_s, hint_s.get_rect(
            centerx=w // 2, top=ty + self._start_btn.rect.height + 6))

    def _draw_card(self, surface, card):
        rect     = card["rect"]
        colour   = card["colour"]
        cat_id   = card["cat_id"]
        cat_name = card["cat_name"]

        # Card background
        pygame.draw.rect(surface, _CARD_BG, rect, border_radius=8)
        pygame.draw.rect(surface, colour, rect, 1, border_radius=8)

        # Left colour accent strip
        strip = pygame.Rect(rect.left + 2, rect.top + 2, 5, rect.height - 4)
        pygame.draw.rect(surface, colour, strip, border_radius=3)

        # Category name wraps inside the card instead of overflowing.
        lines = []
        for part in cat_name.split("\n"):
            lines.extend(_wrap_to_lines(part, self._font_xs, rect.width - 20))
        ty = rect.top + 7
        max_lines = max(1, (card["slots"][0].top - ty - 3) // (self._font_xs.get_height() + 2))
        for line in lines[:max_lines]:
            ls = self._font_xs.render(line, True, C.OFF_WHITE)
            surface.blit(ls, (rect.left + 12, ty))
            ty += self._font_xs.get_height() + 2

        # Token slots
        tokens = self._tokens_in_cat(cat_id)
        for i, slot in enumerate(card["slots"]):
            tok = tokens[i] if i < len(tokens) else None
            is_dragging = tok and tok == self._drag_token

            if tok and not is_dragging:
                pygame.draw.rect(surface, _SLOT_FILLED, slot, border_radius=5)
                pygame.draw.rect(surface, colour, slot, 1, border_radius=5)
                badge = self._badges.get(tok)
                if badge:
                    bs = min(slot.width - 4, slot.height - 4, 26)
                    scaled = pygame.transform.smoothscale(badge, (bs, bs))
                    surface.blit(scaled, scaled.get_rect(center=slot.center))
            else:
                pygame.draw.rect(surface, _SLOT_EMPTY, slot, border_radius=5)
                pygame.draw.rect(surface, (55, 85, 115), slot, 1, border_radius=5)
                plus = self._font_xs.render("+", True, (55, 85, 115))
                surface.blit(plus, plus.get_rect(center=slot.center))


def _wrap_to_lines(text, font, max_w):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        if not current or font.size(test)[0] <= max_w:
            current.append(word)
            continue
        lines.append(" ".join(current))
        current = [word]
    if current:
        lines.append(" ".join(current))
    return lines
