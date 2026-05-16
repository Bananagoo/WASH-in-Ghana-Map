"""
Walkable path mask for player movement on the route screen.

The mask is built once from the Bézier curve and stop positions.
Each curve point carries metadata about which stop-pair segment it belongs to,
so walkability can be gated by game progression.

Coordinate system: all positions are in SCREEN space (y=0 at top of window).
"""
import math

PATH_HALF = 15   # walkable half-width in pixels (slightly inside visual path)
CLEAR_R   = 22   # walkable clearing radius at each stop marker


class PathMask:
    """
    Lightweight path-collision helper.

    Build once, then call is_walkable() every frame.
    """

    def __init__(self):
        # List of (screen_x, screen_y, min_unlocked_id_needed)
        # A point is walkable when current_unlocked_id >= min_unlocked_id_needed.
        self._pts: list = []

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, stops: list, curve_screen: list, seg_lengths: list):
        """
        stops        : list of Stop objects (in order, id 1..N)
        curve_screen : list of (x, y) in screen coords from OverworldRenderer
        seg_lengths  : list of ints — number of curve points per segment
                       (segment i connects stops[i] → stops[i+1])
        """
        self._pts = []

        # Stop clearings — walkable once that stop is the current unlocked stop
        for stop in stops:
            cx = stop.route_position.x
            cy = stop.route_position.y + 30
            needed = stop.id          # unlock stop N to stand in its clearing
            for angle_i in range(16):
                angle = angle_i * math.pi * 2 / 16
                for r in range(4, CLEAR_R + 1, 4):
                    px = cx + math.cos(angle) * r
                    py = cy + math.sin(angle) * r
                    self._pts.append((px, py, needed))
            self._pts.append((float(cx), float(cy), needed))

        # Path segments
        # Segment i (0-indexed) goes from stop i+1 to stop i+2.
        # It is walkable when current_unlocked_id >= i+2
        # (i.e. the destination stop is at least the current unlocked stop).
        cursor = 1  # first curve point is the start of the first segment
        for seg_idx, seg_len in enumerate(seg_lengths):
            needed = seg_idx + 2       # destination stop ID of this segment
            for j in range(seg_len):
                i = cursor + j
                if i < len(curve_screen):
                    px, py = curve_screen[i]
                    self._pts.append((float(px), float(py), needed))
            cursor += seg_len

    # ── Query ─────────────────────────────────────────────────────────────────

    def is_walkable(self, sx: float, sy: float, current_unlocked_id: int) -> bool:
        """Return True if screen position (sx, sy) is in the walkable area."""
        for px, py, needed in self._pts:
            if needed > current_unlocked_id:
                continue
            if math.hypot(sx - px, sy - py) <= PATH_HALF:
                return True
        return False
