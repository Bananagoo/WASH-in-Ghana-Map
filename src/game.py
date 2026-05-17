import asyncio
import pygame

from src import config as C
from src.constants import (
    SCREEN_TITLE, SCREEN_ROUTE, SCREEN_STOP,
    SCREEN_JOURNAL, SCREEN_MAP, SCREEN_FEEDBACK, SCREEN_FINAL,
)
from src.state import GameState
from src.data_loader import load_stops, load_categories, load_game_text
from src.audio import AudioManager
from src.screens.title_screen import TitleScreen
from src.screens.route_screen import RouteScreen
from src.screens.stop_screen import StopScreen
from src.screens.journal_screen import JournalScreen
from src.screens.systems_map_screen import SystemsMapScreen
from src.screens.feedback_screen import FeedbackScreen
from src.screens.final_screen import FinalScreen


class Game:
    def __init__(self):
        self.stops      = load_stops()
        self.categories = load_categories()
        self.text       = load_game_text()

        self.state = GameState(total_stops=len(self.stops))
        self.audio = AudioManager()

        self.screen_map = {
            SCREEN_TITLE:    TitleScreen(self),
            SCREEN_ROUTE:    RouteScreen(self),
            SCREEN_STOP:     StopScreen(self),
            SCREEN_JOURNAL:  JournalScreen(self),
            SCREEN_MAP:      SystemsMapScreen(self),
            SCREEN_FEEDBACK: FeedbackScreen(self),
            SCREEN_FINAL:    FinalScreen(self),
        }

        self._active_screen_id: str = ""
        self._surface: pygame.Surface = None
        self._clock: pygame.time.Clock = None

    async def run(self):
        self._surface = pygame.display.set_mode(
            (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(C.WINDOW_TITLE)
        self._clock = pygame.time.Clock()

        # Enter the first screen
        self._switch_to(SCREEN_TITLE)

        while True:
            dt = self._clock.tick(C.FPS) / 1000.0

            # Check for screen transition
            desired = self.state.current_screen
            if desired != self._active_screen_id:
                self._switch_to(desired)

            active = self.screen_map[self._active_screen_id]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.audio.toggle_mute()
                active.handle_event(event)

            active.update(dt)
            active.draw(self._surface)
            pygame.display.flip()

            # Required for pygbag compatibility
            await asyncio.sleep(0)

    def _switch_to(self, screen_id: str):
        if self._active_screen_id and self._active_screen_id in self.screen_map:
            self.screen_map[self._active_screen_id].on_exit()
        self._active_screen_id = screen_id
        self.screen_map[screen_id].on_enter()

    # ------------------------------------------------------------------
    # Convenience helpers called by screens
    # ------------------------------------------------------------------

    def open_stop(self, stop_id: int):
        stop = next((s for s in self.stops if s.id == stop_id), None)
        if stop is None:
            return
        # Switch first (triggers on_enter), then set_stop so on_enter can't overwrite it
        self.state.previous_screen = self.state.current_screen
        self.state.current_screen = SCREEN_STOP
        self._switch_to(SCREEN_STOP)
        self.screen_map[SCREEN_STOP].set_stop(stop)
