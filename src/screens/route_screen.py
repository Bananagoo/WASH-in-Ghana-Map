import math
import pygame
from src.screens.base_screen import BaseScreen
from src.ui import Button, FontCache
from src.overworld_renderer import OverworldRenderer
from src.sprite import PlayerSprite
from src.path_mask import PathMask
from src.player_controller import PlayerController
from src.icon_renderer import draw_icon, get_icon_type
from src.animation import PulseEffect
from src import journal_panel
from src import config as C
from src.constants import SCREEN_TITLE, SCREEN_STOP, SCREEN_JOURNAL, SCREEN_MAP, SCREEN_WASH_MAP

HEADER_H = 54    # header bar height

_HEADER_COL  = (18, 48, 95)     # deep blue header (matches title screen theme)

# ── Stop marker visual constants (hitbox uses C.STOP_MARKER_RADIUS) ──────────
_MR       = C.STOP_MARKER_RADIUS        # draw radius (14)
_HIT_R    = C.STOP_MARKER_RADIUS + 10  # click hitbox radius (24)

# Stone marker colours
_STONE_WARM  = (165, 150, 128)
_STONE_SHADE = (130, 118, 100)
_STONE_HL    = (200, 188, 170)

# Info modal colours
_INFO_BG     = (20, 50, 95)
_INFO_BDR    = (95, 155, 215)


