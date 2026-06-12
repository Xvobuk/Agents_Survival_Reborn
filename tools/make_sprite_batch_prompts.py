from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents_survival_reborn.constants import DOCS_DIR
from agents_survival_reborn.data import SpriteSpec, sprite_specs


COLUMNS = 8
ROWS = 8
CELL_SIZE = 128

BATCHES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "01_terrain_and_nature_features",
        "Terrain tiles and natural gatherable world features",
        ("terrain", "feature:feature_cactus..feature_cave"),
    ),
    (
        "02_ore_plants_and_natural_deposits",
        "Ore veins, stone outcrops, special deposits, fiber plants, and natural resource features",
        ("feature:feature_coal_vein..feature_beehive",),
    ),
    (
        "03_structures_agents_and_ui",
        "Crafting stations, placed structures, machines, agents, and UI icons",
        (
            "feature_loom",
            "feature_pottery_wheel",
            "feature_signal_fire",
            "feature_wattle_wall",
            "feature_straw_roof",
            "feature_water_wheel",
            "feature_carpenter_table",
            "feature_cart",
            "feature_smelter",
            "feature_pump",
            "feature_windmill",
            "feature_steam_boiler",
            "feature_steam_hammer",
            "feature_jeweler_bench",
            "feature_oil_press",
            "feature_blast_furnace",
            "feature_tanning_table",
            "feature_stonecutting_table",
            "feature_forge_bellows",
            "agent",
            "ui",
        ),
    ),
    (
        "04_basic_items_food_and_building",
        "Basic resources, food, early tools, metal weapons, and gem-edged gear",
        ("item:item_soil..item_diamond_edged_sword",),
    ),
    (
        "05_building_armor_and_raw_resources",
        "Building pieces, storage, shelter, armor, jewelry, potions, stone tools, and raw resources",
        ("item:item_wooden_floor..item_resinous_wood",),
    ),
    (
        "06_plants_animal_parts_and_workshop_tools",
        "Plant materials, animal parts, metal components, processed materials, and workshop tools",
        ("item:item_oak_acorn..item_wooden_mallet",),
    ),
    (
        "07_metal_tools_weapons_fishing_farming",
        "Metal tools, weapons, ammunition, fishing gear, farming supplies, lighting, navigation, and food",
        ("item:item_copper_hammer..item_wicker_basket",),
    ),
    (
        "08_stations_building_medicine",
        "Station icons, storage, construction, machines, medicine, and treatment items",
        ("item:item_straw_roof..item_compress",),
    ),
)


def main() -> int:
    specs = sprite_specs()
    batches = [(name, title, _select_specs(specs, selectors)) for name, title, selectors in BATCHES]
    _validate_batches(specs, batches)
    text = _build_document(batches)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    target = DOCS_DIR / "sprite_batch_prompts.md"
    target.write_text(text, encoding="utf-8")
    print(target)
    return 0


def _select_specs(specs: list[SpriteSpec], selectors: Iterable[str]) -> list[SpriteSpec]:
    selected: list[SpriteSpec] = []
    by_id = {spec.sprite_id: spec for spec in specs}
    for selector in selectors:
        if ".." in selector:
            kind, bounds = selector.split(":", 1)
            start, end = bounds.split("..", 1)
            in_range = False
            for spec in specs:
                if spec.kind != kind:
                    continue
                if spec.sprite_id == start:
                    in_range = True
                if in_range:
                    selected.append(spec)
                if spec.sprite_id == end:
                    in_range = False
            continue
        if selector in {"terrain", "feature", "agent", "item", "ui"}:
            selected.extend(spec for spec in specs if spec.kind == selector)
            continue
        if selector in by_id:
            selected.append(by_id[selector])
            continue
        raise KeyError(f"Unknown sprite selector: {selector}")
    return selected


