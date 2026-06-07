from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pygame

from agents_survival_reborn.constants import SPRITE_DIR
from agents_survival_reborn.data import SpriteSpec, sprite_specs


COLORS = {
    "terrain": (84, 142, 92),
    "feature": (126, 112, 82),
    "agent": (108, 151, 205),
    "item": (174, 142, 82),
    "ui": (98, 116, 140),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write simple transparent PNG placeholders for missing sprite files.")
    parser.add_argument("--replace-existing", action="store_true", help="Overwrite existing sprite PNGs too.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pygame.init()
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped = 0
    for spec in sprite_specs():
        target = SPRITE_DIR / spec.path
        if target.exists() and not args.replace_existing:
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        surface = make_placeholder(spec)
        pygame.image.save(surface, str(target))
        written.append(spec.sprite_id)
    pygame.quit()
    print(f"written={len(written)} skipped={skipped}")
    for sprite_id in written[:40]:
        print(sprite_id)
    if len(written) > 40:
        print(f"... {len(written) - 40} more")
    return 0


def make_placeholder(spec: SpriteSpec) -> pygame.Surface:
    width, height = spec.size
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    base = COLORS.get(spec.kind, (120, 120, 120))
    if spec.kind == "terrain":
        surface.fill(base)
        for y in range(0, height, 7):
            pygame.draw.line(surface, lighten(base, 32), (0, y), (width, y + 4), 1)
        return surface
    rect = pygame.Rect(2, 2, width - 4, height - 4)
    pygame.draw.rect(surface, (*base, 230), rect, border_radius=4)
    pygame.draw.rect(surface, (18, 22, 27, 255), rect, 2, border_radius=4)
    if spec.kind == "agent":
        pygame.draw.circle(surface, lighten(base, 45), (width // 2, 9), 5)
        pygame.draw.rect(surface, darken(base, 20), (width // 2 - 6, 15, 12, height - 20), border_radius=4)
    elif spec.kind == "item":
        pygame.draw.circle(surface, lighten(base, 36), (width // 2, height // 2), min(width, height) // 4)
    elif spec.kind == "feature":
        pygame.draw.polygon(surface, lighten(base, 38), [(width // 2, 5), (width - 6, height - 7), (6, height - 7)])
    else:
        pygame.draw.circle(surface, lighten(base, 48), (width // 2, height // 2), min(width, height) // 3, 2)
    return surface


def lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, channel + amount) for channel in color)


def darken(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(max(0, channel - amount) for channel in color)


if __name__ == "__main__":
    raise SystemExit(main())
