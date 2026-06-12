from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents_survival_reborn.constants import GENERATED_DIR, SPRITE_DIR
from agents_survival_reborn.data import SpriteSpec, sprite_specs
from import_sprite_atlas import _load_atlas, _make_sprite, _parse_hex_color, _slice_cell
from make_sprite_batch_prompts import BATCHES, CELL_SIZE, COLUMNS, ROWS, _select_specs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slice one 8x8 ChatGPT batch atlas into the matching game sprites.")
    parser.add_argument("batch", choices=[batch[0] for batch in BATCHES], help="Batch name from docs/sprite_batch_prompts.md.")
    parser.add_argument("atlas", type=Path, help="Path to the generated PNG for this batch.")
    parser.add_argument("--out", type=Path, default=SPRITE_DIR)
    parser.add_argument("--chroma-key", default="ff00ff")
    parser.add_argument("--tolerance", type=int, default=34)
    parser.add_argument("--grid-mode", choices=("detect", "exact"), default="detect", help="detect finds ChatGPT's inner cell grid; exact uses the full 8x8 image.")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--preview", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    batch_specs = _batch_specs(args.batch)
    pygame.init()
    key = _parse_hex_color(args.chroma_key)
    if args.grid_mode == "detect":
        atlas = _load_original_atlas(args.atlas)
        cell_rects = _detect_cell_rects(atlas, key, args.tolerance, len(batch_specs))
    else:
        atlas = _load_atlas(args.atlas, COLUMNS, ROWS, CELL_SIZE)
        cell_rects = [_exact_cell_rect(index) for index in range(len(batch_specs))]
    args.out.mkdir(parents=True, exist_ok=True)
    if args.preview:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        pygame.image.save(atlas, str(GENERATED_DIR / f"normalized_{args.batch}.png"))

    written = 0
    skipped = 0
    for index, spec in enumerate(batch_specs):
        target = args.out / spec.path
        if target.exists() and not args.replace_existing:
            skipped += 1
            continue
        if args.grid_mode == "detect":
            cell = atlas.subsurface(cell_rects[index]).copy()
        else:
            cell = _slice_cell(atlas, index, COLUMNS, CELL_SIZE)
        sprite = _make_sprite(cell, spec, key, args.tolerance)
        pygame.image.save(sprite, str(target))
        written += 1

    pygame.quit()
    print(f"Batch: {args.batch}")
    print(f"Sprites written: {written}")
    print(f"Sprites skipped: {skipped}")
    print(f"Output: {args.out}")
    return 0


def _batch_specs(batch_name: str) -> list[SpriteSpec]:
    all_specs = sprite_specs()
    for name, _title, selectors in BATCHES:
        if name == batch_name:
            return _select_specs(all_specs, selectors)
    raise SystemExit(f"Unknown batch: {batch_name}")


def _load_original_atlas(path: Path) -> pygame.Surface:
    if not path.exists():
        raise SystemExit(f"Atlas not found: {path}")
    atlas = pygame.image.load(str(path))
    return atlas.convert_alpha() if pygame.display.get_surface() else atlas.copy()


def _detect_cell_rects(atlas: pygame.Surface, key: tuple[int, int, int], tolerance: int, sprite_count: int) -> list[pygame.Rect]:
    rows_needed = (sprite_count + COLUMNS - 1) // COLUMNS
    x_segments = _detect_axis_segments(atlas, key, tolerance, axis="x", expected=COLUMNS)
    y_segments = _detect_axis_segments(atlas, key, tolerance, axis="y", expected=rows_needed)
    if len(x_segments) < COLUMNS:
        raise SystemExit(f"Could not detect {COLUMNS} atlas columns; detected {len(x_segments)}.")
    if len(y_segments) < rows_needed:
        raise SystemExit(f"Could not detect {rows_needed} filled atlas rows; detected {len(y_segments)}.")
    x_bounds = _bounds_from_segments(x_segments[:COLUMNS], 0, atlas.get_width())
    y_bounds = _bounds_from_segments(y_segments[:rows_needed], 0, atlas.get_height())
    rects: list[pygame.Rect] = []
    for index in range(sprite_count):
        col = index % COLUMNS
        row = index // COLUMNS
        left, right = x_bounds[col]
        top, bottom = y_bounds[row]
        rect = pygame.Rect(left, top, right - left, bottom - top)
        rects.append(rect)
    return rects


def _bounds_from_segments(segments: list[tuple[int, int]], low: int, high: int) -> list[tuple[int, int]]:
    centers = [(left + right) / 2 for left, right in segments]
    bounds: list[tuple[int, int]] = []
    for index, center in enumerate(centers):
        if index == 0:
            if len(centers) > 1:
                left = center - (centers[1] - center) / 2
            else:
                left = segments[index][0]
        else:
            left = (centers[index - 1] + center) / 2
        if index == len(centers) - 1:
            if len(centers) > 1:
                right = center + (center - centers[index - 1]) / 2
            else:
                right = segments[index][1]
        else:
            right = (center + centers[index + 1]) / 2
        bounds.append((max(low, int(round(left))), min(high, int(round(right)))))
    return bounds


def _detect_axis_segments(
    atlas: pygame.Surface,
    key: tuple[int, int, int],
    tolerance: int,
    *,
    axis: str,
    expected: int,
) -> list[tuple[int, int]]:
    rgb = pygame.surfarray.array3d(atlas).astype(np.int16)
    key_array = np.array(key, dtype=np.int16)
    distance = np.abs(rgb - key_array).max(axis=2)
    non_key = distance > tolerance
    projection = non_key.sum(axis=1 if axis == "x" else 0)
    threshold = max(5, int((atlas.get_height() if axis == "x" else atlas.get_width()) * 0.004))
    segments = _segments_from_projection(projection, threshold, min_width=8)
    if len(segments) > expected:
        segments = sorted(segments, key=lambda pair: pair[1] - pair[0], reverse=True)[:expected]
        segments.sort()
    return segments


def _segments_from_projection(projection: np.ndarray, threshold: int, *, min_width: int) -> list[tuple[int, int]]:
    segments: list[tuple[int, int]] = []
    in_segment = False
    start = 0
    for index, count in enumerate(projection):
        if count > threshold and not in_segment:
            start = index
            in_segment = True
        elif in_segment and count <= threshold:
            if index - start >= min_width:
                segments.append((start, index))
            in_segment = False
    if in_segment and len(projection) - start >= min_width:
        segments.append((start, len(projection)))
    return segments


def _exact_cell_rect(index: int) -> pygame.Rect:
    col = index % COLUMNS
    row = index // COLUMNS
    return pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)


if __name__ == "__main__":
    raise SystemExit(main())
