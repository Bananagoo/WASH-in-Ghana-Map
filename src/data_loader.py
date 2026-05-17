import json
import os
from typing import List

from src.models import Stop, Category, GameText, RoutePosition


def _load_json(filename: str) -> object:
    # Use path relative to cwd (where main.py lives) — works locally and in pygbag/WASM
    path = os.path.join("data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_stops() -> List[Stop]:
    raw = _load_json("stops.json")
    stops = []
    for s in raw:
        pos = RoutePosition(**s["route_position"])
        stops.append(Stop(
            id=s["id"],
            title=s["title"],
            token=s["token"],
            icon_label=s["icon_label"],
            emoji=s.get("emoji", ""),
            main_categories=s["main_categories"],
            primary_category=s["primary_category"],
            purpose=s["purpose"],
            key_learning=s["key_learning"],
            course_concept=s["course_concept"],
            reflection=s["reflection"],
            route_position=pos,
            image=s.get("image", ""),
            secondary_image=s.get("secondary_image", ""),
            token_image=s.get("token_image", ""),
            visual_theme=s.get("visual_theme", "default"),
            wash_focus=s.get("wash_focus", ""),
            reading_tie=s.get("reading_tie", ""),
            what_happened=s.get("what_happened", ""),
            systems_insight=s.get("systems_insight", ""),
            references=s.get("references", []),
        ))
    return stops


def load_categories() -> List[Category]:
    raw = _load_json("categories.json")
    categories = []
    for c in raw:
        pos = RoutePosition(**c["map_position"])
        categories.append(Category(
            id=c["id"],
            name=c["name"],
            description=c["description"],
            color=tuple(c["color"]),
            map_position=pos,
        ))
    return categories


def load_game_text() -> GameText:
    raw = _load_json("game_text.json")
    return GameText(**raw)
