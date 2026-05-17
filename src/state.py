from typing import Dict, List, Optional, Set
from src.constants import SCREEN_TITLE


class GameState:
    def __init__(self, total_stops: int):
        self.total_stops = total_stops
        self.reset()

    def reset(self):
        self.current_screen: str = SCREEN_TITLE
        self.previous_screen: Optional[str] = None

        self.current_stop_index: int = 0          # 0-based index into stops list
        self.completed_stop_ids: Set[int] = set() # stop.id values that are done
        self.collected_tokens: List[str] = []     # token names in order collected

        self.selected_token_index: Optional[int] = None  # for systems map
        self.map_placements: Dict[str, str] = {}  # token_name -> category_id
        self.score: Optional[int] = None
        self.score_pct: Optional[float] = None

        # WASH Systems Map final activity
        self.wash_map_placements: Dict[str, str] = {}  # token_name -> category_id
        self.wash_similarity_score: Optional[int] = None

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def go_to(self, screen: str):
        self.previous_screen = self.current_screen
        self.current_screen = screen

    def go_back(self):
        if self.previous_screen:
            self.current_screen, self.previous_screen = (
                self.previous_screen, self.current_screen
            )

    # ------------------------------------------------------------------
    # Stop progression
    # ------------------------------------------------------------------

    def mark_stop_complete(self, stop_id: int, token_name: str):
        self.completed_stop_ids.add(stop_id)
        if token_name not in self.collected_tokens:
            self.collected_tokens.append(token_name)
        # Advance current pointer past completed stops
        while (self.current_stop_index < self.total_stops and
               (self.current_stop_index + 1) in self.completed_stop_ids):
            self.current_stop_index += 1
        # Advance to next uncompleted stop
        if stop_id == self.current_stop_index + 1:
            self.current_stop_index = len(self.completed_stop_ids)

    def is_stop_completed(self, stop_id: int) -> bool:
        return stop_id in self.completed_stop_ids

    def is_stop_unlocked(self, stop_id: int) -> bool:
        return stop_id == self.current_unlocked_id()

    def current_unlocked_id(self) -> int:
        return len(self.completed_stop_ids) + 1

    def all_stops_complete(self) -> bool:
        return len(self.completed_stop_ids) >= self.total_stops

    def complete_all_stops(self, stops):
        for stop in stops:
            self.completed_stop_ids.add(stop.id)
            if stop.token not in self.collected_tokens:
                self.collected_tokens.append(stop.token)
        self.current_stop_index = len(stops)

    # ------------------------------------------------------------------
    # Systems map
    # ------------------------------------------------------------------

    def place_token(self, token_name: str, category_id: str):
        self.map_placements[token_name] = category_id

    def all_tokens_placed(self) -> bool:
        return len(self.map_placements) >= len(self.collected_tokens)

    def calculate_score(self, stops, categories_by_id: Dict[str, object]):
        correct = 0
        for stop in stops:
            placed = self.map_placements.get(stop.token)
            if placed and placed == _category_id_for_name(
                stop.primary_category, categories_by_id
            ):
                correct += 1
        self.score = correct
        total = len(stops)
        self.score_pct = round(correct / total * 100) if total else 0


def _category_id_for_name(name: str, categories_by_id: Dict[str, object]) -> str:
    for cat_id, cat in categories_by_id.items():
        if cat.name.lower() == name.lower():
            return cat_id
    return ""
