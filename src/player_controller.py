"""
Player controller — WASD / arrow-key free movement restricted to the path mask.

The controller owns position, facing direction, and walk-animation state.
It does NOT own the sprite drawing; callers read .position, .direction,
.is_moving, .walk_frame, and .bob_offset and pass them to PlayerSprite.draw().
"""
import math
import pygame
from src.path_mask import PathMask

SPEED       = 88.0   # pixels per second
BOB_SPEED   = 2.6
BOB_AMP     = 2.2
WALK_SPEED  = 6.0
NEAR_DIST   = 36     # pixels — "near a stop" threshold for Space prompt


class PlayerController:

    def __init__(self):
        self._pos      = [0.0, 0.0]
        self._dir      = "down"   # "down" | "up" | "left" | "right"
        self._moving   = False
        self._walk_t   = 0.0
        self._bob_t    = 0.0

    # ── Setup ─────────────────────────────────────────────────────────────────

    def place_at(self, x: float, y: float):
        self._pos = [x, y]

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, keys, mask: PathMask,
               current_unlocked_id: int):
        """
        Read key state, attempt movement, update animation timers.
        mask.is_walkable() gates all movement.
        """
        dx = dy = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1.0
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1.0
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1.0

        # Normalise diagonal
        mag = math.hypot(dx, dy)
        if mag > 0:
            dx /= mag
            dy /= mag

        self._moving = False

        if dx != 0.0 or dy != 0.0:
            step = SPEED * dt
            nx = self._pos[0] + dx * step
            ny = self._pos[1] + dy * step

            # Try combined move first; fall back to axis-separated
            if mask.is_walkable(nx, ny, current_unlocked_id):
                self._pos[0] = nx
                self._pos[1] = ny
                self._moving = True
            else:
                moved = False
                if dx != 0.0 and mask.is_walkable(
                        self._pos[0] + dx * step, self._pos[1],
                        current_unlocked_id):
                    self._pos[0] += dx * step
                    moved = True
                if dy != 0.0 and mask.is_walkable(
                        self._pos[0], self._pos[1] + dy * step,
                        current_unlocked_id):
                    self._pos[1] += dy * step
                    moved = True
                self._moving = moved

            # Update facing direction
            if abs(dx) >= abs(dy):
                self._dir = "right" if dx > 0 else "left"
            else:
                self._dir = "down" if dy > 0 else "up"

        # Animation timers
        if self._moving:
            self._walk_t += dt * WALK_SPEED
        else:
            self._bob_t  += dt * BOB_SPEED

    # ── Proximity helper ──────────────────────────────────────────────────────

    def near_stop(self, stops: list, current_unlocked_id: int):
        """Return the current unlocked Stop if the player is close enough, else None."""
        for stop in stops:
            if stop.id != current_unlocked_id:
                continue
            sx = stop.route_position.x
            sy = stop.route_position.y + 30
            if math.hypot(self._pos[0] - sx, self._pos[1] - sy) <= NEAR_DIST:
                return stop
        return None

    # ── Read-only properties ──────────────────────────────────────────────────

    @property
    def position(self):
        return (self._pos[0], self._pos[1])

    @property
    def direction(self) -> str:
        return self._dir

    @property
    def is_moving(self) -> bool:
        return self._moving

    @property
    def walk_frame(self) -> int:
        return int(self._walk_t) % 2

    @property
    def bob_offset(self) -> int:
        return int(math.sin(self._bob_t) * BOB_AMP) if not self._moving else 0
