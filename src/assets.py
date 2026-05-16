"""
Asset loader with graceful fallbacks.
Every function returns a valid Surface even when files are missing.
"""
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
    """Load an image file. Returns None if missing or unreadable."""
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


def clear_cache():
    _cache.clear()


# ------------------------------------------------------------------
# Placeholder surfaces (used when real assets are absent)
# ------------------------------------------------------------------

def stop_placeholder(w: int, h: int, icon_label: str, visual_theme: str,
                     font: pygame.font.Font) -> pygame.Surface:
    """A styled placeholder for a stop illustration."""
    colour = THEME_COLOURS.get(visual_theme, THEME_COLOURS["default"])
    dark   = tuple(max(0, c - 40) for c in colour)
    light  = tuple(min(255, c + 60) for c in colour)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Background gradient approximation (two rects)
    pygame.draw.rect(surf, colour, (0, 0, w, h), border_radius=8)
    pygame.draw.rect(surf, dark,   (0, h // 2, w, h // 2), border_radius=8)

    # Subtle diagonal stripe texture
    for i in range(-h, w, 24):
        pygame.draw.line(surf, light, (i, 0), (i + h, h), 1)

    # Icon label centred
    big_font = pygame.font.SysFont("Arial, Helvetica", max(w // 6, 14))
    label_surf = big_font.render(icon_label, True, (255, 255, 255))
    label_surf.set_alpha(220)
    surf.blit(label_surf, label_surf.get_rect(center=(w // 2, h // 2)))

    # Border
    pygame.draw.rect(surf, (255, 255, 255, 80), (0, 0, w, h), width=2, border_radius=8)
    return surf


def token_badge(token_name: str, size: int = 40,
                bg_colour: Tuple[int, int, int] = (200, 160, 50)) -> pygame.Surface:
    """Circular badge with first letter — used as a token icon."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy, r = size // 2, size // 2, size // 2 - 1
    pygame.draw.circle(surf, bg_colour, (cx, cy), r)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r, width=2)
    font = pygame.font.SysFont("Arial", max(size // 3, 8), bold=True)
    letter = font.render(token_name[0].upper(), True, (255, 255, 255))
    surf.blit(letter, letter.get_rect(center=(cx, cy)))
    return surf
