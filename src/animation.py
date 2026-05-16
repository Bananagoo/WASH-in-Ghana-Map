import math
import pygame
from typing import Tuple


# ------------------------------------------------------------------
# Easing functions (t is 0..1, output is 0..1)
# ------------------------------------------------------------------

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t * t * t
    return 1.0 - (-2 * t + 2) ** 3 / 2


def lerp_pos(a: Tuple[float, float], b: Tuple[float, float], t: float) -> Tuple[float, float]:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


# ------------------------------------------------------------------
# Tween — tracks progress over a fixed duration
# ------------------------------------------------------------------

class Tween:
    def __init__(self, duration: float):
        self.duration = max(duration, 0.001)
        self.elapsed = 0.0

    @property
    def value(self) -> float:
        return min(self.elapsed / self.duration, 1.0)

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    def update(self, dt: float):
        self.elapsed = min(self.elapsed + dt, self.duration)

    def restart(self):
        self.elapsed = 0.0


# ------------------------------------------------------------------
# FloatUpEffect — "+Token Name" drifts upward and fades out
# ------------------------------------------------------------------

class FloatUpEffect:
    def __init__(self, text: str, pos: Tuple[int, int], colour, font, duration: float = 1.4):
        self.text = text
        self.sx = pos[0]
        self.sy = float(pos[1])
        self.colour = colour
        self.font = font
        self._tween = Tween(duration)
        self.done = False

    def update(self, dt: float):
        self._tween.update(dt)
        if self._tween.done:
            self.done = True

    def draw(self, surface: pygame.Surface):
        t = ease_out(self._tween.value)
        alpha = int((1.0 - self._tween.value) * 255)
        y = int(self.sy - 70 * t)
        surf = self.font.render(self.text, True, self.colour)
        surf.set_alpha(alpha)
        surface.blit(surf, (self.sx - surf.get_width() // 2, y))


# ------------------------------------------------------------------
# PulseEffect — oscillating scale for stop markers
# ------------------------------------------------------------------

class PulseEffect:
    def __init__(self, speed: float = 3.0, amplitude: float = 4.0):
        self.speed = speed
        self.amplitude = amplitude
        self._t = 0.0

    def update(self, dt: float):
        self._t += dt * self.speed

    @property
    def offset(self) -> float:
        return self.amplitude * math.sin(self._t)
