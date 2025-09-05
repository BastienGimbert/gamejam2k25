import os
from typing import Dict, List, Optional, Tuple

import pygame

from classes.utils import decouper_sprite


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _token_direction_from_filename(name: str) -> Optional[str]:
    base = os.path.splitext(os.path.basename(name))[0]
    tok = base.split("_", 1)[0].upper()
    if tok in {"D", "S", "U", "DS", "US"}:
        return tok
    return None


class DirectionalAnimator:
    def __init__(
        self,
        base_person_path: str,
        frames_per_state: Optional[Dict[str, int]] = None,
        durations: Optional[Dict[str, float]] = None,
        loop_states: Tuple[str, ...] = ("Idle",),
        side_faces_right: bool = True,
        desired_compound_total: Optional[int] = None,
    ) -> None:
        self.base_person_path = (
            base_person_path
            if os.path.isabs(base_person_path)
            else os.path.join(_project_root(), base_person_path)
        )
        self.frames_per_state = frames_per_state or {
            "Idle": 4,
            "Preattack": 1,
            "Attack": 6,
        }
        self.state_order: List[str] = ["Idle", "Preattack", "Attack"]
        self.durations = durations or {"Idle": 0.18, "Preattack": 0.10, "Attack": 0.10}
        self.loop_states = set(loop_states)
        self.side_faces_right = side_faces_right
        self.desired_compound_total = desired_compound_total

        self.directions: Tuple[str, ...] = self._discover_directions()
        if not self.directions:
            self.directions = ("D", "S", "U")

        self.frames: Dict[Tuple[str, str], List[pygame.Surface]] = {}
        self._has_state_sheet: Dict[str, bool] = {}

        self.state = "Idle"
        self.direction = "S"
        self.flip_x = False
        self.index = 0
        self.timer = 0.0

        self._load_all()

    def _discover_directions(self) -> Tuple[str, ...]:
        dirs = []
        if os.path.isdir(self.base_person_path):
            for fn in os.listdir(self.base_person_path):
                if not fn.lower().endswith(".png"):
                    continue
                tok = _token_direction_from_filename(fn)
                if tok and tok not in dirs:
                    dirs.append(tok)
        priority = ["D", "S", "U", "DS", "US"]
        dirs.sort(key=lambda d: priority.index(d) if d in priority else 99)
        return tuple(dirs)

    def _load_img(self, path: str) -> Optional[pygame.Surface]:
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        return None

    def _count_if_divisible(self, width: int, preferred: int) -> int:
        if preferred and preferred >= 2 and width % preferred == 0:
            return preferred
        for n in (6, 8, 10, 12, 4, 5, 7, 9):
            if width % n == 0:
                return n
        for n in range(2, 41):
            if width % n == 0:
                return n
        return 1

    def _load_for_direction(self, direction: str) -> Dict[str, List[pygame.Surface]]:
        out: Dict[str, List[pygame.Surface]] = {}
        has_state = False
        for s in self.state_order:
            if os.path.exists(
                os.path.join(self.base_person_path, f"{direction}_{s}.png")
            ):
                has_state = True
                break
        self._has_state_sheet[direction] = has_state

        if has_state:
            for s in self.state_order:
                p = os.path.join(self.base_person_path, f"{direction}_{s}.png")
                sheet = self._load_img(p)
                if sheet is None:
                    surf = pygame.Surface((1, 1), pygame.SRCALPHA)
                    surf.fill((0, 0, 0, 0))
                    out[s] = [surf]
                else:
                    n = self.frames_per_state.get(s, 1)
                    out[s] = decouper_sprite(sheet, n, horizontal=True, copy=True)
            return out

        p_single = os.path.join(self.base_person_path, f"{direction}.png")
        sheet = self._load_img(p_single)
        if sheet is None:
            surf = pygame.Surface((1, 1), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            return {"Idle": [surf], "Preattack": [surf], "Attack": [surf]}

        target_n = self.desired_compound_total or 6
        n = self._count_if_divisible(sheet.get_width(), target_n)
        frames = decouper_sprite(sheet, n, horizontal=True, copy=True)

        if n >= 6:
            idle = [frames[0]]
            pre = [frames[0]]
            atk = frames
        else:
            idle = [frames[0]]
            pre = [frames[0]]
            atk = frames

        out["Idle"] = idle
        out["Preattack"] = pre
        out["Attack"] = atk
        return out

    def _load_all(self) -> None:
        for d in self.directions:
            packs = self._load_for_direction(d)
            for s in self.state_order:
                self.frames[(d, s)] = packs.get(s, packs.get("Idle", []))

    def start(
        self, state: str, direction: Optional[str] = None, flip_x: Optional[bool] = None
    ) -> None:
        if direction is not None:
            self.direction = direction
        if flip_x is not None:
            self.flip_x = flip_x if self.direction in ("S", "DS", "US") else False
        self.state = state
        self.index = 0
        self.timer = 0.0

    def set_orientation(self, direction: str, flip_x: bool) -> None:
        self.direction = direction
        self.flip_x = flip_x if direction in ("S", "DS", "US") else False

    def update(self, dt: float) -> bool:
        frames = self.frames.get((self.direction, self.state), [])
        if not frames:
            return False
        self.timer += max(0.0, dt)
        finished = False
        dur = self.durations.get(self.state, 0.1)
        while self.timer >= dur:
            self.timer -= dur
            self.index += 1
            if self.index >= len(frames):
                if self.state in self.loop_states:
                    self.index = 0
                else:
                    self.index = len(frames) - 1
                    finished = True
                    break
        return finished

    def draw(self, surface: pygame.Surface, center_x: int, base_y: int) -> None:
        frames = self.frames.get((self.direction, self.state), [])
        if not frames:
            return
        img = frames[self.index]
        if self.flip_x:
            img = pygame.transform.flip(img, True, False)
        rect = img.get_rect()
        rect.midbottom = (center_x, base_y)
        surface.blit(img, rect)

    def best_orientation(
        self, src_x: float, src_y: float, dst_x: float, dst_y: float
    ) -> Tuple[str, bool]:
        dx = float(dst_x - src_x)
        dy = float(dst_y - src_y)
        ax, ay = abs(dx), abs(dy)
        has_diag = ("DS" in self.directions) or ("US" in self.directions)

        if has_diag and min(ax, ay) > 0 and max(ax, ay) / min(ax, ay) <= 1.75:
            d = "DS" if dy >= 0 else "US"
            flip = dx < 0 if self.side_faces_right else dx > 0
            return d if d in self.directions else ("D" if dy > 0 else "U"), flip

        if ax >= ay:
            flip = dx < 0 if self.side_faces_right else dx > 0
            return "S", flip
        return ("D", False) if dy > 0 else ("U", False)
