from __future__ import annotations

import argparse
from pathlib import Path
import sys

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
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--preview", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    batch_specs = _batch_specs(args.batch)
    pygame.init()
    atlas = _load_atlas(args.atlas, COLUMNS, ROWS, CELL_SIZE)
    key = _parse_hex_color(args.chroma_key)
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


if __name__ == "__main__":
    raise SystemExit(main())
