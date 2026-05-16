"""
Overworld background renderer.

Pre-renders once to a pygame.Surface; route_screen blits it every frame.
Layers (bottom to top):
  1. Tiled 16px Sunnyside grass (falls back to solid fill)
  2. Bézier dirt path (circle-stamped for smooth round edges)
  3. Sunnyside tree, crop, and animal sprites scattered off the path
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
_SCENERY_STRIPS = [
    ("assets/images/deco/animals/spr_deco_chicken_01_strip4.png", 4, 16, 2),
    ("assets/images/deco/animals/spr_deco_bird_01_strip4.png", 4, 16, 2),
    ("assets/images/deco/animals/spr_deco_duck_01_strip4.png", 4, 16, 2),
]
_SCENERY_SINGLES = [
    ("assets/images/deco/crops/sunflower_05.png", 2),
    ("assets/images/deco/crops/cabbage_05.png", 2),
    ("assets/images/deco/crops/wheat_05.png", 2),
    ("assets/images/deco/crops/pumpkin_05.png", 2),
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
        scenery_sprites = _load_scenery_sprites()

        # 1. Grass — fill base colour first so any transparent tile edges
        #    blend with green instead of the default black surface background
        surf.fill(_G_BASE)
        if grass_tiles:
            _draw_tiled_grass(surf, grass_tiles)

        # 2. Path
        self._draw_path(surf, pts, self._curve)

        # 3. Scattered scenery sprites
        self._scatter(surf, pts, self._curve, rng, tree_sprites, scenery_sprites)

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
        if len(stop_pts) < 2:
            return list(stop_pts), []

        out = [stop_pts[0]]
        seg_lengths = []

        # Cubic Hermite interpolation gives each stop a shared incoming/outgoing
        # tangent, avoiding hard corners while keeping the route organic.
        for i in range(len(stop_pts) - 1):
            p0 = stop_pts[max(i - 1, 0)]
            p1 = stop_pts[i]
            p2 = stop_pts[i + 1]
            p3 = stop_pts[min(i + 2, len(stop_pts) - 1)]

            ax, ay = p1
            bx, by = p2
            dist = math.hypot(bx - ax, by - ay)
            n = max(18, int(dist / 3))
            seg_lengths.append(n)

            m1 = ((p2[0] - p0[0]) * 0.34, (p2[1] - p0[1]) * 0.34)
            m2 = ((p3[0] - p1[0]) * 0.34, (p3[1] - p1[1]) * 0.34)
            dx, dy = bx - ax, by - ay
            length = max(math.hypot(dx, dy), 1)
            nx, ny = -dy / length, dx / length
            bend = 18 * (-1 if i % 2 else 1)

            for j in range(1, n + 1):
                t = j / n
                t2 = t * t
                t3 = t2 * t
                h00 = 2*t3 - 3*t2 + 1
                h10 = t3 - 2*t2 + t
                h01 = -2*t3 + 3*t2
                h11 = t3 - t2
                cx = h00*p1[0] + h10*m1[0] + h01*p2[0] + h11*m2[0]
                cy = h00*p1[1] + h10*m1[1] + h01*p2[1] + h11*m2[1]

                wave = (math.sin(math.pi * t) ** 2) * bend
                if abs(dx) > abs(dy) * 1.2:
                    cx += nx * wave
                    cy += ny * wave

                out.append((round(cx), round(cy)))

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

    def _scatter(self, surf, stop_pts, curve, rng, tree_sprites, scenery_sprites):
        placed: list = []

        if tree_sprites:
            self._scatter_group(
                surf, stop_pts, curve, rng, tree_sprites, placed,
                attempts=800, stop_clearance=100, path_clearance=55,
                object_clearance=54, max_count=48,
            )

        if scenery_sprites:
            self._scatter_group(
                surf, stop_pts, curve, rng, scenery_sprites, placed,
                attempts=240, stop_clearance=74, path_clearance=42,
                object_clearance=78, max_count=24,
            )

    def _scatter_group(self, surf, stop_pts, curve, rng, sprites, placed,
                       attempts, stop_clearance, path_clearance, object_clearance,
                       max_count):
        count = 0
        for _ in range(attempts):
            if count >= max_count:
                return
            x = rng.randint(12, self._w - 12)
            y = rng.randint(12, self._h - 12)
            if any(math.hypot(x-px, y-py) < stop_clearance for px, py in stop_pts):
                continue
            if _near_points(x, y, curve, path_clearance):
                continue
            if any(math.hypot(x-ox, y-oy) < object_clearance for ox, oy in placed):
                continue
            _blit_sprite(surf, x, y, rng.choice(sprites))
            placed.append((x, y))
            count += 1


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


def _load_scenery_sprites() -> list:
    sprites = []

    for path, n_frames, fw, scale in _SCENERY_STRIPS:
        if not os.path.exists(path):
            continue
        try:
            sheet = pygame.image.load(path).convert_alpha()
            fh = sheet.get_height()
            for i in range(n_frames):
                frame = sheet.subsurface(
                    pygame.Rect(i * fw, 0, fw, fh)).copy()
                sprites.append(
                    pygame.transform.scale(frame, (fw * scale, fh * scale)))
        except Exception:
            pass

    for path, scale in _SCENERY_SINGLES:
        if not os.path.exists(path):
            continue
        try:
            img = pygame.image.load(path).convert_alpha()
            iw, ih = img.get_size()
            sprites.append(pygame.transform.scale(img, (iw * scale, ih * scale)))
        except Exception:
            pass

    return sprites


def _blit_sprite(surf: pygame.Surface, x: int, y: int,
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


def _near_points(x, y, pts, threshold):
    threshold_sq = threshold * threshold
    for px, py in pts:
        dx = x - px
        dy = y - py
        if dx * dx + dy * dy < threshold_sq:
            return True
    return False
