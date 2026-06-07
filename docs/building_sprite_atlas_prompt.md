# Building Sprite Atlas Prompt

Use this prompt in ChatGPT image generation to create one clean atlas for the new building sprites.

```text
Create a pixel-art sprite atlas for a top-down 2D survival sandbox game.

Canvas:
- transparent background if possible; if not possible, use one single flat chroma-key magenta background (#ff00ff) with no shadows or antialiasing bleeding into it
- pixel art, crisp edges, no text labels, no numbers, no UI mockup
- consistent lighting from upper-left
- same style as cozy detailed 32-bit survival/RPG sprites
- every sprite must fit inside its own invisible 32x32 cell with at least 3 px padding
- arrange sprites in a clean grid with even spacing, no overlaps
- do not draw a scene; draw isolated game sprites only

Sprites to include, exactly these 8 sprites:

1. Wooden floor tile, 32x32
Top-down square floor made of warm wooden planks, seamless tile edges, subtle board lines.

2. Stone floor tile, 32x32
Top-down square floor made of flat gray stone slabs, seamless tile edges, subtle cracks.

3. Wooden wall block, 32x32
Top-down/three-quarter wall segment made of logs and planks, sturdy, readable as an impassable wall.

4. Stone wall block, 32x32
Top-down/three-quarter wall segment made of stacked gray stones, sturdy, readable as an impassable wall.

5. Wooden floor inventory icon, 32x32
Small stack or single plank-floor tile icon, readable in inventory.

6. Stone floor inventory icon, 32x32
Small stack or single stone-floor tile icon, readable in inventory.

7. Wooden wall inventory icon, 32x32
Small wooden wall piece icon, readable in inventory.

8. Stone wall inventory icon, 32x32
Small stone wall piece icon, readable in inventory.

Important:
- Keep world tiles and inventory icons visually related but not identical: world tiles should be flatter/top-down, inventory icons may have a tiny item-like perspective.
- Do not include agents, trees, tools, furniture, doors, beds, crates, text, labels, icons outside this list, or decorative background elements.
- The output should be easy to slice manually into 32x32 sprites.
```

Expected filenames after slicing:

| Sprite ID | File | Size |
| --- | --- | --- |
| `item_wooden_floor` | `item_wooden_floor.png` | 32x32 |
| `item_stone_floor` | `item_stone_floor.png` | 32x32 |
| `item_wooden_wall` | `item_wooden_wall.png` | 32x32 |
| `item_stone_wall` | `item_stone_wall.png` | 32x32 |
| `feature_wooden_wall` | `feature_wooden_wall.png` | 32x32 |
| `feature_stone_wall` | `feature_stone_wall.png` | 32x32 |

The floor world layer uses the item sprites directly:

- `wooden_floor` uses `item_wooden_floor`
- `stone_floor` uses `item_stone_floor`

