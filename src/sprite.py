"""
Player sprite — Sunnyside World longhair character (strip animation).
Falls back to procedural pixel-art character if assets are missing.

The Sunnyside Human sprites are layered (base body + hair overlay).
We composite them at load time, crop to the character bounds, and scale 3x
so the ~16x19px pixel art character renders as a legible ~50x60px figure.

Transparency: composited frames use SRCALPHA. Left-facing frames are
pre-converted to colorkey surfaces and pre-flipped so pygame.transform.flip()
is never called at draw time (avoids the pygame 2.0.x SRCALPHA+flip bug).
"""
import math
import os
import pygame

_BASE_IDLE = "assets/images/sprites/base_idle_strip9.png"
_HAIR_IDLE = "assets/images/sprites/longhair_idle_strip9.png"
_BASE_WALK = "assets/images/sprites/base_walk_strip8.png"
_HAIR_WALK = "assets/images/sprites/longhair_walk_strip8.png"

_IDLE_N  = 9
_WALK_N  = 8
_FRAME_W = 96
_FRAME_H = 64
_SCALE   = 3      # nearest-neighbor scale applied after cropping
_PAD     = 3      # transparent padding (px) kept around character bbox
_IDLE_FPS = 7.0
_WALK_FPS = 9.0

# Colorkey for pre-flipped left-facing surfaces (pygame 2.0.x flip-safe)
_CKEY = (0, 0, 1)


