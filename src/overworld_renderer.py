"""
Overworld background renderer.

Pre-renders once to a pygame.Surface; route_screen blits it every frame.
Layers (bottom to top):
  1. Tiled 16px Sunnyside grass (falls back to solid fill)
  2. Bézier dirt path (circle-stamped for smooth round edges)
  3. Sunnyside tree sprites scattered off the path
"""
import math
import os
import random
import pygame

R = pygame.Rect

# ── Path colours ──────────────────────────────────────────────────────────────
_PE = (118, 82, 42)     # path edge (dark earth)
_PS = (178, 140, 88)    # path surface (warm tan)
_PC = (200, 168, 110)   # path centre highlight

# ── Fallback fill colour (used if tileset is missing) ─────────────────────────
_G_BASE = (100, 148, 68)

# ── Asset paths ───────────────────────────────────────────────────────────────
_TILESET_PATH = "assets/images/tileset/spr_tileset_16px.png"
_TREE_STRIPS  = [
    ("assets/images/deco/spr_deco_tree_01_strip4.png", 4, 32),
    ("assets/images/deco/spr_deco_tree_02_strip4.png", 4, 28),
]

_TILE_SRC = 16    # atlas tile size
_TILE_DSP = 32    # displayed size (2×)
_TREE_SCL = 2     # tree scale factor


class OverworldRenderer:
    """Build the overworld background once, blit it every frame."""

    HEADER_H    = 54
    PATH_W_EDGE = 32
    PATH_W_SURF = 22
    PATH_W_CTR  =  8

    def __init__(self, width: int, height: int):
        self._w = width
        self._h = height
        self._surface: pygame.Surface | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def build(self, stops: list):
        rng  = random.Random(42)
        surf = pygame.Surface((self._w, self._h)).convert()

        pts = [(s.route_position.x,
                s.route_position.y + 30 - self.HEADER_H)
               for s in stops]

        self._curve, self._seg_lengths = self._make_curve(pts)
        self._pts_surface = list(pts)

        grass_tiles  = _load_grass_tiles()
        tree_sprites = _load_tree_sprites()

        # 1. Grass — fill base colour first so any transparent tile edges
        #    blend with green instead of the default black surface background
        surf.fill(_G_BASE)
        if grass_tiles:
            _draw_tiled_grass(surf, grass_tiles)

        # 2. Path
        self._draw_path(surf, pts, self._curve)

        # 3. Scattered tree sprites
        self._scatter(surf, pts, self._curve, rng, tree_sprites)

        self._surface = surf

    def draw_background(self, surface: pygame.Surface, x: int, y: int):
        if self._surface:
            surface.blit(self._surface, (x, y))

    @property
    def curve_screen(self) -> list:
        return [(x, y + self.HEADER_H) for x, y in self._curve]

    @property
    def seg_lengths(self) -> list:
        return list(self._seg_lengths)

    # ── Bézier curve ──────────────────────────────────────────────────────────

    @staticmethod
    def _make_curve(stop_pts: list):
        out = [stop_pts[0]]
        seg_lengths = []
        alt = 1
        rng = random.Random(17)

        for a, b in zip(stop_pts, stop_pts[1:]):
            ax, ay = a
            bx, by = b
            dist = math.hypot(bx - ax, by - ay)
            is_horiz = abs(bx - ax) > abs(by - ay) * 1.4

            if is_horiz:
                mx, my = (ax + bx) / 2, (ay + by) / 2
                ctrl   = (mx, my + 42 * alt)
                alt    = -alt
            else:
                dx, dy = bx - ax, by - ay
                length = max(dist, 1)
                px, py = -dy / length, dx / length
                mx, my = (ax + bx) / 2, (ay + by) / 2
                off    = rng.uniform(24, 40) * alt
                ctrl   = (mx + px * off, my + py * off)

            n = max(12, int(dist / 4))
            seg_lengths.append(n)
            for j in range(1, n + 1):
                t  = j / n
                cx = (1-t)**2*ax + 2*(1-t)*t*ctrl[0] + t**2*bx
                cy = (1-t)**2*ay + 2*(1-t)*t*ctrl[1] + t**2*by
                out.append((int(cx), int(cy)))

        return out, seg_lengths

    # ── Path ──────────────────────────────────────────────────────────────────

    def _draw_path(self, surf, stop_pts, curve):
        if len(curve) < 2:
            return
        re = self.PATH_W_EDGE // 2
        rs = self.PATH_W_SURF // 2
        rc = self.PATH_W_CTR  // 2

        # Circle-stamp each layer for perfectly rounded edges and joins
        for px, py in curve:
            pygame.draw.circle(surf, _PE, (int(px), int(py)), re)
        for px, py in curve:
            pygame.draw.circle(surf, _PS, (int(px), int(py)), rs)
        for px, py in curve:
            pygame.draw.circle(surf, _PC, (int(px), int(py)), rc)

    # ── Scatter ───────────────────────────────────────────────────────────────

    def _scatter(self, surf, stop_pts, curve, rng, tree_sprites):
        if not tree_sprites:
            return
        placed: list = []
        for _ in range(800):
            x = rng.randint(12, self._w - 12)
            y = rng.randint(12, self._h - 12)
            if any(math.hypot(x-px, y-py) < 100 for px, py in stop_pts):
                continue
            if _near_seg(x, y, stop_pts, 55):
                continue
            if any(math.hypot(x-ox, y-oy) < 54 for ox, oy in placed):
                continue
            _blit_tree_sprite(surf, x, y, rng.choice(tree_sprites))
            placed.append((x, y))


