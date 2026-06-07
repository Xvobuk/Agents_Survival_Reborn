from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import os
from pathlib import Path
import sys

import numpy as np
import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents_survival_reborn.constants import GENERATED_DIR, SPRITE_DIR


@dataclass(frozen=True)
class Component:
    left: int
    top: int
    right: int
    bottom: int
    area: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def center(self) -> tuple[float, float]:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)

    @property
    def solidity(self) -> float:
        return self.area / max(1, self.width * self.height)


BUILDING_MAPPING = (
    # First row: clean top-down floors and full-height walls.
    ("item_wooden_floor", "item_wooden_floor.png", "tile"),
    ("item_stone_floor", "item_stone_floor.png", "tile"),
    ("feature_wooden_wall", "feature_wooden_wall.png", "object"),
    ("feature_stone_wall", "feature_stone_wall.png", "object"),
    # Second row includes a usable door sprite.
    ("skip_wood_floor_alt", "", "object"),
    ("skip_stone_floor_alt", "", "object"),
    ("feature_wooden_door", "feature_wooden_door.png", "object"),
    ("skip_stone_wall_alt", "", "object"),
    # Third row: compact icons for inventory wall items.
    ("skip_wood_floor_iso", "", "object"),
    ("skip_stone_floor_iso", "", "object"),
    ("item_wooden_wall", "item_wooden_wall.png", "object"),
    ("item_stone_wall", "item_stone_wall.png", "object"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-slice the transparent ChatGPT building atlas into game-ready 32x32 sprites."
    )
    parser.add_argument("atlas", type=Path, help="Path to the transparent building atlas PNG.")
    parser.add_argument("--out", type=Path, default=SPRITE_DIR, help="Output sprite directory.")
    parser.add_argument("--alpha-threshold", type=int, default=18, help="Minimum alpha treated as visible.")
    parser.add_argument("--min-area", type=int, default=900, help="Minimum connected visible pixels per sprite.")
    parser.add_argument("--padding", type=int, default=14, help="Pixels of source padding around each detected sprite.")
    parser.add_argument("--preview", action="store_true", help="Save a debug preview with detected boxes.")
    parser.add_argument("--dry-run", action="store_true", help="Detect and report sprites without writing PNGs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.atlas.exists():
        raise SystemExit(f"Atlas not found: {args.atlas}")

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    source = pygame.image.load(str(args.atlas)).convert_alpha()
    components = _detect_components(source, args.alpha_threshold, args.min_area)
    selected = _select_sprite_components(components)
    if len(selected) != len(BUILDING_MAPPING):
        raise SystemExit(f"Expected 12 building sprites, detected {len(selected)} usable components.")

    args.out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    for component, (sprite_id, filename, mode) in zip(selected, BUILDING_MAPPING, strict=True):
        if not filename:
            skipped.append(sprite_id)
            continue
        crop = _crop_component(source, component, args.padding)
        sprite = _make_sprite(crop, mode)
        if not args.dry_run:
            pygame.image.save(sprite, str(args.out / filename))
        written.append(sprite_id)

        if sprite_id == "feature_wooden_door":
            if not args.dry_run:
                pygame.image.save(sprite, str(args.out / "item_wooden_door.png"))
            written.append("item_wooden_door")

    if args.preview:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        preview = _draw_preview(source, selected)
        pygame.image.save(preview, str(GENERATED_DIR / "building_atlas_detected.png"))

    pygame.quit()
    print(f"Detected components: {len(selected)}")
    print(f"Sprites written: {len(written)}")
    for sprite_id in written:
        print(f"- {sprite_id}")
    if skipped:
        print("Skipped atlas variants:")
        for sprite_id in skipped:
            print(f"- {sprite_id}")
    if args.preview:
        print(f"Preview: {GENERATED_DIR / 'building_atlas_detected.png'}")
    return 0


def _detect_components(surface: pygame.Surface, alpha_threshold: int, min_area: int) -> list[Component]:
    alpha = pygame.surfarray.array_alpha(surface).T
    rgb = pygame.surfarray.array3d(surface).transpose(1, 0, 2)
    visible = alpha > alpha_threshold
    if visible.mean() > 0.90:
        # Fallback for images exported with an opaque black background despite the prompt.
        visible = rgb.max(axis=2) > 20

    height, width = visible.shape
    visited = np.zeros_like(visible, dtype=bool)
    components: list[Component] = []
    for y in range(height):
        for x in range(width):
            if visited[y, x] or not visible[y, x]:
                continue
            component = _flood_fill(visible, visited, x, y)
            if component.area < min_area:
                continue
            if component.width < 40 or component.height < 28:
                continue
            if component.solidity < 0.08:
                continue
            components.append(component)
    return components


def _flood_fill(visible: np.ndarray, visited: np.ndarray, start_x: int, start_y: int) -> Component:
    queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
    visited[start_y, start_x] = True
    min_x = max_x = start_x
    min_y = max_y = start_y
    area = 0
    height, width = visible.shape
    while queue:
        x, y = queue.popleft()
        area += 1
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
        for ny in range(max(0, y - 1), min(height, y + 2)):
            for nx in range(max(0, x - 1), min(width, x + 2)):
                if visited[ny, nx] or not visible[ny, nx]:
                    continue
                visited[ny, nx] = True
                queue.append((nx, ny))
    return Component(min_x, min_y, max_x + 1, max_y + 1, area)


def _select_sprite_components(components: list[Component]) -> list[Component]:
    candidates = sorted(components, key=lambda c: c.area, reverse=True)[:18]
    candidates = sorted(candidates[:12], key=lambda c: c.center[1])
    rows = [sorted(candidates[index : index + 4], key=lambda c: c.center[0]) for index in range(0, 12, 4)]
    return [component for row in rows for component in row]


def _crop_component(surface: pygame.Surface, component: Component, padding: int) -> pygame.Surface:
    rect = pygame.Rect(
        max(0, component.left - padding),
        max(0, component.top - padding),
        min(surface.get_width(), component.right + padding) - max(0, component.left - padding),
        min(surface.get_height(), component.bottom + padding) - max(0, component.top - padding),
    )
    return surface.subsurface(rect).copy()


def _make_sprite(source: pygame.Surface, mode: str) -> pygame.Surface:
    cleaned = _drop_near_transparent_pixels(source)
    bbox = _alpha_bbox(cleaned)
    if bbox is None:
        return pygame.Surface((32, 32), pygame.SRCALPHA)
    cropped = cleaned.subsurface(bbox).copy()
    if mode == "tile":
        return pygame.transform.smoothscale(cropped, (32, 32))
    return _fit_centered(cropped, (32, 32))


def _drop_near_transparent_pixels(surface: pygame.Surface) -> pygame.Surface:
    result = surface.copy()
    rgb = pygame.surfarray.array3d(result)
    alpha = pygame.surfarray.pixels_alpha(result)
    black_background = rgb.max(axis=2) <= 8
    alpha[black_background] = 0
    alpha[alpha < 14] = 0
    del alpha
    return result


def _alpha_bbox(surface: pygame.Surface) -> pygame.Rect | None:
    alpha = pygame.surfarray.array_alpha(surface)
    ys, xs = np.where(alpha.T > 12)
    if len(xs) == 0 or len(ys) == 0:
        return None
    left = int(xs.min())
    right = int(xs.max()) + 1
    top = int(ys.min())
    bottom = int(ys.max()) + 1
    return pygame.Rect(left, top, right - left, bottom - top)


def _fit_centered(source: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    width, height = source.get_size()
    target_w, target_h = size
    scale = min(target_w / max(1, width), target_h / max(1, height))
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    scaled = pygame.transform.smoothscale(source, new_size)
    result = pygame.Surface(size, pygame.SRCALPHA)
    result.blit(scaled, ((target_w - new_size[0]) // 2, (target_h - new_size[1]) // 2))
    return result


def _draw_preview(source: pygame.Surface, components: list[Component]) -> pygame.Surface:
    preview = source.copy()
    for index, component in enumerate(components, start=1):
        rect = pygame.Rect(component.left, component.top, component.width, component.height)
        pygame.draw.rect(preview, (255, 60, 60, 255), rect, 4)
        font = pygame.font.Font(None, 42)
        label = font.render(str(index), True, (255, 255, 255))
        preview.blit(label, (component.left + 8, component.top + 8))
    return preview


if __name__ == "__main__":
    raise SystemExit(main())
