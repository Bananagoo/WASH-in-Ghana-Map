from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class RoutePosition:
    x: int
    y: int


@dataclass
class Stop:
    id: int
    title: str
    token: str
    icon_label: str
    emoji: str
    main_categories: List[str]
    primary_category: str
    purpose: str
    key_learning: str
    course_concept: str
    reflection: str
    route_position: RoutePosition
    # Optional enrichment fields (safe to leave out of JSON)
    image: str = ""
    secondary_image: str = ""
    token_image: str = ""
    visual_theme: str = "default"
    wash_focus: str = ""
    reading_tie: str = ""
    what_happened: str = ""
    systems_insight: str = ""


@dataclass
class Category:
    id: str
    name: str
    description: str
    color: Tuple[int, int, int]
    map_position: RoutePosition


@dataclass
class GameText:
    title: str
    subtitle: str
    course: str
    tutorial: List[str]
    route_instructions: str
    stop_collect_button: str
    stop_back_button: str
    journal_title: str
    journal_empty: str
    journal_back_button: str
    map_title: str
    map_instructions: str
    map_select_prompt: str
    map_token_placed: str
    map_finish_button: str
    map_back_button: str
    feedback_title: str
    feedback_intro: str
    feedback_score_label: str
    feedback_correct_label: str
    feedback_token_column: str
    feedback_your_column: str
    feedback_key_column: str
    feedback_next_button: str
    feedback_restart_button: str
    final_title: str
    final_takeaway: List[str]
    final_credit: str
    final_restart_button: str
    feedback_messages: dict
