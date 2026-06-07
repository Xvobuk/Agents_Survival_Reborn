from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents_survival_reborn.constants import DOCS_DIR, SPRITE_DIR
from agents_survival_reborn.data import AGENT_SPRITES, FEATURES, TERRAINS, SpriteSpec, sprite_specs
from sprite_chroma import clean_sprite_surface, remove_magenta_background


# Real cell centers from "ChatGPT Image 5 июн. 2026 г., 01_02_20.png".
COL_CENTERS = [75, 186, 298, 409, 520, 631, 742, 854, 966, 1078, 1190, 1302]
ROW_CENTERS = [89, 238, 385, 532, 669, 793, 919, 1053]
CROP_SIZE = (112, 150)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Salvage useful sprites from the imperfect ChatGPT atlas.")
    parser.add_argument("atlas", type=Path, help="Path to the downloaded ChatGPT PNG.")
    parser.add_argument("--out", type=Path, default=SPRITE_DIR)
    parser.add_argument("--replace-existing", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.atlas.exists():
        raise SystemExit(f"Atlas not found: {args.atlas}")
    pygame.init()
    atlas = pygame.image.load(str(args.atlas))
    args.out.mkdir(parents=True, exist_ok=True)
    specs = {spec.sprite_id: spec for spec in sprite_specs()}
    written: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for row, col, sprite_ids in _mapping():
        cell = _crop_cell(atlas, row, col)
        for sprite_id in sprite_ids:
            spec = specs.get(sprite_id)
            if spec is None:
                missing.append(sprite_id)
                continue
            target = args.out / spec.path
            if target.exists() and not args.replace_existing:
                skipped.append(sprite_id)
                continue
            sprite = _make_sprite(cell, spec)
            pygame.image.save(sprite, str(target))
            written.append(sprite_id)

    pygame.quit()
    _write_report(written, skipped, missing, args.atlas)
    print(f"Sprites written: {len(written)}")
    print(f"Sprites skipped: {len(skipped)}")
    if missing:
        print(f"Unknown sprite ids in mapping: {', '.join(missing)}")
    print(f"Output: {args.out}")
    return 0


def _mapping() -> list[tuple[int, int, tuple[str, ...]]]:
    entries: list[tuple[int, int, tuple[str, ...]]] = []

    terrain_sprites = [terrain.sprite for terrain in TERRAINS.values()]
    feature_sprites = [feature.sprite for feature in FEATURES.values()]
    for index, sprite_id in enumerate(terrain_sprites):
        entries.append(_cell_for_manifest_index(index, (sprite_id,)))
    for index, sprite_id in enumerate(feature_sprites, start=len(terrain_sprites)):
        entries.append(_cell_for_manifest_index(index, (sprite_id,)))

    entries.extend(
        [
            (4, 4, ("item_snow",)),
            (4, 5, ("item_workbench",)),
            (4, 6, ("item_campfire",)),
            (4, 7, ("item_kiln",)),
            (4, 8, ("item_soil",)),
            (4, 9, ("item_sand",)),
            (4, 10, ("item_clay_lump",)),
            (4, 11, ("item_stone",)),
            (4, 12, ("item_pebble",)),
            (5, 1, ("item_flint",)),
            (5, 2, ("item_coal",)),
            (5, 3, ("item_copper_ore",)),
            (5, 4, ("item_iron_ore",)),
            (5, 5, ("item_gold_ore",)),
            (5, 6, ("item_diamond",)),
            (5, 7, ("item_shell",)),
            (5, 8, ("item_glass",)),
            (5, 9, ("item_charcoal",)),
            (5, 10, ("item_birch_log", "item_oak_log", "item_pine_log", "item_fruit_log")),
            (5, 11, ("item_grass_fiber",)),
            (5, 12, ("item_cordage",)),
            (6, 1, ("item_stick",)),
            (6, 2, ("item_herb",)),
            (6, 3, ("item_bark",)),
            (6, 4, ("item_raw_meat",)),
            (6, 5, ("item_berries",)),
            (6, 6, ("item_blueberries",)),
            (6, 7, ("item_mushroom",)),
            (6, 8, ("item_raw_fish",)),
            (6, 9, ("item_cooked_meat",)),
            (6, 10, ("item_egg",)),
            (6, 11, ("item_bread",)),
            (6, 12, ("item_clay_pot",)),
            (7, 1, ("item_stone_axe",)),
            (7, 2, ("item_stone_pickaxe",)),
            (7, 3, ("item_stone_shovel",)),
            (7, 4, ("item_wooden_spear",)),
            (7, 5, ("item_bow",)),
            (7, 6, ("item_arrow",)),
            (7, 7, ("item_torch",)),
            (7, 8, ("item_wooden_shield",)),
            (7, 9, ("item_wooden_crate",)),
            (7, 10, ("item_wooden_door",)),
            (7, 11, ("item_bedroll",)),
            (7, 12, ("item_sack",)),
            (2, 8, ("item_seaweed",)),
            (2, 11, ("item_flower",)),
            (3, 2, ("item_reeds",)),
        ]
    )

    for index, sprite_id in enumerate(AGENT_SPRITES):
        entries.append((8, index + 1, (sprite_id,)))
    entries.extend(
        [
            (8, 9, ("ui_health",)),
            (8, 10, ("ui_energy",)),
            (8, 11, ("ui_unknown",)),
            (8, 12, ("ui_hunger",)),
        ]
    )
    return entries


def _cell_for_manifest_index(index: int, sprite_ids: tuple[str, ...]) -> tuple[int, int, tuple[str, ...]]:
    row = index // 12 + 1
    col = index % 12 + 1
    return row, col, sprite_ids


def _crop_cell(atlas: pygame.Surface, row: int, col: int) -> pygame.Surface:
    center_x = COL_CENTERS[col - 1]
    center_y = ROW_CENTERS[row - 1]
    width, height = CROP_SIZE
    left = max(0, round(center_x - width / 2))
    top = max(0, round(center_y - height / 2))
    right = min(atlas.get_width(), left + width)
    bottom = min(atlas.get_height(), top + height)
    return atlas.subsurface(pygame.Rect(left, top, right - left, bottom - top)).copy()


def _make_sprite(cell: pygame.Surface, spec: SpriteSpec) -> pygame.Surface:
    transparent, _ = remove_magenta_background(cell)
    bbox = _alpha_bbox(transparent)
    if bbox is None:
        return pygame.Surface(spec.size, pygame.SRCALPHA)
    cropped = transparent.subsurface(bbox).copy()
    if spec.kind == "terrain":
        sprite = _fit_opaque(cropped, spec.size)
        return clean_sprite_surface(sprite, preserve_opaque=True)[0]
    sprite = _fit_centered(cropped, spec.size)
    return clean_sprite_surface(sprite)[0]


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


def _fit_opaque(source: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    scaled = pygame.transform.smoothscale(source, size)
    rgb = pygame.surfarray.array3d(scaled)
    alpha = pygame.surfarray.array_alpha(scaled)
    visible = alpha > 12
    if visible.any():
        fill = rgb[visible].mean(axis=0).astype(np.uint8)
    else:
        fill = np.array([80, 120, 80], dtype=np.uint8)
    rgb[~visible] = fill
    result = pygame.Surface(size, pygame.SRCALPHA)
    pygame.surfarray.blit_array(result, rgb)
    pygame.surfarray.pixels_alpha(result)[:, :] = 255
    return result


def _write_report(written: list[str], skipped: list[str], missing: list[str], atlas: Path) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Salvaged ChatGPT Atlas",
        "",
        f"Source: `{atlas}`",
        "",
        f"Written: {len(written)}",
        f"Skipped: {len(skipped)}",
        f"Unknown mapping entries: {len(missing)}",
        "",
        "## Written Sprites",
        "",
    ]
    lines.extend(f"- `{sprite_id}`" for sprite_id in written)
    if skipped:
        lines.extend(["", "## Skipped Existing Sprites", ""])
        lines.extend(f"- `{sprite_id}`" for sprite_id in skipped)
    if missing:
        lines.extend(["", "## Unknown Sprite IDs", ""])
        lines.extend(f"- `{sprite_id}`" for sprite_id in missing)
    (DOCS_DIR / "salvaged_chatgpt_atlas.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
