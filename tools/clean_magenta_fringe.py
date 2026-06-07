from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents_survival_reborn.constants import DOCS_DIR, SPRITE_DIR
from agents_survival_reborn.data import sprite_specs
from sprite_chroma import clean_sprite_surface


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remove magenta chroma-key fringes from sliced sprite PNGs.")
    parser.add_argument("--sprites", type=Path, default=SPRITE_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pygame.init()
    specs = sprite_specs()
    cleaned: list[tuple[str, int, int, int]] = []
    missing: list[str] = []
    for spec in specs:
        path = args.sprites / spec.path
        if not path.exists():
            missing.append(spec.sprite_id)
            continue
        image = pygame.image.load(str(path))
        cleaned_image, stats = clean_sprite_surface(image, preserve_opaque=spec.kind == "terrain")
        if stats.removed_pixels or stats.replaced_pixels:
            cleaned.append((spec.sprite_id, stats.removed_pixels, stats.replaced_pixels, stats.remaining_magenta_pixels))
            if not args.dry_run:
                pygame.image.save(cleaned_image, str(path))
    pygame.quit()
    _write_report(cleaned, missing, args.dry_run)
    print(f"Sprites cleaned: {len(cleaned)}")
    print(f"Missing sprites: {len(missing)}")
    if args.dry_run:
        print("Dry run only; no files were changed.")
    return 0


def _write_report(cleaned: list[tuple[str, int, int, int]], missing: list[str], dry_run: bool) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Magenta Fringe Cleanup",
        "",
        f"Mode: {'dry-run' if dry_run else 'write'}",
        "",
        "| Sprite | Transparent Pixels Removed | Opaque Pixels Replaced | Remaining Magenta-Like Pixels |",
        "| --- | ---: | ---: | ---: |",
    ]
    for sprite_id, removed, replaced, remaining in cleaned:
        lines.append(f"| `{sprite_id}` | {removed} | {replaced} | {remaining} |")
    if missing:
        lines.extend(["", "## Missing Sprites", ""])
        lines.extend(f"- `{sprite_id}`" for sprite_id in missing)
    (DOCS_DIR / "magenta_cleanup.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