# ── Asset loaders ─────────────────────────────────────────────────────────────

def _load_grass_tiles() -> list:
    """Load uniformly bright grass tiles from the 16px Sunnyside tileset atlas.

    5×5 sample (25 points including near-edges).  All 25 must pass the
    green-dominance check, the tile's mean G must be ≥ 140, and the spread
    (max G – min G across the 25 points) must be < 28 to exclude shadowed or
    patterned variants.  Finally, only tiles within 88 % of the brightest
    passing mean are kept so the tiled field looks uniform.
    """
    if not os.path.exists(_TILESET_PATH):
        return []
    try:
        sheet = pygame.image.load(_TILESET_PATH).convert_alpha()
        TILE  = _TILE_SRC
        candidates = []

        for row in range(8):
            for col in range(24):
                gs  = []
                ok  = True
                for dy in (1, 3, 6, 8, 10, 12, 14):
                    for dx in (1, 3, 6, 8, 10, 12, 14):
                        r, g, b, a = sheet.get_at((col*TILE+dx, row*TILE+dy))
                        if not (a > 220 and g > 120 and g > r * 1.2 and g > b + 20):
                            ok = False
                            break
                        gs.append(g)
                    if not ok:
                        break
                if not ok:
                    continue
                mean_g = sum(gs) / len(gs)
                if mean_g < 140 or (max(gs) - min(gs)) > 28:
                    continue        # too dark or uneven
                src = sheet.subsurface(
                    pygame.Rect(col*TILE, row*TILE, TILE, TILE)).copy()
                candidates.append((mean_g, src))

        if not candidates:
            return []

        max_mean = max(m for m, _ in candidates)
        cutoff   = max_mean * 0.88
        final    = [s for m, s in candidates if m >= cutoff] or \
                   [s for _, s in candidates]

        return [pygame.transform.scale(s, (_TILE_DSP, _TILE_DSP)) for s in final]
    except Exception:
        return []


def _draw_tiled_grass(surf: pygame.Surface, tiles: list):
    w, h = surf.get_size()
    n    = len(tiles)
    for ty in range(0, h, _TILE_DSP):
        for tx in range(0, w, _TILE_DSP):
            idx = (tx // _TILE_DSP * 7919 + ty // _TILE_DSP * 2053) % n
            surf.blit(tiles[idx], (tx, ty))


def _load_tree_sprites() -> list:
    sprites = []
    for path, n_frames, fw in _TREE_STRIPS:
        if not os.path.exists(path):
            continue
        try:
            sheet = pygame.image.load(path).convert_alpha()
            fh    = sheet.get_height()
            for i in range(n_frames):
                frame = sheet.subsurface(
                    pygame.Rect(i * fw, 0, fw, fh)).copy()
                sprites.append(
                    pygame.transform.scale(frame, (fw * _TREE_SCL, fh * _TREE_SCL)))
        except Exception:
            pass
    return sprites


def _blit_tree_sprite(surf: pygame.Surface, x: int, y: int,
                      spr: pygame.Surface):
    sw, sh = spr.get_size()
    surf.blit(spr, (x - sw // 2, y - sh))


# ── Geometry helper ───────────────────────────────────────────────────────────

def _near_seg(x, y, pts, threshold):
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i+1]
        dx, dy = bx-ax, by-ay
        sq = dx*dx + dy*dy
        if sq == 0:
            d = math.hypot(x-ax, y-ay)
        else:
            t = max(0.0, min(1.0, ((x-ax)*dx + (y-ay)*dy) / sq))
            d = math.hypot(x-(ax+t*dx), y-(ay+t*dy))
        if d < threshold:
            return True
    return False
