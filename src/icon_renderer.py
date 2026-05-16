"""
Procedural stop icons for the overworld route screen.

All drawing goes directly onto the destination surface — no SRCALPHA
intermediate surfaces, which have unreliable compositing in pygame 2.0.x.
Icon content is clipped to the sign board with surface.set_clip().
"""
import math
import pygame


# Maps stop id → icon_type string used by DRAWERS below
_DEFAULT_ICONS = {
    1:  "school",
    2:  "water_drop",
    3:  "truck",
    4:  "monument",
    5:  "clinic",
    6:  "stream",
    7:  "toilet",
    8:  "chart",
    9:  "valve",
    10: "soap",
    11: "castle",
    12: "jug",
    13: "forest_tree",
    14: "canopy",
    15: "camera",
    16: "farm",
}

_WD_SIGN  = (185, 145, 82)   # wooden sign board (warm)
_WD_RIM   = (138, 100, 50)   # sign rim / post
_WD_DIM   = (145, 115, 72)   # dimmed board
_WD_DIM_R = (108,  80, 42)   # dimmed rim


def get_icon_type(stop_id: int, override: str = "") -> str:
    if override:
        return override
    return _DEFAULT_ICONS.get(stop_id, "default")


def draw_icon(surface: pygame.Surface, cx: int, cy: int,
              icon_type: str, size: int = 34, dimmed: bool = False):
    """
    Draw a small wooden-sign icon centred at (cx, cy).

    Draws directly onto surface — no SRCALPHA intermediate — to avoid
    black-box transparency artefacts on pygame 2.0.x.
    Icon content is clipped to the sign board using surface.set_clip().
    """
    sw = size + 2    # board width
    sh = size - 4    # board height

    board_col = _WD_DIM   if dimmed else _WD_SIGN
    rim_col   = _WD_DIM_R if dimmed else _WD_RIM

    # Post stub below board (drawn first so board sits on top)
    pygame.draw.rect(surface, rim_col,
                     pygame.Rect(cx - 1, cy + sh // 2, 3, 8))

    # Sign board background
    board_rect = pygame.Rect(cx - sw // 2, cy - sh // 2, sw, sh)
    pygame.draw.rect(surface, board_col, board_rect, border_radius=3)

    # Wood-grain highlight across the top of the board
    pygame.draw.line(surface,
                     tuple(min(255, c + 20) for c in board_col),
                     (cx - sw // 2 + 2, cy - sh // 2 + 2),
                     (cx + sw // 2 - 2, cy - sh // 2 + 2), 1)

    # Icon graphic — clipped so it can't bleed outside the board
    old_clip = surface.get_clip()
    surface.set_clip(board_rect)
    drawer = _DRAWERS.get(icon_type, _default)
    drawer(surface, cx, cy, sh // 2 - 2)
    surface.set_clip(old_clip)

    # Rim outline drawn after icon so it's always visible on top
    pygame.draw.rect(surface, rim_col, board_rect, 1, border_radius=3)

    # Dim overlay for locked stops.
    # Uses surface-wide alpha (NOT SRCALPHA per-pixel) — reliable on all versions.
    if dimmed:
        dim = pygame.Surface((sw, sh)).convert()
        dim.fill((55, 45, 30))
        dim.set_alpha(105)
        surface.blit(dim, board_rect.topleft)


# ------------------------------------------------------------------
# Individual icon draw functions.
# Each receives: surf, cx, cy, r  (r = usable inner radius)
# They now draw directly onto surf (main screen or clipped region).
# ------------------------------------------------------------------

def _school(s, cx, cy, r):
    bw, bh = int(r * 1.45), int(r * 1.0)
    pygame.draw.rect(s, (242, 222, 185),
                     pygame.Rect(cx - bw // 2, cy - bh // 4, bw, bh), border_radius=1)
    pygame.draw.polygon(s, (210, 88, 65),
                        [(cx - bw // 2 - 1, cy - bh // 4),
                         (cx + bw // 2 + 1, cy - bh // 4),
                         (cx, cy - r + 1)])
    pygame.draw.rect(s, (118, 88, 52),
                     pygame.Rect(cx - 2, cy + bh // 4 - 4, 5, bh // 2 + 2))
    wc = (155, 205, 228)
    pygame.draw.rect(s, wc, pygame.Rect(cx - bw // 2 + 3, cy - bh // 4 + 3, 4, 4))
    pygame.draw.rect(s, wc, pygame.Rect(cx + bw // 2 - 7, cy - bh // 4 + 3, 4, 4))


def _water_drop(s, cx, cy, r):
    cr = int(r * 0.65)
    pygame.draw.circle(s, (95, 175, 235), (cx, cy + r // 4), cr)
    pygame.draw.polygon(s, (95, 175, 235),
                        [(cx - r // 2, cy + r // 4 - cr + 2),
                         (cx + r // 2, cy + r // 4 - cr + 2),
                         (cx, cy - r + 2)])
    pygame.draw.circle(s, (185, 222, 248), (cx - r // 5, cy - r // 6), max(2, r // 5))


def _truck(s, cx, cy, r):
    bw, bh = int(r * 1.05), int(r * 1.6)
    pygame.draw.rect(s, (205, 205, 215),
                     pygame.Rect(cx - bw // 2, cy - bh // 2, bw, bh), border_radius=2)
    pygame.draw.rect(s, (165, 170, 182),
                     pygame.Rect(cx - bw // 2 + 1, cy - bh // 2 + 1, bw - 2, bh // 3))
    pygame.draw.rect(s, (148, 198, 225),
                     pygame.Rect(cx - bw // 2 + 3, cy - bh // 2 + 3, bw - 6, bh // 5))
    wh = 3
    wc = (65, 65, 78)
    for wx in [cx - bw // 2 - wh, cx + bw // 2 - wh]:
        for wy in [cy - bh // 3, cy + bh // 3 - wh * 2]:
            pygame.draw.rect(s, wc, pygame.Rect(wx, wy, wh * 2, wh * 2))


def _monument(s, cx, cy, r):
    pw, ph = max(4, r // 3), int(r * 1.75)
    pygame.draw.rect(s, (202, 182, 138),
                     pygame.Rect(cx - pw - 2, cy + ph // 2 - 4, pw * 2 + 4, 5))
    pygame.draw.rect(s, (222, 202, 158),
                     pygame.Rect(cx - pw // 2, cy - ph // 2, pw, ph))
    pygame.draw.polygon(s, (235, 215, 170),
                        [(cx - pw // 2, cy - ph // 2),
                         (cx + pw // 2, cy - ph // 2),
                         (cx, cy - r + 1)])
    pygame.draw.line(s, (172, 152, 110),
                     (cx + pw // 2, cy - ph // 2 + 2),
                     (cx + pw // 2, cy + ph // 2 - 4), 1)


def _clinic(s, cx, cy, r):
    bw = int(r * 1.7)
    pygame.draw.rect(s, (245, 248, 245),
                     pygame.Rect(cx - bw // 2, cy - bw // 2, bw, bw), border_radius=2)
    pygame.draw.rect(s, (215, 48, 52),
                     pygame.Rect(cx - bw // 2 + 3, cy - 3, bw - 6, 6))
    pygame.draw.rect(s, (215, 48, 52),
                     pygame.Rect(cx - 3, cy - bw // 2 + 3, 6, bw - 6))
    pygame.draw.rect(s, (178, 40, 44),
                     pygame.Rect(cx - bw // 2, cy - bw // 2, bw, bw), width=1, border_radius=2)


def _stream(s, cx, cy, r):
    col = (105, 182, 235)
    for yo in (-r // 2 + 1, 0, r // 2 - 1):
        y = cy + yo
        for x in range(cx - r + 1, cx + r - 4, 5):
            pts = [(x, y), (x + 2, y - 3), (x + 4, y), (x + 6, y + 3)]
            if pts[-1][0] <= cx + r:
                pygame.draw.lines(s, col, False, pts, 2)


def _toilet(s, cx, cy, r):
    tw, th = int(r * 1.2), int(r * 0.7)
    tc = (232, 236, 238)
    pygame.draw.rect(s, tc, pygame.Rect(cx - tw // 2, cy - r + 2, tw, th), border_radius=2)
    pygame.draw.rect(s, (198, 204, 207),
                     pygame.Rect(cx - tw // 2, cy - r + 2, tw, th), width=1, border_radius=2)
    bw = int(r * 1.55)
    pygame.draw.ellipse(s, tc,
                        pygame.Rect(cx - bw // 2, cy - r // 5, bw, int(r * 1.1)))
    pygame.draw.ellipse(s, (198, 204, 207),
                        pygame.Rect(cx - bw // 2, cy - r // 5, bw, int(r * 1.1)), width=1)


def _chart(s, cx, cy, r):
    bw = max(3, r // 3)
    heights = [int(r * 1.05), int(r * 1.55), int(r * 1.82)]
    x0 = cx - r + 2
    col = (198, 178, 242)
    edge = (152, 132, 198)
    for i, h in enumerate(heights):
        br = pygame.Rect(x0 + i * (bw + 3), cy + r - 2 - h, bw, h)
        pygame.draw.rect(s, col, br, border_radius=1)
        pygame.draw.rect(s, edge, br, width=1, border_radius=1)
    pygame.draw.line(s, edge, (cx - r + 2, cy - r + 2), (cx - r + 2, cy + r - 2), 1)
    pygame.draw.line(s, edge, (cx - r + 2, cy + r - 2), (cx + r - 2, cy + r - 2), 1)


def _valve(s, cx, cy, r):
    pygame.draw.circle(s, (182, 192, 205), (cx, cy), r)
    pygame.draw.circle(s, (150, 162, 178), (cx, cy), r, width=2)
    for ang in (0, 90, 180, 270):
        rad = math.radians(ang)
        x2 = cx + int(r * 0.72 * math.cos(rad))
        y2 = cy + int(r * 0.72 * math.sin(rad))
        pygame.draw.line(s, (125, 140, 155), (cx, cy), (x2, y2), 2)
    pygame.draw.circle(s, (98, 115, 132), (cx, cy), max(3, r // 3))


def _soap(s, cx, cy, r):
    bw, bh = int(r * 1.55), int(r * 0.9)
    pygame.draw.rect(s, (228, 244, 252),
                     pygame.Rect(cx - bw // 2, cy + 2, bw, bh), border_radius=4)
    pygame.draw.rect(s, (192, 215, 228),
                     pygame.Rect(cx - bw // 2, cy + 2, bw, bh), width=1, border_radius=4)
    pygame.draw.rect(s, (178, 208, 222),
                     pygame.Rect(cx - bw // 2 + 4, cy + 6, bw - 8, 3))
    for bx, by, br in [(cx - r // 2, cy - r // 2, 4),
                        (cx + r // 3, cy - r // 3, 3),
                        (cx,          cy - r + 2,  5)]:
        pygame.draw.circle(s, (208, 242, 252), (bx, by), br)
        pygame.draw.circle(s, (182, 222, 242), (bx, by), br, width=1)


def _castle(s, cx, cy, r):
    bw, bh = int(r * 1.85), int(r * 1.4)
    pygame.draw.rect(s, (192, 170, 132),
                     pygame.Rect(cx - bw // 2, cy - bh // 2 + 5, bw, bh - 5))
    nw = max(3, bw // 6)
    for i in range(4):
        nx = cx - bw // 2 + i * (bw // 3)
        pygame.draw.rect(s, (192, 170, 132),
                         pygame.Rect(nx, cy - bh // 2, nw + 2, 9))
    pygame.draw.rect(s, (98, 78, 56),
                     pygame.Rect(cx - 4, cy, 8, bh // 2 + 3))
    pygame.draw.ellipse(s, (98, 78, 56),
                        pygame.Rect(cx - 4, cy - 4, 8, 8))


def _jug(s, cx, cy, r):
    body = [(cx - r // 2, cy - r + 4),
            (cx + r // 2, cy - r + 4),
            (cx + int(r * 0.72), cy + int(r * 0.48)),
            (cx + int(r * 0.42), cy + r - 2),
            (cx - int(r * 0.42), cy + r - 2),
            (cx - int(r * 0.72), cy + int(r * 0.48))]
    pygame.draw.polygon(s, (238, 175, 212), body)
    pygame.draw.polygon(s, (198, 138, 175), body, width=1)
    pygame.draw.lines(s, (198, 138, 175), False,
                      [(cx + r // 2, cy - r // 4),
                       (cx + r - 1,  cy - r // 4),
                       (cx + r - 1,  cy + r // 3),
                       (cx + r // 2, cy + r // 3)], 2)
    pygame.draw.ellipse(s, (115, 178, 222),
                        pygame.Rect(cx - r // 2 + 2, cy - r + 5, r - 4, r // 4))


def _forest_tree(s, cx, cy, r):
    cols = [(58, 108, 42), (72, 128, 52), (88, 148, 62)]
    for i, (dx, dy, cr) in enumerate([(-r // 3, r // 4, int(r * 0.62)),
                                       (r // 3,  r // 4, int(r * 0.62)),
                                       (0, -r // 5, int(r * 0.72))]):
        pygame.draw.circle(s, cols[i % 3], (cx + dx, cy + dy), cr)
    pygame.draw.circle(s, (92, 155, 68), (cx, cy - r // 5), int(r * 0.48))


def _canopy(s, cx, cy, r):
    cols = [(48, 95, 35), (62, 115, 46), (76, 138, 56)]
    cluster = [(-r // 3, r // 4, r // 2), (r // 3, r // 4, r // 2),
               (0, -r // 4, int(r * 0.6)), (-r // 4, 0, int(r * 0.52))]
    for i, (dx, dy, cr) in enumerate(cluster):
        pygame.draw.circle(s, cols[i % 3], (cx + dx, cy + dy), cr)
    pygame.draw.line(s, (138, 98, 58), (cx - r + 2, cy), (cx + r - 2, cy), 2)


def _camera(s, cx, cy, r):
    bw, bh = int(r * 1.72), int(r * 1.25)
    pygame.draw.rect(s, (52, 52, 65),
                     pygame.Rect(cx - bw // 2, cy - bh // 2, bw, bh), border_radius=3)
    pygame.draw.circle(s, (78, 82, 98), (cx, cy + 2), r // 2 + 1)
    pygame.draw.circle(s, (155, 192, 220), (cx, cy + 2), r // 2 - 2)
    pygame.draw.circle(s, (188, 218, 238), (cx - 2, cy), r // 4)
    pygame.draw.rect(s, (62, 62, 78),
                     pygame.Rect(cx - bw // 4, cy - bh // 2 - 3, bw // 2, 4), border_radius=1)
    pygame.draw.rect(s, (238, 235, 198),
                     pygame.Rect(cx + bw // 4, cy - bh // 2 + 2, bw // 5, bh // 4), border_radius=1)


def _farm(s, cx, cy, r):
    pygame.draw.ellipse(s, (138, 88, 32),
                        pygame.Rect(cx - r // 2, cy - int(r * 0.88), r, int(r * 1.72)))
    for offset in (-r // 4, 0, r // 4):
        pygame.draw.line(s, (112, 70, 26),
                         (cx + offset, cy - int(r * 0.82)),
                         (cx + offset, cy + int(r * 0.78)), 1)
    pygame.draw.ellipse(s, (165, 112, 55),
                        pygame.Rect(cx - r // 2 + 3, cy - int(r * 0.72),
                                    r // 3, int(r * 0.78)))
    pygame.draw.line(s, (78, 108, 42),
                     (cx, cy - int(r * 0.88)), (cx + r // 3, cy - r + 1), 2)


def _default(s, cx, cy, r):
    pygame.draw.circle(s, (198, 198, 210), (cx, cy), r - 1)
    pygame.draw.line(s, (148, 148, 165), (cx, cy - r // 2), (cx, cy + r // 2), 2)
    pygame.draw.line(s, (148, 148, 165), (cx - r // 2, cy), (cx + r // 2, cy), 2)


_DRAWERS = {
    "school":      _school,
    "water_drop":  _water_drop,
    "truck":       _truck,
    "monument":    _monument,
    "clinic":      _clinic,
    "stream":      _stream,
    "toilet":      _toilet,
    "chart":       _chart,
    "valve":       _valve,
    "soap":        _soap,
    "castle":      _castle,
    "jug":         _jug,
    "forest_tree": _forest_tree,
    "canopy":      _canopy,
    "camera":      _camera,
    "farm":        _farm,
}
