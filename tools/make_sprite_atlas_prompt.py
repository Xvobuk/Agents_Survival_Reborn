from __future__ import annotations

from pathlib import Path
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents_survival_reborn.data import SpriteSpec, sprite_specs


COLUMNS = 12
ROWS = 11
CELL_SIZE = 128


def main() -> int:
    specs = sprite_specs()
    print(build_prompt(specs))
    return 0


def build_prompt(specs: list[SpriteSpec]) -> str:
    layout = _layout(specs)
    return textwrap.dedent(
        f"""
        Create a single pixel-art sprite atlas for a top-down survival sandbox game.

        HARD TECHNICAL REQUIREMENTS:
        - One image only.
        - Exact layout: {COLUMNS} columns x {ROWS} rows, row-major order.
        - Cell size: {CELL_SIZE}x{CELL_SIZE} px. Ideal final image size: {COLUMNS * CELL_SIZE}x{ROWS * CELL_SIZE} px.
        - If your tool cannot output that exact size, keep the same 6:5 aspect ratio and the same {COLUMNS}x{ROWS} grid.
        - Do not draw visible grid lines.
        - Do not draw labels, words, numbers, filenames, signatures, UI text, or watermarks.
        - Use a flat pure chroma-key background #FF00FF only in empty/transparent areas.
        - Terrain tiles must fill their entire cell edge-to-edge and must not show #FF00FF.
        - Features, agents, item icons, and UI icons must be centered on #FF00FF with clean silhouettes and 8-14 px padding.
        - Leave unused cells blank pure #FF00FF.

        ART DIRECTION:
        - Cohesive polished 2D pixel art, readable at 32x32.
        - Top-down / slight 3/4 top-down game perspective.
        - Clean dark outline where useful, simple shapes, strong silhouettes, no photorealism.
        - Natural color variety: water blues, sand yellows, grass greens, rock grays, clay reds, snow whites, metals distinct.
        - Do not make generic circles or placeholder symbols.
        - Terrain tiles should look seamless and tileable.
        - World features should look like objects placed on a map tile.
        - Item icons should look like inventory icons, not full scenery.
        - Agent sprites should be small standing survivor characters with distinct outfits and personalities.

        EXACT CELL CONTENTS, ROW-MAJOR:
        PLACEHOLDER_LAYOUT

        Before generating, internally check that there are {len(specs)} requested sprites and {COLUMNS * ROWS - len(specs)} blank unused cells.
        """
    ).strip().replace("PLACEHOLDER_LAYOUT", layout)


def _layout(specs: list[SpriteSpec]) -> str:
    lines: list[str] = []
    total_cells = COLUMNS * ROWS
    for index in range(total_cells):
        row = index // COLUMNS + 1
        col = index % COLUMNS + 1
        if index < len(specs):
            spec = specs[index]
            lines.append(f"        Row {row:02}, Col {col:02}: {spec.path} - {spec.name}, {spec.kind}, target {spec.size[0]}x{spec.size[1]}")
        else:
            lines.append(f"        Row {row:02}, Col {col:02}: UNUSED - blank #FF00FF")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
