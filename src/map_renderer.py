"""
Stylized Ghana map background renderer.
Pre-renders to a Surface once; blitted every frame.
Not geographically precise — evocative of a hand-drawn field map.
"""
import math
import pygame
from typing import List, Tuple


# ------------------------------------------------------------------
# Ghana outline polygon (normalized 0..1 fractions of map area)
# Clockwise from NW. Stylized, not accurate.
# ------------------------------------------------------------------
_GHANA_NORM = [
    (0.10, 0.03),
    (0.28, 0.00),
    (0.50, 0.01),
    (0.70, 0.03),
    (0.85, 0.07),
    (0.90, 0.20),
    (0.93, 0.42),
    (0.96, 0.62),
    (0.91, 0.80),
    (0.80, 0.92),
    (0.58, 0.97),
    (0.34, 0.96),
    (0.14, 0.90),
    (0.05, 0.74),
    (0.03, 0.50),
    (0.05, 0.28),
    (0.08, 0.12),
]

# Terrain blobs: (norm_x, norm_y, rx_px, ry_px, colour_shift)
_BLOBS = [
    (0.38, 0.58, 90, 55, (0,  28,  5)),   # forest belt center
    (0.56, 0.65, 70, 48, (0,  22,  8)),   # forest belt right
    (0.44, 0.72, 95, 42, (5,  32,  0)),   # south forest
    (0.45, 0.40, 65, 38, (18, 14, -8)),   # Ashanti plateau
    (0.38, 0.12, 115, 38, (26, 10, -14)), # northern savanna
    (0.65, 0.18, 85, 32, (22,  8, -12)),  # northeast
    (0.74, 0.52, 40, 72, (0,  14,  28)),  # Volta lake hint
]

# City dot labels: (norm_x, norm_y, label)
_CITIES = [
    (0.26, 0.76, "Accra"),
    (0.20, 0.60, "Cape Coast"),
    (0.44, 0.38, "Kumasi"),
    (0.48, 0.10, "Tamale"),
    (0.72, 0.50, "Volta"),
    (0.32, 0.28, "Berekuso"),
]


class MapRenderer:
    """Build once, blit every frame."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._bg: pygame.Surface = None

    def build(self):
        surf = pygame.Surface((self.width, self.height))
        self._draw_parchment(surf)
        self._draw_territory(surf)
        self._draw_blobs(surf)
        self._draw_coastline(surf)
        self._draw_cities(surf)
        self._draw_compass(surf)
        self._draw_title(surf)
        self._bg = surf

    def draw_background(self, surface: pygame.Surface, x: int = 0, y: int = 0):
        if self._bg is None:
            self.build()
        surface.blit(self._bg, (x, y))

    # ------------------------------------------------------------------
    # Internal layers
    # ------------------------------------------------------------------

    def _draw_parchment(self, surf: pygame.Surface):
        surf.fill((232, 220, 190))
        # Grid dots — paper/map texture
        dot_col = (215, 204, 172)
        for gx in range(0, self.width, 30):
            for gy in range(0, self.height, 30):
                pygame.draw.circle(surf, dot_col, (gx, gy), 1)

    def _scaled_poly(self) -> List[Tuple[int, int]]:
        return [(int(nx * self.width), int(ny * self.height))
                for nx, ny in _GHANA_NORM]

    def _draw_territory(self, surf: pygame.Surface):
        poly = self._scaled_poly()
        # Fill
        pygame.draw.polygon(surf, (210, 200, 160), poly)
        # Outline — drawn as dotted-ish by drawing short segments
        for i in range(len(poly)):
            a = poly[i]
            b = poly[(i + 1) % len(poly)]
            pygame.draw.line(surf, (160, 145, 105), a, b, 2)

    def _draw_blobs(self, surf: pygame.Surface):
        base = (210, 200, 155)
        for nx, ny, rx, ry, shift in _BLOBS:
            cx = int(nx * self.width)
            cy = int(ny * self.height)
            col = tuple(max(0, min(255, base[i] + shift[i])) for i in range(3))
            blob = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(blob, (*col, 110), (0, 0, rx * 2, ry * 2))
            surf.blit(blob, (cx - rx, cy - ry))

    def _draw_coastline(self, surf: pygame.Surface):
        coast_y = int(self.height * 0.91)
        water_h = self.height - coast_y
        water = pygame.Surface((self.width, water_h), pygame.SRCALPHA)
        water.fill((120, 170, 210, 150))
        surf.blit(water, (0, coast_y))

        # Wave arcs
        wave_col = (90, 140, 185)
        for row in range(3):
            wy = coast_y + 8 + row * 11
            for wx in range(0, self.width, 36):
                pygame.draw.arc(surf, wave_col,
                                pygame.Rect(wx, wy, 26, 7), 0, math.pi, 1)

        font = pygame.font.SysFont("Arial, Helvetica", 11)
        lbl = font.render("Gulf of Guinea", True, (70, 110, 155))
        surf.blit(lbl, lbl.get_rect(center=(self.width // 2, coast_y + 20)))

    def _draw_cities(self, surf: pygame.Surface):
        font = pygame.font.SysFont("Arial, Helvetica", 11)
        for nx, ny, name in _CITIES:
            cx = int(nx * self.width)
            cy = int(ny * self.height)
            pygame.draw.circle(surf, (145, 115, 80), (cx, cy), 3)
            pygame.draw.circle(surf, (100, 80, 55), (cx, cy), 3, width=1)
            lbl = font.render(name, True, (110, 85, 55))
            surf.blit(lbl, (cx + 6, cy - 8))

    def _draw_compass(self, surf: pygame.Surface):
        cx, cy, r = self.width - 48, self.height - 52, 22
        pygame.draw.circle(surf, (218, 208, 182), (cx, cy), r)
        pygame.draw.circle(surf, (165, 148, 108), (cx, cy), r, width=1)
        # North arrow (red)
        tip    = (cx, cy - r + 5)
        left   = (cx - 5, cy + 5)
        right  = (cx + 5, cy + 5)
        pygame.draw.polygon(surf, (185, 60, 55), [tip, left, right])
        # South arrow (grey)
        s_tip  = (cx, cy + r - 5)
        s_left = (cx - 5, cy - 5)
        s_rht  = (cx + 5, cy - 5)
        pygame.draw.polygon(surf, (160, 155, 145), [s_tip, s_left, s_rht])
        font = pygame.font.SysFont("Arial", 10, bold=True)
        n_lbl = font.render("N", True, (75, 60, 50))
        surf.blit(n_lbl, n_lbl.get_rect(center=(cx, cy - r - 8)))

    def _draw_title(self, surf: pygame.Surface):
        font = pygame.font.SysFont("Arial, Helvetica", 12)
        lbl = font.render("Ghana Field Route", True, (130, 105, 70))
        surf.blit(lbl, (10, self.height - 20))