class PlayerSprite:

    def __init__(self):
        self._idle_r: list = []
        self._idle_l: list = []
        self._walk_r: list = []
        self._walk_l: list = []
        self._blit_ox  = 0   # x offset: blit at (x - _blit_ox) to centre character
        self._blit_oy  = 0   # y offset: blit at (y - _blit_oy) to centre character
        self._feet_oy  = 0   # y offset: blit at (y - _feet_oy) so feet land at y
        self._loaded   = False
        self._anim_t  = 0.0

    # ── Procedural fallback palette ───────────────────────────────────────────
    _SKIN     = (220, 182, 138)
    _HAIR     = (222, 188,  68)
    _HAIR_DK  = (192, 158,  48)
    _DENIM    = ( 85, 115, 158)
    _DENIM_DK = ( 68,  95, 132)
    _CREAM    = (245, 238, 218)
    _BOOT     = ( 72,  55,  38)
    _EYE      = ( 90, 155, 215)
    _PUPIL    = ( 40,  30,  20)

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_image(self):
        if self._loaded:
            return
        self._loaded = True

        idle_r, idle_l, ox, oy, foy = self._build_strip(_BASE_IDLE, _HAIR_IDLE, _IDLE_N)
        walk_r, walk_l, _,  _,  _  = self._build_strip(_BASE_WALK, _HAIR_WALK, _WALK_N,
                                                        ref_ox=ox, ref_oy=oy, ref_foy=foy)
        self._idle_r, self._idle_l = idle_r, idle_l
        self._walk_r, self._walk_l = walk_r, walk_l
        self._blit_ox, self._blit_oy, self._feet_oy = ox, oy, foy

    def _build_strip(self, base_path, hair_path, n, ref_ox=None, ref_oy=None, ref_foy=None):
        """
        Composite base + hair layers, find character bbox, crop, scale 3x,
        convert to colorkey, pre-flip for left-facing.

        ref_ox/ref_oy/ref_foy: re-use previously computed blit offsets so walk frames
        stay spatially consistent with idle frames (same anchor).
        feet_oy: distance from frame top to feet position at scale — blit at
        (x - blit_ox, y - feet_oy) so the character's feet land exactly at (x, y).
        """
        if not (os.path.exists(base_path) and os.path.exists(hair_path)):
            return [], [], 0, 0, 0
        try:
            base_sheet = pygame.image.load(base_path).convert_alpha()
            hair_sheet = pygame.image.load(hair_path).convert_alpha()
        except Exception:
            return [], [], 0, 0, 0

        # Composite each frame onto an SRCALPHA surface
        raw = []
        for i in range(n):
            r = pygame.Rect(i * _FRAME_W, 0, _FRAME_W, _FRAME_H)
            f = pygame.Surface((_FRAME_W, _FRAME_H), pygame.SRCALPHA)
            f.blit(base_sheet.subsurface(r), (0, 0))
            f.blit(hair_sheet.subsurface(r), (0, 0))
            raw.append(f)

        # Global bbox across all frames so the character doesn't jitter
        all_x, all_y = [], []
        for f in raw:
            for fy in range(_FRAME_H):
                for fx in range(_FRAME_W):
                    if f.get_at((fx, fy))[3] > 10:
                        all_x.append(fx)
                        all_y.append(fy)

        if not all_x:
            return [], [], 0, 0, 0

        cx0 = max(0, min(all_x) - _PAD)
        cy0 = max(0, min(all_y) - _PAD)
        cx1 = min(_FRAME_W, max(all_x) + _PAD + 1)
        cy1 = min(_FRAME_H, max(all_y) + _PAD + 1)
        cw, ch = cx1 - cx0, cy1 - cy0

        # Scaled blit offsets
        char_cx = (min(all_x) + max(all_x)) // 2 - cx0
        char_cy = (min(all_y) + max(all_y)) // 2 - cy0
        # feet_y: pixels from crop-top to the bottom of the character's bounding box
        feet_y_in_crop = max(all_y) - cy0
        ox  = ref_ox  if ref_ox  is not None else char_cx       * _SCALE
        oy  = ref_oy  if ref_oy  is not None else char_cy       * _SCALE
        foy = ref_foy if ref_foy is not None else feet_y_in_crop * _SCALE

        # Crop → scale → colorkey → pre-flip
        right_frames, left_frames = [], []
        for f in raw:
            cropped = f.subsurface(pygame.Rect(cx0, cy0, cw, ch)).copy()
            scaled  = pygame.transform.scale(cropped, (cw * _SCALE, ch * _SCALE))
            ck      = self._to_colorkey(scaled)
            right_frames.append(ck)
            left_frames.append(pygame.transform.flip(ck, True, False))

        return right_frames, left_frames, ox, oy, foy

    @staticmethod
    def _to_colorkey(src: pygame.Surface) -> pygame.Surface:
        """Composite SRCALPHA surface onto colorkey surface (flip-safe result)."""
        w, h = src.get_size()
        dst  = pygame.Surface((w, h)).convert()   # match display format for reliable colorkey
        dst.fill(_CKEY)
        dst.set_colorkey(_CKEY)
        dst.blit(src, (0, 0))
        return dst

    # ── Animation update ──────────────────────────────────────────────────────

    def update(self, dt: float):
        self._anim_t += dt

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface,
             x: int, y: int,
             direction: str = "down",
             moving: bool = False,
             walk_frame: int = 0,
             bob_offset: int = 0):
        yd = y + bob_offset

        if self._idle_r:
            self._blit_strip_frame(surface, x, yd, direction, moving)
            return

        # Procedural fallback — shift up so feet land at yd (not center)
        yd_feet = yd - 15
        if direction in ("down", "up"):
            self._draw_front(surface, x, yd_feet,
                             walk_frame if moving else -1,
                             facing_back=(direction == "up"))
        else:
            self._draw_side(surface, x, yd_feet,
                            walk_frame if moving else -1,
                            flip=(direction == "left"))

    def _blit_strip_frame(self, surface, x, y, direction, moving):
        if direction == "left":
            frames = self._walk_l if (moving and self._walk_l) else self._idle_l
        else:
            frames = self._walk_r if (moving and self._walk_r) else self._idle_r

        fps   = _WALK_FPS if moving else _IDLE_FPS
        idx   = int(self._anim_t * fps) % len(frames)
        frame = frames[idx]
        surface.blit(frame, (x - self._blit_ox, y - self._feet_oy))

    # ── Procedural: front-facing ──────────────────────────────────────────────

    def _draw_front(self, surf, x, y, walk_frame, facing_back=False):
        sk = self._SKIN;  ha = self._HAIR;  hd = self._HAIR_DK
        dn = self._DENIM; dd = self._DENIM_DK; cr = self._CREAM
        bt = self._BOOT

        if walk_frame == 0:
            loff, roff = -2, 2
        elif walk_frame == 1:
            loff, roff = 2, -2
        else:
            loff = roff = 0

        pygame.draw.ellipse(surf, bt, pygame.Rect(x - 9, y + 9 + loff, 8, 6))
        pygame.draw.ellipse(surf, bt, pygame.Rect(x + 1,  y + 9 + roff, 8, 6))
        pygame.draw.ellipse(surf, dn, pygame.Rect(x - 10, y - 6, 20, 20))
        pygame.draw.ellipse(surf, dd, pygame.Rect(x - 10, y - 6, 20, 20), 1)

        if not facing_back:
            pygame.draw.line(surf, dd, (x - 3, y - 6), (x - 3, y + 2))
            pygame.draw.line(surf, dd, (x + 3, y - 6), (x + 3, y + 2))
            pygame.draw.arc(surf, cr, pygame.Rect(x - 7, y - 8, 14, 8),
                            math.radians(0), math.radians(180), 3)

        pygame.draw.ellipse(surf, sk, pygame.Rect(x - 16, y - 4, 7, 6))
        pygame.draw.ellipse(surf, sk, pygame.Rect(x + 9,  y - 4, 7, 6))
        pygame.draw.circle(surf, sk, (x, y - 10), 9)

        if facing_back:
            pygame.draw.circle(surf, hd, (x, y - 10), 9)
            pygame.draw.ellipse(surf, hd, pygame.Rect(x - 9, y - 20, 18, 10))
            pygame.draw.line(surf, hd, (x, y - 1), (x, y + 6), 3)
        else:
            pygame.draw.ellipse(surf, hd, pygame.Rect(x - 10, y - 22, 20, 10))
            pygame.draw.ellipse(surf, ha, pygame.Rect(x - 9,  y - 20, 18,  9))
            pygame.draw.ellipse(surf, ha, pygame.Rect(x - 12, y - 13,  6, 10))
            pygame.draw.ellipse(surf, ha, pygame.Rect(x + 6,  y - 13,  6, 10))
            pygame.draw.circle(surf, self._EYE,   (x - 3, y - 11), 2)
            pygame.draw.circle(surf, self._EYE,   (x + 3, y - 11), 2)
            pygame.draw.circle(surf, self._PUPIL, (x - 3, y - 11), 1)
            pygame.draw.circle(surf, self._PUPIL, (x + 3, y - 11), 1)
            pygame.draw.arc(surf, (190, 130, 100),
                            pygame.Rect(x - 3, y - 8, 6, 4),
                            math.radians(200), math.radians(340), 1)

    # ── Procedural: side profile ──────────────────────────────────────────────

    def _draw_side(self, surf, x, y, walk_frame, flip=False):
        tmp = pygame.Surface((60, 50)).convert()
        tmp.fill(_CKEY)
        tmp.set_colorkey(_CKEY)
        tx, ty = 30, 25

        sk = self._SKIN;  ha = self._HAIR;  hd = self._HAIR_DK
        dn = self._DENIM; dd = self._DENIM_DK; cr = self._CREAM
        bt = self._BOOT

        if walk_frame == 0:
            f_off, b_off, arm_dy = -3, 3, -2
        elif walk_frame == 1:
            f_off, b_off, arm_dy = 3, -3, 2
        else:
            f_off = b_off = arm_dy = 0

        pygame.draw.ellipse(tmp, dd, pygame.Rect(tx - 1, ty + 8 + b_off, 7, 7))
        pygame.draw.ellipse(tmp, bt, pygame.Rect(tx,     ty + 12 + b_off, 6, 5))
        pygame.draw.ellipse(tmp, dn, pygame.Rect(tx - 8, ty - 6, 16, 20))
        pygame.draw.ellipse(tmp, dd, pygame.Rect(tx - 8, ty - 6, 16, 20), 1)
        pygame.draw.ellipse(tmp, dn, pygame.Rect(tx + 2, ty + 8 + f_off, 7, 7))
        pygame.draw.ellipse(tmp, bt, pygame.Rect(tx + 2, ty + 12 + f_off, 7, 5))
        pygame.draw.circle(tmp, cr, (tx + 4, ty - 7), 4)
        pygame.draw.ellipse(tmp, sk, pygame.Rect(tx + 5, ty - 2 + arm_dy, 6, 5))

        hx, hy = tx + 2, ty - 10
        pygame.draw.circle(tmp, sk, (hx, hy), 8)
        pygame.draw.ellipse(tmp, hd, pygame.Rect(tx - 8, ty - 20, 14, 10))
        pygame.draw.ellipse(tmp, ha, pygame.Rect(tx - 6, ty - 19, 12,  9))
        pygame.draw.ellipse(tmp, ha, pygame.Rect(tx - 10, ty - 14, 7, 12))
        pygame.draw.ellipse(tmp, ha, pygame.Rect(hx - 8, ty - 20, 14, 9))
        pygame.draw.circle(tmp, self._EYE,   (hx + 4, hy - 1), 2)
        pygame.draw.circle(tmp, self._PUPIL, (hx + 5, hy - 1), 1)
        pygame.draw.arc(tmp, (190, 130, 100),
                        pygame.Rect(hx + 1, hy + 2, 5, 4),
                        math.radians(200), math.radians(340), 1)

        if flip:
            tmp = pygame.transform.flip(tmp, True, False)
        surf.blit(tmp, (x - 30, y - 25))
