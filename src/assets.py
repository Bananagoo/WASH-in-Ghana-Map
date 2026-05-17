"""
Asset loader with graceful fallbacks.
Every function returns a valid Surface even when files are missing.
"""
import math
import os
import pygame
from typing import Optional, Tuple

_cache: dict = {}

# Theme name → (R, G, B) for placeholder stop images
THEME_COLOURS = {
    "water":          (60,  130, 200),
    "health":         (200,  70,  70),
    "infrastructure": (100, 110, 130),
    "knowledge":      (47,  140, 130),
    "culture":        (195, 145,  50),
    "governance":     (130,  80, 185),
    "gender":         (200,  95, 155),
    "climate":        (55,  160,  85),
    "nature":         (60,  145,  75),
    "history":        (110,  85,  60),
    "livelihoods":    (165, 120,  55),
    "default":        (100, 105, 120),
}


# ------------------------------------------------------------------
# Image loading
# ------------------------------------------------------------------

def load_image(path: str, size: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
    """Load an image, scaling to exact size (may distort aspect ratio)."""
    key = (path, size)
    if key in _cache:
        return _cache[key]
    if not path or not os.path.exists(path):
        _cache[key] = None
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        _cache[key] = img
        return img
    except Exception:
        _cache[key] = None
        return None


def load_image_fit(path: str, max_w: int, max_h: int) -> Optional[pygame.Surface]:
    """Load image preserving aspect ratio, fitting within max_w × max_h."""
    key = ("fit", path, max_w, max_h)
    if key in _cache:
        return _cache[key]
    if not path or not os.path.exists(path):
        _cache[key] = None
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        iw, ih = img.get_size()
        scale = min(max_w / iw, max_h / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        img = pygame.transform.smoothscale(img, (nw, nh))
        _cache[key] = img
        return img
    except Exception:
        _cache[key] = None
        return None


def load_image_cover(path: str, width: int, height: int) -> Optional[pygame.Surface]:
    """Load image preserving aspect ratio, cropping to fill width × height."""
    key = ("cover", path, width, height)
    if key in _cache:
        return _cache[key]
    if not path or not os.path.exists(path):
        _cache[key] = None
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        iw, ih = img.get_size()
        scale = max(width / iw, height / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        img = pygame.transform.smoothscale(img, (nw, nh))
        crop = pygame.Rect((nw - width) // 2, (nh - height) // 2, width, height)
        img = img.subsurface(crop).copy()
        _cache[key] = img
        return img
    except Exception:
        _cache[key] = None
        return None


def clear_cache():
    _cache.clear()


# ------------------------------------------------------------------
# Placeholder surfaces (used when real assets are absent)
# ------------------------------------------------------------------

def stop_placeholder(w: int, h: int, icon_label: str, visual_theme: str,
                     font: pygame.font.Font) -> pygame.Surface:
    colour = THEME_COLOURS.get(visual_theme, THEME_COLOURS["default"])
    dark   = tuple(max(0, c - 40) for c in colour)
    light  = tuple(min(255, c + 60) for c in colour)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, colour, (0, 0, w, h), border_radius=8)
    pygame.draw.rect(surf, dark,   (0, h // 2, w, h // 2), border_radius=8)
    for i in range(-h, w, 24):
        pygame.draw.line(surf, light, (i, 0), (i + h, h), 1)
    big_font = pygame.font.SysFont("Arial, Helvetica", max(w // 6, 14))
    label_surf = big_font.render(icon_label, True, (255, 255, 255))
    label_surf.set_alpha(220)
    surf.blit(label_surf, label_surf.get_rect(center=(w // 2, h // 2)))
    pygame.draw.rect(surf, (255, 255, 255, 80), (0, 0, w, h), width=2, border_radius=8)
    return surf


# ------------------------------------------------------------------
# Token icon drawing functions — white icons on coloured badge circle
# ------------------------------------------------------------------

def _dk(c, amt=45):
    return (max(0, c[0]-amt), max(0, c[1]-amt), max(0, c[2]-amt))

def _lt(c, amt=50):
    return (min(255, c[0]+amt), min(255, c[1]+amt), min(255, c[2]+amt))


def _i_field_passport(surf, cx, cy, r):
    w, h = max(8, r), max(10, int(r * 1.3))
    pygame.draw.rect(surf, (240, 240, 255), (cx - w//2, cy - h//2, w, h), border_radius=2)
    pygame.draw.rect(surf, (160, 160, 200), (cx - w//2, cy - h//2, 2, h))
    for i in range(3):
        y = cy - h//4 + i * (h // 4 + 1)
        pygame.draw.line(surf, (160, 160, 180), (cx - w//2 + 4, y), (cx + w//2 - 3, y), 1)


def _i_test_strip(surf, cx, cy, r):
    w, h = max(5, r // 2), max(10, int(r * 1.55))
    pygame.draw.rect(surf, (235, 230, 210), (cx - w//2, cy - h//2, w, h), border_radius=2)
    band = h // 3
    pygame.draw.rect(surf, (60, 220, 200), (cx - w//2, cy + h//2 - band, w, band), border_radius=2)
    pygame.draw.rect(surf, (120, 230, 210), (cx - w//2, cy + h//2 - band*2 + 2, w, band//2))


def _i_sludge_truck(surf, cx, cy, r):
    tw, th = max(8, int(r * 1.65)), max(5, int(r * 0.65))
    x0, y0 = cx - tw//2, cy - th//2 - 1
    # cab on LEFT (front facing right)
    pygame.draw.rect(surf, (225, 228, 235), (x0, y0 - 3, int(tw * 0.35), th + 3), border_radius=3)
    cw = int(tw * 0.35) - 4
    pygame.draw.rect(surf, (140, 170, 210), (x0 + 2, y0 - 1, cw, th // 2 - 1), border_radius=1)
    # cargo body on RIGHT (back)
    pygame.draw.rect(surf, (200, 205, 215), (x0 + int(tw * 0.35), y0, int(tw * 0.65), th), border_radius=2)
    # wheels
    wr = max(2, r // 5)
    wy = y0 + th + wr - 1
    for wx in [x0 + int(tw * 0.18), x0 + int(tw * 0.75)]:
        pygame.draw.circle(surf, (55, 55, 55), (wx, wy), wr)
        pygame.draw.circle(surf, (100, 100, 100), (wx, wy), max(1, wr - 2))


def _i_black_star(surf, cx, cy, r):
    pts = []
    for i in range(5):
        a = math.radians(-90 + i * 72)
        pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
        a2 = math.radians(-90 + i * 72 + 36)
        pts.append((cx + int(r * 0.42 * math.cos(a2)), cy + int(r * 0.42 * math.sin(a2))))
    pygame.draw.polygon(surf, (25, 20, 15), pts)


def _i_first_aid_cross(surf, cx, cy, r):
    arm = max(3, r // 3)
    pygame.draw.rect(surf, (255, 255, 255), (cx - arm, cy - r + 1, arm * 2, (r - 1) * 2), border_radius=1)
    pygame.draw.rect(surf, (255, 255, 255), (cx - r + 1, cy - arm, (r - 1) * 2, arm * 2), border_radius=1)


def _i_stream_stone(surf, cx, cy, r):
    pygame.draw.ellipse(surf, (210, 215, 205), (cx - r, cy - int(r * 0.65), r * 2, int(r * 1.3)))
    pts = []
    for x in range(cx - r + 3, cx + r - 2, 2):
        y = cy + int(3 * math.sin((x - cx) * 0.45))
        pts.append((x, y))
    if len(pts) >= 2:
        pygame.draw.lines(surf, (120, 140, 125), False, pts, 1)


def _i_toilet(surf, cx, cy, r):
    tw, th = max(7, int(r * 1.05)), max(5, int(r * 0.48))
    # tank
    pygame.draw.rect(surf, (230, 232, 238), (cx - tw//2, cy - r + 1, tw, th), border_radius=3)
    # bowl
    bw, bh = max(8, int(r * 1.15)), max(6, int(r * 0.7))
    pygame.draw.ellipse(surf, (238, 240, 245), (cx - bw//2, cy - r + th + 1, bw, bh))
    # seat ring
    pygame.draw.ellipse(surf, (200, 205, 210), (cx - bw//2, cy - r + th + 1, bw, bh), 2)


def _i_histogram(surf, cx, cy, r):
    heights = [int(r * 0.55), int(r * 0.95), int(r * 0.7)]
    bw = max(3, (r * 2 - 4) // len(heights) - 2)
    total_w = len(heights) * bw + (len(heights) - 1) * 2
    x = cx - total_w // 2
    base_y = cy + r // 2
    for h in heights:
        pygame.draw.rect(surf, (255, 255, 255), (x, base_y - h, bw, h), border_radius=1)
        x += bw + 2


def _i_pipe_valve(surf, cx, cy, r):
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r - 1, 2)
    pygame.draw.line(surf, (255, 255, 255), (cx - r + 1, cy), (cx + r - 1, cy), 2)
    pygame.draw.line(surf, (255, 255, 255), (cx, cy - r + 1), (cx, cy + r - 1), 2)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(2, r // 3))


def _i_bar_of_soap(surf, cx, cy, r):
    w, h = max(9, int(r * 1.35)), max(7, int(r * 0.82))
    pygame.draw.rect(surf, (250, 248, 228), (cx - w//2, cy - h//2, w, h), border_radius=4)
    pygame.draw.rect(surf, (210, 205, 185), (cx - w//2, cy - h//2, w, h), 1, border_radius=4)
    for bx, by, br in [(cx - 3, cy - 3, 2), (cx + 4, cy - 2, 2), (cx, cy + 3, 1)]:
        pygame.draw.circle(surf, (210, 208, 190), (bx, by), br, 1)


def _i_shell(surf, cx, cy, r):
    # Scallop/fan shell: hinge at bottom, ribs fan upward
    base_x, base_y = cx, cy + r // 3
    arc_r = int(r * 1.05)
    span_start, span_end = -158, -22  # degrees, sweeping over the top
    n_pts = 14
    shell_col = (255, 240, 195)
    rib_col   = (190, 158, 105)
    pts = [(base_x, base_y)]
    for i in range(n_pts + 1):
        a = math.radians(span_start + i * (span_end - span_start) / n_pts)
        pts.append((base_x + int(arc_r * math.cos(a)), base_y + int(arc_r * math.sin(a))))
    pygame.draw.polygon(surf, shell_col, pts)
    n_ribs = 6
    for i in range(n_ribs + 1):
        a = math.radians(span_start + i * (span_end - span_start) / n_ribs)
        px = base_x + int(arc_r * math.cos(a))
        py = base_y + int(arc_r * math.sin(a))
        pygame.draw.line(surf, rib_col, (base_x, base_y), (px, py), 1)
    pygame.draw.circle(surf, rib_col, (base_x, base_y), max(2, r // 6))


def _i_fish(surf, cx, cy, r):
    bw, bh = max(8, int(r * 1.05)), max(5, int(r * 0.62))
    # body
    pygame.draw.ellipse(surf, (190, 240, 225), (cx - bw//2 + 4, cy - bh//2, bw, bh))
    # tail (triangle pointing left)
    pts = [
        (cx - bw//2 + 3, cy),
        (cx - bw//2 - r//3, cy - r//3),
        (cx - bw//2 - r//3, cy + r//3),
    ]
    pygame.draw.polygon(surf, (190, 240, 225), pts)
    # eye
    pygame.draw.circle(surf, (50, 50, 50), (cx + bw//3, cy - 1), max(1, r // 6))


def _i_bamboo(surf, cx, cy, r):
    stalk_w = max(3, r // 3)
    for dx in [-r // 3, r // 3]:
        x = cx + dx
        pygame.draw.rect(surf, (175, 225, 155), (x - stalk_w//2, cy - r + 1, stalk_w, (r - 1) * 2), border_radius=1)
        for jy in [cy - r // 2, cy, cy + r // 2]:
            pygame.draw.line(surf, (120, 170, 105), (x - stalk_w//2 - 1, jy), (x + stalk_w//2 + 1, jy), 2)


def _i_canopy_leaf(surf, cx, cy, r):
    pts = [(cx, cy - r + 1), (cx + r - 2, cy), (cx, cy + r - 1), (cx - r + 2, cy)]
    pygame.draw.polygon(surf, (175, 230, 155), pts)
    pygame.draw.line(surf, (105, 175, 90), (cx, cy - r + 2), (cx, cy + r - 2), 1)
    # side veins
    for sign in [-1, 1]:
        mid_x = cx + sign * (r // 2)
        pygame.draw.line(surf, (130, 190, 110), (cx, cy), (mid_x, cy - r // 3), 1)


def _i_camera(surf, cx, cy, r):
    bw, bh = max(10, int(r * 1.5)), max(7, int(r * 1.05))
    # body
    pygame.draw.rect(surf, (215, 215, 218), (cx - bw//2, cy - bh//2 + 2, bw, bh), border_radius=3)
    # viewfinder bump
    bump_w = bw // 3
    pygame.draw.rect(surf, (195, 195, 198), (cx - bump_w//2, cy - bh//2 - 1, bump_w, 4), border_radius=2)
    # lens
    lr = max(3, r // 2)
    pygame.draw.circle(surf, (55, 75, 120), (cx, cy + 2), lr)
    pygame.draw.circle(surf, (95, 125, 175), (cx, cy + 2), max(1, lr - 2))
    pygame.draw.circle(surf, (200, 220, 255), (cx - lr//3, cy + 2 - lr//3), max(1, lr//4))


def _i_cocoa_pod(surf, cx, cy, r):
    pw, ph = max(7, int(r * 0.85)), max(10, int(r * 1.42))
    pygame.draw.ellipse(surf, (205, 165, 85), (cx - pw//2, cy - ph//2, pw, ph))
    for dx in [-pw//4, 0, pw//4]:
        pygame.draw.line(surf, (160, 120, 52), (cx + dx, cy - ph//2 + 3), (cx + dx, cy + ph//2 - 3), 1)


_ICON_FNS = {
    "Field Passport":  _i_field_passport,
    "Test Strip":      _i_test_strip,
    "Sludge Truck":    _i_sludge_truck,
    "Black Star Coin": _i_black_star,
    "First Aid Cross": _i_first_aid_cross,
    "Stream Stone":    _i_stream_stone,
    "Toilet":          _i_toilet,
    "Histogram":       _i_histogram,
    "Pipe Valve":      _i_pipe_valve,
    "Bar of Soap":     _i_bar_of_soap,
    "Shell":           _i_shell,
    "Fish":            _i_fish,
    "Bamboo":          _i_bamboo,
    "Canopy Leaf":     _i_canopy_leaf,
    "Camera":          _i_camera,
    "Cocoa Pod":       _i_cocoa_pod,
}

_TOKEN_STYLES: dict = {
    "Field Passport":  ((60,  100, 180), "PP"),
    "Test Strip":      ((47,  140, 130), "TS"),
    "Sludge Truck":    ((100, 110, 130), "ST"),
    "Black Star Coin": ((200, 165,  50), "★"),
    "First Aid Cross": ((200,  70,  70), "✚"),
    "Stream Stone":    ((120, 160, 140), "SS"),
    "Toilet":          ((80,  130, 200), "TO"),
    "Histogram":       ((80,  160, 200), "HG"),
    "Pipe Valve":      ((130,  80, 185), "PV"),
    "Bar of Soap":     ((47,  140, 130), "SP"),
    "Shell":           ((195, 145,  50), "SH"),
    "Fish":            ((60,  170, 120), "FS"),
    "Bamboo":          ((60,  150,  80), "BM"),
    "Canopy Leaf":     ((55,  160,  85), "CL"),
    "Camera":          ((80,  160, 200), "CA"),
    "Cocoa Pod":       ((165, 120,  55), "CP"),
}


def token_badge(token_name: str, size: int = 40,
                bg_colour: Tuple[int, int, int] = (200, 160, 50)) -> pygame.Surface:
    """Circular badge with a drawn icon — used as a collectible token icon."""
    style  = _TOKEN_STYLES.get(token_name)
    colour = style[0] if style else bg_colour

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy, r = size // 2, size // 2, size // 2 - 1

    # Outer glow ring + fill
    light = tuple(min(255, c + 50) for c in colour)
    pygame.draw.circle(surf, light,   (cx, cy), r)
    pygame.draw.circle(surf, colour,  (cx, cy), r - 3)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r, width=2)

    # Drawn icon
    icon_fn = _ICON_FNS.get(token_name)
    ir = max(4, r - 6)
    if icon_fn:
        icon_fn(surf, cx, cy, ir)
    else:
        label = style[1] if style else (token_name[:2].upper() if token_name else "?")
        font_size = max(size // 4, 7) if len(label) > 2 else max(size // 3, 8)
        font = pygame.font.SysFont("Arial", font_size, bold=True)
        text_surf = font.render(label, True, (255, 255, 255))
        surf.blit(text_surf, text_surf.get_rect(center=(cx, cy)))

    return surf
