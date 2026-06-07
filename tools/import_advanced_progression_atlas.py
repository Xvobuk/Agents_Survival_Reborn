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


VISUAL_MAPPING: tuple[tuple[str, ...], ...] = (
    ("feature_wolf",),
    ("feature_bear",),
    ("feature_snake",),
    ("feature_potion_stand", "item_potion_stand"),
    ("item_hide",),
    ("item_leather",),
    ("item_venom_sac",),
    ("item_copper_axe",),
    ("item_copper_sword",),
    ("item_iron_sword",),
    ("skip_leather_alt",),
    ("skip_ingot_alt",),
    ("item_stone_knife",),
    ("item_gold_ring",),
    ("item_diamond_ring",),
    ("item_iron_axe",),
    ("skip_knife_alt",),
    ("item_iron_chestplate",),
    ("item_leather_tunic",),
    ("item_leather_boots",),
    ("item_iron_helmet",),
    ("item_leather_cap",),
    ("skip_iron_armor_alt",),
    ("item_iron_boots",),
    ("item_healing_potion",),
    ("skip_red_potion_alt",),
    ("item_stamina_potion",),
    ("skip_iron_boots_alt",),
    ("item_cactus_spine",),
    ("ui_chat",),
)


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
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def center_x(self) -> float:
        return (self.left + self.right) / 2

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.left, self.top, self.width, self.height)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import the advanced progression ChatGPT atlas.")
    parser.add_argument("atlas", type=Path, help="Path to the generated transparent atlas PNG.")
    parser.add_argument("--out", type=Path, default=SPRITE_DIR, help="Output sprite directory.")
    parser.add_argument("--preview", action="store_true", help="Write contact-sheet and detection previews.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write sprites.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.atlas.exists():
        raise SystemExit(f"Atlas not found: {args.atlas}")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    atlas = pygame.image.load(str(args.atlas)).convert_alpha()
    components = _select_components(_alpha_components(atlas))
    if len(components) != len(VISUAL_MAPPING):
        raise SystemExit(f"Expected {len(VISUAL_MAPPING)} visible components, detected {len(components)}.")

    args.out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[str] = []
    previews: list[tuple[str, pygame.Surface]] = []
    for component, sprite_ids in zip(components, VISUAL_MAPPING, strict=True):
        sprite = _fit_centered(atlas.subsurface(_padded_rect(component.rect(), atlas.get_size(), 14)).copy(), (32, 32))
        for sprite_id in sprite_ids:
            if sprite_id.startswith("skip_"):
                skipped.append(sprite_id)
                continue
            if not args.dry_run:
                pygame.image.save(sprite, str(args.out / f"{sprite_id}.png"))
            written.append(sprite_id)
            previews.append((sprite_id, sprite))

    if args.preview:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        pygame.image.save(_make_contact_sheet(previews), str(GENERATED_DIR / "advanced_progression_import_contact.png"))
        pygame.image.save(_draw_detection_preview(atlas, components), str(GENERATED_DIR / "advanced_progression_detected.png"))

    pygame.quit()
    print(f"Sprites written: {len(written)}")
    for sprite_id in written:
        print(f"- {sprite_id}")
    if skipped:
        print("Skipped atlas variants:")
        for sprite_id in skipped:
            print(f"- {sprite_id}")
    if args.preview:
        print(f"Preview: {GENERATED_DIR / 'advanced_progression_import_contact.png'}")
    return 0


def _alpha_components(surface: pygame.Surface) -> list[Component]:
    alpha = pygame.surfarray.array_alpha(surface)
    visible = (alpha.T > 12).astype(bool)
    height, width = visible.shape
    visited = np.zeros_like(visible, dtype=bool)
    components: list[Component] = []
    for y in range(height):
        for x in range(width):
            if visited[y, x] or not visible[y, x]:
                continue
            components.append(_flood_fill(visible, visited, x, y))
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


def _select_components(components: list[Component]) -> list[Component]:
    useful = [
        component
        for component in components
        if component.area >= 500 and component.width >= 18 and component.height >= 18
    ]
    useful = sorted(useful, key=lambda component: component.area, reverse=True)[: len(VISUAL_MAPPING)]
    rows: list[list[Component]] = []
    for component in sorted(useful, key=lambda component: component.center_y):
        for row in rows:
            row_center = sum(entry.center_y for entry in row) / len(row)
            if abs(component.center_y - row_center) < 70:
                row.append(component)
                break
        else:
            rows.append([component])
    rows = sorted(rows, key=lambda row: sum(entry.center_y for entry in row) / len(row))
    ordered: list[Component] = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda component: component.center_x))
    return ordered


def _padded_rect(rect: pygame.Rect, size: tuple[int, int], padding: int) -> pygame.Rect:
    width, height = size
    left = max(0, rect.left - padding)
    top = max(0, rect.top - padding)
    right = min(width, rect.right + padding)
    bottom = min(height, rect.bottom + padding)
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


def _make_contact_sheet(entries: list[tuple[str, pygame.Surface]]) -> pygame.Surface:
    cell = 48
    columns = 7
    rows = (len(entries) + columns - 1) // columns
    sheet = pygame.Surface((columns * cell, rows * cell), pygame.SRCALPHA)
    for index, (_, sprite) in enumerate(entries):
        col = index % columns
        row = index // columns
        for y in range(row * cell, (row + 1) * cell, 8):
            for x in range(col * cell, (col + 1) * cell, 8):
                color = (54, 54, 54, 255) if ((x + y) // 8) % 2 else (30, 30, 30, 255)
                pygame.draw.rect(sheet, color, (x, y, 8, 8))
        sheet.blit(sprite, (col * cell + 8, row * cell + 8))
    return sheet


def _draw_detection_preview(source: pygame.Surface, components: list[Component]) -> pygame.Surface:
    preview = source.copy()
    font = pygame.font.Font(None, 42)
    for index, component in enumerate(components, start=1):
        pygame.draw.rect(preview, (255, 60, 60, 255), component.rect(), 4)
        label = font.render(str(index), True, (255, 255, 255))
        preview.blit(label, (component.left + 8, component.top + 8))
    return preview


if __name__ == "__main__":
    raise SystemExit(main())