def _validate_batches(specs: list[SpriteSpec], batches: list[tuple[str, str, list[SpriteSpec]]]) -> None:
    seen: list[str] = []
    for name, _title, batch in batches:
        if len(batch) > COLUMNS * ROWS:
            raise SystemExit(f"{name} has {len(batch)} sprites, but an {COLUMNS}x{ROWS} atlas only has {COLUMNS * ROWS} cells.")
        seen.extend(spec.sprite_id for spec in batch)
    all_ids = [spec.sprite_id for spec in specs]
    missing = sorted(set(all_ids) - set(seen))
    duplicates = sorted(sprite_id for sprite_id in set(seen) if seen.count(sprite_id) > 1)
    if missing or duplicates:
        raise SystemExit(f"Batch coverage error. Missing={missing}; duplicates={duplicates}")


def _build_document(batches: list[tuple[str, str, list[SpriteSpec]]]) -> str:
    lines = [
        "# Sprite Batch Prompts",
        "",
        "Generated from the current game sprite manifest.",
        "",
        f"- Total sprites: {sum(len(batch) for _name, _title, batch in batches)}",
        f"- Batch layout: {COLUMNS} columns x {ROWS} rows",
        f"- Cell size: {CELL_SIZE}x{CELL_SIZE}",
        f"- Image size per full batch: {COLUMNS * CELL_SIZE}x{ROWS * CELL_SIZE}",
        "",
        "Save ChatGPT outputs into `assets/generated/` using the suggested filenames.",
        "",
        "## Batch Summary",
        "",
    ]
    for index, (name, title, batch) in enumerate(batches, start=1):
        lines.append(f"{index}. `{name}.png` - {title} - {len(batch)} sprites")
    for name, title, batch in batches:
        lines.extend(["", f"## {name}", "", f"Purpose: {title}", "", "Prompt:", "", "```text", _build_prompt(name, title, batch), "```"])
    return "\n".join(lines).rstrip() + "\n"


def _build_prompt(name: str, title: str, specs: list[SpriteSpec]) -> str:
    layout = _layout(specs)
    return textwrap.dedent(
        f"""
        Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: {name}
        - Batch purpose: {title}

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: {COLUMNS} columns x {ROWS} rows, row-major order.
        - Cell size: {CELL_SIZE}x{CELL_SIZE} px. Ideal final image size: {COLUMNS * CELL_SIZE}x{ROWS * CELL_SIZE} px.
        - Do not draw visible grid lines.
        - Do not draw labels, words, numbers, filenames, signatures, UI text, or watermarks.
        - Use a flat pure chroma-key background #FF00FF only in empty/transparent areas.
        - Terrain tiles must fill their entire cell edge-to-edge and must not show #FF00FF.
        - Features, agents, item icons, and UI icons must be centered on #FF00FF with clean silhouettes and 8-14 px padding.
        - Leave unused cells blank pure #FF00FF.

        ART DIRECTION:
        - Cohesive polished 2D pixel art, readable after downscaling to 32x32.
        - Top-down / slight 3/4 top-down game perspective.
        - Clean dark outline where useful, simple readable shapes, strong silhouettes.
        - No photorealism, no generic colored circles, no placeholder symbols.
        - Keep materials visually distinct: copper orange, iron gray, gold yellow, diamond cyan, stone gray, leather brown, herbs green.
        - Inventory items should look like icons, not scenery.
        - World features should look like objects placed on a map tile.
        - Agent sprites should be small standing survivor characters with distinct outfits and personalities.

        EXACT CELL CONTENTS, ROW-MAJOR:
        {layout}

        Before generating, internally check that this batch has {len(specs)} requested sprites and {COLUMNS * ROWS - len(specs)} unused blank cells.
        """
    ).strip()


def _layout(specs: list[SpriteSpec]) -> str:
    lines: list[str] = []
    total_cells = COLUMNS * ROWS
    for index in range(total_cells):
        row = index // COLUMNS + 1
        col = index % COLUMNS + 1
        if index < len(specs):
            spec = specs[index]
            lines.append(f"Row {row:02}, Col {col:02}: {spec.path} - {spec.name}, {spec.kind}, target {spec.size[0]}x{spec.size[1]}")
        else:
            lines.append(f"Row {row:02}, Col {col:02}: UNUSED - blank #FF00FF")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
