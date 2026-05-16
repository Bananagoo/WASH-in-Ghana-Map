import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game import Game


class BaseScreen:
    """All screens inherit from this. Each screen owns its own event handling,
    update logic, and draw logic."""

    def __init__(self, game: "Game"):
        self.game = game

    def on_enter(self):
        """Called once each time this screen becomes active."""

    def on_exit(self):
        """Called once when leaving this screen."""

    def handle_event(self, event: pygame.event.Event):
        """Handle a single pygame event."""

    def update(self, dt: float):
        """Update logic; dt is elapsed seconds since last frame."""

    def draw(self, surface: pygame.Surface):
        """Draw everything to surface."""
