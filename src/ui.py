import pygame
from typing import Callable, Optional, Tuple
from src import config as C


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        font: pygame.font.Font,
        colour: Tuple[int, int, int] = None,
        hover_colour: Tuple[int, int, int] = None,
        text_colour: Tuple[int, int, int] = None,
        border_radius: int = C.BUTTON_BORDER_RADIUS,
    ):
        self.rect = rect
        self.label = label
        self.font = font
        self.colour = colour or C.BUTTON_COLOUR
        self.hover_colour = hover_colour or C.BUTTON_HOVER_COLOUR
        self.text_colour = text_colour or C.BUTTON_TEXT_COLOUR
        self.border_radius = border_radius
        self._hovered = False
        self.visible = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        colour = self.hover_colour if self._hovered else self.colour
        pygame.draw.rect(surface, colour, self.rect, border_radius=self.border_radius)
        text_surf = self.font.render(self.label, True, self.text_colour)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Panel:
    def __init__(self, rect: pygame.Rect, colour: Tuple[int, int, int] = C.PANEL_COLOUR,
                 border_radius: int = 8):
        self.rect = rect
        self.colour = colour
        self.border_radius = border_radius

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.colour, self.rect, border_radius=self.border_radius)


def wrap_text(text: str, font: pygame.font.Font, max_width: int):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        if font.size(test)[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_text_block(
    surface: pygame.Surface,
    lines,
    font: pygame.font.Font,
    colour: Tuple[int, int, int],
    x: int,
    y: int,
    line_spacing: int = 4,
) -> int:
    """Draw a list of strings. Returns the y coordinate after the last line."""
    for line in lines:
        surf = font.render(line, True, colour)
        surface.blit(surf, (x, y))
        y += font.get_height() + line_spacing
    return y


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    colour: Tuple[int, int, int],
    x: int,
    y: int,
    max_width: int,
    line_spacing: int = 4,
) -> int:
    lines = wrap_text(text, font, max_width)
    return draw_text_block(surface, lines, font, colour, x, y, line_spacing)


def draw_label(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    colour: Tuple[int, int, int],
    rect: pygame.Rect,
    align: str = "left",
):
    surf = font.render(text, True, colour)
    if align == "center":
        pos = surf.get_rect(center=rect.center)
    elif align == "right":
        pos = surf.get_rect(midright=rect.midright)
    else:
        pos = surf.get_rect(midleft=rect.midleft)
    surface.blit(surf, pos)


class FontCache:
    _cache = {}

    @classmethod
    def get(cls, size: int) -> pygame.font.Font:
        if size not in cls._cache:
            cls._cache[size] = pygame.font.SysFont("Arial, Helvetica, sans-serif", size)
        return cls._cache[size]

    @classmethod
    def clear(cls):
        cls._cache.clear()


def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               bg: tuple, border: tuple, radius: int = 8, border_w: int = 2):
    """Draw a filled, bordered rounded rectangle panel."""
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, border_w, border_radius=radius)