class RouteScreen(BaseScreen):

    def on_enter(self):
        state = self.game.state
        stops = self.game.stops
        w, h  = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        route_w = w - C.JOURNAL_WIDTH

        self._font_lg = FontCache.get(C.FONT_LG)
        self._font_md = FontCache.get(C.FONT_MD)
        self._font_sm = FontCache.get(C.FONT_SM)
        self._font_xs = FontCache.get(C.FONT_XS)

        # ── Overworld (built once; persists across visits) ─────────────────
        if not hasattr(self, "_overworld"):
            self._overworld = OverworldRenderer(route_w, h - HEADER_H)
            self._overworld.build(stops)

        # ── Path mask (built once from overworld curve) ────────────────────
        if not hasattr(self, "_path_mask"):
            self._path_mask = PathMask()
            self._path_mask.build(stops,
                                  self._overworld.curve_screen,
                                  self._overworld.seg_lengths)

        # ── Player sprite (persists across visits) ─────────────────────────
        if not hasattr(self, "_sprite"):
            self._sprite = PlayerSprite()
        self._sprite.load_image()

        # ── Player controller (persists; keeps position across visits) ─────
        if not hasattr(self, "_controller"):
            self._controller = PlayerController()
            first = stops[0]
            self._controller.place_at(float(first.route_position.x),
                                      float(first.route_position.y) + 30.0)

        # ── Pulse animation (current stop marker) ──────────────────────────
        if not hasattr(self, "_pulse"):
            self._pulse = PulseEffect(speed=2.8, amplitude=3.5)

        # ── Info modal state ───────────────────────────────────────────────
        self._show_info = False

        # ── Hover state ────────────────────────────────────────────────────
        self._hovered_stop = None

        # ── Buttons ────────────────────────────────────────────────────────
        btn_size = 30

        # "← Home" — top left of header
        self._home_btn = Button(
            pygame.Rect(C.PAD, (HEADER_H - 24) // 2, 80, 24),
            "← Home",
            self._font_xs,
            colour=(45, 78, 140),
            hover_colour=(65, 105, 175),
            text_colour=C.WHITE,
            border_radius=6,
        )

        # "i" info — top right of header, rightmost
        self._info_btn = Button(
            pygame.Rect(w - btn_size - C.PAD, (HEADER_H - btn_size) // 2,
                        btn_size, btn_size),
            "i",
            self._font_sm,
            colour=(95, 155, 215),
            hover_colour=C.GOLD_LIGHT,
            text_colour=C.DARK_GREY,
            border_radius=15,
        )

        # "Collect All" — bottom left, shortcut to unlock map
        self._autocollect_btn = Button(
            pygame.Rect(C.PAD, h - 50, 130, 28),
            "Collect All →",
            self._font_xs,
            colour=(55, 75, 110),
            hover_colour=(80, 105, 150),
            text_colour=C.GOLD_LIGHT,
            border_radius=6,
        )

        btn_y = h - 58
        self._journal_btn = Button(
            pygame.Rect(w - C.JOURNAL_WIDTH + 10, btn_y,
                        C.JOURNAL_WIDTH - 20, 34),
            "Field Journal",
            self._font_sm,
            colour=C.GOLD,
            hover_colour=C.RUST,
            text_colour=C.DARK_GREY,
        )
        self._map_btn = Button(
            pygame.Rect(w - C.JOURNAL_WIDTH + 10, btn_y - 44,
                        C.JOURNAL_WIDTH - 20, 34),
            "Systems Map →",
            self._font_sm,
        )
        self._map_btn.visible = state.all_stops_complete()

    def on_exit(self):
        pass

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        state = self.game.state
        stops = self.game.stops

        # Close info modal on any click or key press
        if self._show_info:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self._show_info = False
            return

        if self._home_btn.handle_event(event):
            self.game.audio.play("click")
            state.go_to(SCREEN_TITLE)
            return

        if self._info_btn.handle_event(event):
            self._show_info = True
            return

        if self._autocollect_btn.handle_event(event):
            state.complete_all_stops(stops)
            self._map_btn.visible = True
            return

        if self._journal_btn.handle_event(event):
            self.game.audio.play("click")
            state.go_to(SCREEN_JOURNAL)
            return

        if self._map_btn.visible and self._map_btn.handle_event(event):
            self.game.audio.play("transition")
            state.go_to(SCREEN_WASH_MAP)
            return

        if event.type == pygame.MOUSEMOTION:
            self._hovered_stop = None
            for stop in stops:
                sx, sy = self._stop_screen_pos(stop)
                if math.hypot(event.pos[0]-sx, event.pos[1]-sy) <= _HIT_R:
                    self._hovered_stop = stop
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            unlocked_id = state.current_unlocked_id()
            for stop in stops:
                sx, sy = self._stop_screen_pos(stop)
                if math.hypot(event.pos[0]-sx, event.pos[1]-sy) <= _HIT_R:
                    # Allow opening current stop OR any already-completed stop
                    if stop.id <= unlocked_id:
                        self.game.audio.play("open_stop")
                        self.game.open_stop(stop.id)
                        return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_j:
                state.go_to(SCREEN_JOURNAL)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        state = self.game.state
        stops = self.game.stops

        self._pulse.update(dt)
        self._sprite.update(dt)
        all_done = state.all_stops_complete()
        self._map_btn.visible          = all_done
        self._autocollect_btn.visible  = not all_done

        # Player free movement on the path mask
        keys = pygame.key.get_pressed()
        self._controller.update(dt, keys, self._path_mask,
                                state.current_unlocked_id())

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _stop_screen_pos(self, stop):
        return (stop.route_position.x, stop.route_position.y + 30)

    def draw(self, surface: pygame.Surface):
        state   = self.game.state
        stops   = self.game.stops
        w, h    = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        route_w = w - C.JOURNAL_WIDTH

        # ── Header ────────────────────────────────────────────────────────
        pygame.draw.rect(surface, _HEADER_COL, pygame.Rect(0, 0, w, HEADER_H))
        pygame.draw.rect(surface, C.GOLD,      pygame.Rect(0, HEADER_H-4, w, 4))
        self._home_btn.draw(surface)
        title_s = self._font_md.render("Mapping WASH — Field Route", True, C.WHITE)
        surface.blit(title_s, (C.PAD + 90, 14))
        # Progress counter sits just left of the "i" button
        btn_right = w - C.PAD                    # right edge of "i" button
        btn_left  = btn_right - 30               # left edge of "i" button (btn_size=30)
        prog_s = self._font_sm.render(
            f"{len(state.completed_stop_ids)} / {len(stops)}",
            True, C.GOLD_LIGHT,
        )
        surface.blit(prog_s, prog_s.get_rect(right=btn_left - 8, centery=HEADER_H // 2))
        self._info_btn.draw(surface)

        # ── Overworld background ──────────────────────────────────────────
        self._overworld.draw_background(surface, 0, HEADER_H)

        # ── Stop markers + icons ──────────────────────────────────────────
        unlocked_id = state.current_unlocked_id()
        for stop in stops:
            sx, sy = self._stop_screen_pos(stop)
            completed = state.is_stop_completed(stop.id)
            current   = (stop.id == unlocked_id
                         and not state.all_stops_complete())
            locked    = (stop.id > unlocked_id)
            hovered   = (self._hovered_stop is not None
                         and self._hovered_stop.id == stop.id)

            # ── Pulse glow ring (drawn first, behind icon and marker) ─────
            if current:
                pulse_r = int(_MR + 8 + self._pulse.offset)
                pygame.draw.circle(surface, C.GOLD_LIGHT, (sx, sy), pulse_r, 3)
                pygame.draw.circle(surface, C.GOLD, (sx, sy), pulse_r + 3, 1)

            # ── Wooden sign icon above marker ─────────────────────────────
            icon_y    = sy - _MR - 26
            icon_type = get_icon_type(stop.id, getattr(stop, "icon_type", ""))
            draw_icon(surface, sx, icon_y, icon_type, size=30, dimmed=locked)

            # ── Hover ring ────────────────────────────────────────────────
            if hovered and not locked:
                pygame.draw.circle(surface, C.WHITE, (sx, sy), _MR + 4)

            # ── Stone marker ──────────────────────────────────────────────
            pygame.draw.circle(surface, _STONE_WARM,  (sx, sy), _MR + 2)
            pygame.draw.circle(surface, _STONE_SHADE, (sx+1, sy+1), _MR + 2, 2)

            if current:
                interior = C.RUST
            elif completed:
                interior = C.TEAL
            elif locked:
                interior = (148, 138, 122)
            else:
                interior = C.GOLD

            pygame.draw.circle(surface, interior, (sx, sy), _MR)

            num_s = self._font_xs.render(str(stop.id), True, C.WHITE)
            surface.blit(num_s, num_s.get_rect(center=(sx, sy)))

        # ── Player sprite ─────────────────────────────────────────────────
        px, py = self._controller.position
        self._sprite.draw(
            surface, int(px), int(py),
            direction  = self._controller.direction,
            moving     = self._controller.is_moving,
            walk_frame = self._controller.walk_frame,
            bob_offset = self._controller.bob_offset,
        )

        # ── Journal panel ─────────────────────────────────────────────────
        panel_rect = pygame.Rect(route_w, HEADER_H,
                                 C.JOURNAL_WIDTH, h - HEADER_H)
        pygame.draw.line(surface, (180, 162, 128),
                         (route_w, HEADER_H), (route_w, h), 2)
        journal_panel.draw(surface, panel_rect, stops, state,
                           self._font_sm, self._font_xs)
        self._journal_btn.draw(surface)
        if self._map_btn.visible:
            self._map_btn.draw(surface)

        # ── Tooltip ───────────────────────────────────────────────────────
        if self._hovered_stop:
            self._draw_tooltip(surface, self._hovered_stop, state, unlocked_id)

        # ── Autocollect button ────────────────────────────────────────────
        self._autocollect_btn.draw(surface)

        # ── Info modal ────────────────────────────────────────────────────
        if self._show_info:
            self._draw_info_modal(surface)

    # ── Info modal ────────────────────────────────────────────────────────────

    def _draw_info_modal(self, surface: pygame.Surface):
        from src.ui import draw_panel, draw_wrapped_text
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        # Semi-opaque dark overlay (convert() ensures set_alpha works on all platforms)
        dim = pygame.Surface((w, h)).convert()
        dim.fill((8, 18, 38))
        dim.set_alpha(200)
        surface.blit(dim, (0, 0))

        pw, ph = 520, 320
        px = w // 2 - pw // 2
        py = h // 2 - ph // 2
        draw_panel(surface, pygame.Rect(px, py, pw, ph),
                   _INFO_BG, _INFO_BDR, radius=12)

        ty = py + C.PAD_LG
        title_s = self._font_md.render("About this Game", True, C.GOLD)
        surface.blit(title_s, title_s.get_rect(centerx=w // 2, top=ty))
        ty += title_s.get_height() + 6
        pygame.draw.line(surface, _INFO_BDR,
                         (px + C.PAD_LG, ty), (px + pw - C.PAD_LG, ty), 1)
        ty += 10

        lines = [
            "Mapping WASH: A Systems Journey Through Ghana",
            "Navigate the field route and click on stop markers to",
            "explore WASH (Water, Sanitation & Hygiene) sites.",
            "",
            "Controls:",
            "  WASD / Arrow keys  —  move character",
            "  Click stop marker  —  open field note",
            "  J  —  open field journal",
            "  M  —  mute / unmute music",
            "  F11  —  toggle fullscreen",
            "",
            "Click anywhere or press any key to close.",
        ]
        for line in lines:
            col = C.GOLD_LIGHT if line.startswith("Controls") else C.OFF_WHITE
            s = self._font_xs.render(line, True, col)
            surface.blit(s, (px + C.PAD_LG, ty))
            ty += self._font_xs.get_height() + 3

    # ── Tooltip ───────────────────────────────────────────────────────────────

    def _draw_tooltip(self, surface, stop, state, unlocked_id):
        lines = [f"Stop {stop.id}: {stop.title[:44]}"]
        if stop.token:
            lines.append(f"Token: {stop.token}")
        if state.is_stop_completed(stop.id):
            lines.append("Click to re-read →")
        elif stop.id == unlocked_id:
            lines.append("Click to open →")
        else:
            lines.append("Locked — visit in order")

        font = self._font_xs
        pad  = 8
        width  = max(font.size(l)[0] for l in lines) + pad * 2
        height = len(lines) * (font.get_height() + 2) + pad * 2

        mx, my = pygame.mouse.get_pos()
        tx = min(mx + 16, C.SCREEN_WIDTH - C.JOURNAL_WIDTH - width - 4)
        ty = max(my - height - 8, HEADER_H + 4)

        pygame.draw.rect(surface, (35, 28, 20),
                         pygame.Rect(tx-2, ty-2, width+4, height+4),
                         border_radius=6)
        pygame.draw.rect(surface, C.GOLD,
                         pygame.Rect(tx-2, ty-2, width+4, height+4),
                         1, border_radius=6)

        iy = ty + pad
        for line in lines:
            s = font.render(line, True, C.WHITE)
            surface.blit(s, (tx + pad, iy))
            iy += font.get_height() + 2
