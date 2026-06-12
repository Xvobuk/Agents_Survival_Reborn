# Sprite Batch Prompts

Generated from the current game sprite manifest.

- Total sprites: 399
- Batch layout: 8 columns x 8 rows
- Cell size: 128x128
- Image size per full batch: 1024x1024

Save ChatGPT outputs into `assets/generated/` using the suggested filenames.

## Batch Summary

1. `01_terrain_and_nature_features.png` - Terrain tiles and natural gatherable world features - 53 sprites
2. `02_ore_plants_and_natural_deposits.png` - Ore veins, stone outcrops, special deposits, fiber plants, and natural resource features - 40 sprites
3. `03_structures_agents_and_ui.png` - Crafting stations, placed structures, machines, agents, and UI icons - 34 sprites
4. `04_basic_items_food_and_building.png` - Basic resources, food, early tools, metal weapons, and gem-edged gear - 64 sprites
5. `05_building_armor_and_raw_resources.png` - Building pieces, storage, shelter, armor, jewelry, potions, stone tools, and raw resources - 64 sprites
6. `06_plants_animal_parts_and_workshop_tools.png` - Plant materials, animal parts, metal components, processed materials, and workshop tools - 64 sprites
7. `07_metal_tools_weapons_fishing_farming.png` - Metal tools, weapons, ammunition, fishing gear, farming supplies, lighting, navigation, and food - 64 sprites
8. `08_stations_building_medicine.png` - Station icons, storage, construction, machines, medicine, and treatment items - 16 sprites

## 01_terrain_and_nature_features

Purpose: Terrain tiles and natural gatherable world features

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 01_terrain_and_nature_features
        - Batch purpose: Terrain tiles and natural gatherable world features

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: terrain_deep_water.png - Deep water, terrain, target 32x32
Row 01, Col 02: terrain_shallow_water.png - Shallow water, terrain, target 32x32
Row 01, Col 03: terrain_coast.png - Coast, terrain, target 32x32
Row 01, Col 04: terrain_sand.png - Sand, terrain, target 32x32
Row 01, Col 05: terrain_grass.png - Grassland, terrain, target 32x32
Row 01, Col 06: terrain_meadow.png - Meadow, terrain, target 32x32
Row 01, Col 07: terrain_forest_floor.png - Forest floor, terrain, target 32x32
Row 01, Col 08: terrain_rock.png - Rocky cliffs, terrain, target 32x32
Row 02, Col 01: terrain_hills.png - Hills, terrain, target 32x32
Row 02, Col 02: terrain_clay_hills.png - Clay hills, terrain, target 32x32
Row 02, Col 03: terrain_swamp.png - Swamp, terrain, target 32x32
Row 02, Col 04: terrain_snow.png - Snowfield, terrain, target 32x32
Row 02, Col 05: terrain_tundra.png - Tundra, terrain, target 32x32
Row 02, Col 06: terrain_jungle.png - Jungle, terrain, target 32x32
Row 02, Col 07: terrain_mushroom_grove.png - Mushroom grove, terrain, target 32x32
Row 02, Col 08: terrain_badlands.png - Badlands, terrain, target 32x32
Row 03, Col 01: terrain_limestone_karst.png - Limestone karst, terrain, target 32x32
Row 03, Col 02: terrain_basalt_field.png - Basalt field, terrain, target 32x32
Row 03, Col 03: terrain_salt_flat.png - Salt flat, terrain, target 32x32
Row 03, Col 04: terrain_flax_meadow.png - Flax meadow, terrain, target 32x32
Row 03, Col 05: terrain_willow_wetland.png - Willow wetland, terrain, target 32x32
Row 03, Col 06: terrain_chalk_downs.png - Chalk downs, terrain, target 32x32
Row 03, Col 07: terrain_bee_grove.png - Bee grove, terrain, target 32x32
Row 03, Col 08: feature_cactus.png - Cactus, feature, target 32x32
Row 04, Col 01: feature_crab.png - Crab, feature, target 32x32
Row 04, Col 02: feature_fish_school.png - Fish school, feature, target 32x32
Row 04, Col 03: feature_salmon_school.png - Salmon school, feature, target 32x32
Row 04, Col 04: feature_eel.png - Eel, feature, target 32x32
Row 04, Col 05: feature_kelp.png - Kelp, feature, target 32x32
Row 04, Col 06: feature_reef.png - Reef, feature, target 32x32
Row 04, Col 07: feature_grass_tuft.png - Tall grass, feature, target 32x32
Row 04, Col 08: feature_flower_patch.png - Flower patch, feature, target 32x32
Row 05, Col 01: feature_berry_bush.png - Berry bush, feature, target 32x32
Row 05, Col 02: feature_herbs.png - Herbs, feature, target 32x32
Row 05, Col 03: feature_reeds.png - Reeds, feature, target 32x32
Row 05, Col 04: feature_mushrooms.png - Mushrooms, feature, target 32x32
Row 05, Col 05: feature_rabbit.png - Rabbit, feature, target 32x32
Row 05, Col 06: feature_deer.png - Deer, feature, target 32x32
Row 05, Col 07: feature_fox.png - Fox, feature, target 32x32
Row 05, Col 08: feature_boar.png - Boar, feature, target 32x32
Row 06, Col 01: feature_wolf.png - Wolf, feature, target 32x32
Row 06, Col 02: feature_bear.png - Bear, feature, target 32x32
Row 06, Col 03: feature_snake.png - Snake, feature, target 32x32
Row 06, Col 04: feature_frog.png - Frog, feature, target 32x32
Row 06, Col 05: feature_duck.png - Duck, feature, target 32x32
Row 06, Col 06: feature_gull.png - Gull, feature, target 32x32
Row 06, Col 07: feature_turtle.png - Turtle, feature, target 32x32
Row 06, Col 08: feature_birch_tree.png - Birch tree, feature, target 32x32
Row 07, Col 01: feature_oak_tree.png - Oak tree, feature, target 32x32
Row 07, Col 02: feature_pine_tree.png - Pine tree, feature, target 32x32
Row 07, Col 03: feature_fruit_tree.png - Fruit tree, feature, target 32x32
Row 07, Col 04: feature_stone_outcrop.png - Stone outcrop, feature, target 32x32
Row 07, Col 05: feature_cave.png - Cave mouth, feature, target 32x32
Row 07, Col 06: UNUSED - blank #FF00FF
Row 07, Col 07: UNUSED - blank #FF00FF
Row 07, Col 08: UNUSED - blank #FF00FF
Row 08, Col 01: UNUSED - blank #FF00FF
Row 08, Col 02: UNUSED - blank #FF00FF
Row 08, Col 03: UNUSED - blank #FF00FF
Row 08, Col 04: UNUSED - blank #FF00FF
Row 08, Col 05: UNUSED - blank #FF00FF
Row 08, Col 06: UNUSED - blank #FF00FF
Row 08, Col 07: UNUSED - blank #FF00FF
Row 08, Col 08: UNUSED - blank #FF00FF

        Before generating, internally check that this batch has 53 requested sprites and 11 unused blank cells.
```

## 02_ore_plants_and_natural_deposits

Purpose: Ore veins, stone outcrops, special deposits, fiber plants, and natural resource features

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 02_ore_plants_and_natural_deposits
        - Batch purpose: Ore veins, stone outcrops, special deposits, fiber plants, and natural resource features

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: feature_coal_vein.png - Coal vein, feature, target 32x32
Row 01, Col 02: feature_copper_vein.png - Copper vein, feature, target 32x32
Row 01, Col 03: feature_iron_vein.png - Iron vein, feature, target 32x32
Row 01, Col 04: feature_gold_vein.png - Gold vein, feature, target 32x32
Row 01, Col 05: feature_diamond_vein.png - Diamond vein, feature, target 32x32
Row 01, Col 06: feature_clay_patch.png - Clay patch, feature, target 32x32
Row 01, Col 07: feature_snowdrift.png - Snowdrift, feature, target 32x32
Row 01, Col 08: feature_workbench.png - Workbench, feature, target 32x32
Row 02, Col 01: feature_campfire.png - Campfire, feature, target 32x32
Row 02, Col 02: feature_kiln.png - Kiln, feature, target 32x32
Row 02, Col 03: feature_potion_stand.png - Potion stand, feature, target 32x32
Row 02, Col 04: feature_tent.png - Tent, feature, target 32x32
Row 02, Col 05: feature_wooden_crate.png - Wooden crate, feature, target 32x32
Row 02, Col 06: feature_wooden_door.png - Wooden door, feature, target 32x32
Row 02, Col 07: feature_wooden_wall.png - Wooden wall, feature, target 32x32
Row 02, Col 08: feature_stone_wall.png - Stone wall, feature, target 32x32
Row 03, Col 01: feature_bedroll.png - Bedroll, feature, target 32x32
Row 03, Col 02: feature_flint_nodule.png - Flint nodule, feature, target 32x32
Row 03, Col 03: feature_obsidian_glass.png - Obsidian glass, feature, target 32x32
Row 03, Col 04: feature_limestone_outcrop.png - Limestone outcrop, feature, target 32x32
Row 03, Col 05: feature_granite_outcrop.png - Granite outcrop, feature, target 32x32
Row 03, Col 06: feature_slate_outcrop.png - Slate outcrop, feature, target 32x32
Row 03, Col 07: feature_basalt_outcrop.png - Basalt outcrop, feature, target 32x32
Row 03, Col 08: feature_sulfur_deposit.png - Sulfur deposit, feature, target 32x32
Row 04, Col 01: feature_saltpeter_deposit.png - Saltpeter crust, feature, target 32x32
Row 04, Col 02: feature_kaolin_patch.png - Kaolin clay patch, feature, target 32x32
Row 04, Col 03: feature_gypsum_crystals.png - Gypsum crystals, feature, target 32x32
Row 04, Col 04: feature_sandstone_outcrop.png - Sandstone outcrop, feature, target 32x32
Row 04, Col 05: feature_rock_salt_crust.png - Rock salt crust, feature, target 32x32
Row 04, Col 06: feature_amber_root.png - Amber-bearing roots, feature, target 32x32
Row 04, Col 07: feature_pearl_mussels.png - River pearl mussels, feature, target 32x32
Row 04, Col 08: feature_flax_patch.png - Flax patch, feature, target 32x32
Row 05, Col 01: feature_hemp_patch.png - Hemp patch, feature, target 32x32
Row 05, Col 02: feature_cotton_bolls.png - Cotton bolls, feature, target 32x32
Row 05, Col 03: feature_willow_stand.png - Willow stand, feature, target 32x32
Row 05, Col 04: feature_straw_patch.png - Dry straw patch, feature, target 32x32
Row 05, Col 05: feature_medicinal_flowers.png - Medicinal flowers, feature, target 32x32
Row 05, Col 06: feature_mint_patch.png - Mint patch, feature, target 32x32
Row 05, Col 07: feature_nettles.png - Nettles, feature, target 32x32
Row 05, Col 08: feature_beehive.png - Beehive, feature, target 32x32
Row 06, Col 01: UNUSED - blank #FF00FF
Row 06, Col 02: UNUSED - blank #FF00FF
Row 06, Col 03: UNUSED - blank #FF00FF
Row 06, Col 04: UNUSED - blank #FF00FF
Row 06, Col 05: UNUSED - blank #FF00FF
Row 06, Col 06: UNUSED - blank #FF00FF
Row 06, Col 07: UNUSED - blank #FF00FF
Row 06, Col 08: UNUSED - blank #FF00FF
Row 07, Col 01: UNUSED - blank #FF00FF
Row 07, Col 02: UNUSED - blank #FF00FF
Row 07, Col 03: UNUSED - blank #FF00FF
Row 07, Col 04: UNUSED - blank #FF00FF
Row 07, Col 05: UNUSED - blank #FF00FF
Row 07, Col 06: UNUSED - blank #FF00FF
Row 07, Col 07: UNUSED - blank #FF00FF
Row 07, Col 08: UNUSED - blank #FF00FF
Row 08, Col 01: UNUSED - blank #FF00FF
Row 08, Col 02: UNUSED - blank #FF00FF
Row 08, Col 03: UNUSED - blank #FF00FF
Row 08, Col 04: UNUSED - blank #FF00FF
Row 08, Col 05: UNUSED - blank #FF00FF
Row 08, Col 06: UNUSED - blank #FF00FF
Row 08, Col 07: UNUSED - blank #FF00FF
Row 08, Col 08: UNUSED - blank #FF00FF

        Before generating, internally check that this batch has 40 requested sprites and 24 unused blank cells.
```

## 03_structures_agents_and_ui

Purpose: Crafting stations, placed structures, machines, agents, and UI icons

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 03_structures_agents_and_ui
        - Batch purpose: Crafting stations, placed structures, machines, agents, and UI icons

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: feature_loom.png - Loom, feature, target 32x32
Row 01, Col 02: feature_pottery_wheel.png - Pottery wheel, feature, target 32x32
Row 01, Col 03: feature_signal_fire.png - Signal fire, feature, target 32x32
Row 01, Col 04: feature_wattle_wall.png - Wattle wall, feature, target 32x32
Row 01, Col 05: feature_straw_roof.png - Straw roof bundle, feature, target 32x32
Row 01, Col 06: feature_water_wheel.png - Water wheel, feature, target 32x32
Row 01, Col 07: feature_carpenter_table.png - Carpenter table, feature, target 32x32
Row 01, Col 08: feature_cart.png - Cart, feature, target 32x32
Row 02, Col 01: feature_smelter.png - Smelter, feature, target 32x32
Row 02, Col 02: feature_pump.png - Pump, feature, target 32x32
Row 02, Col 03: feature_windmill.png - Windmill, feature, target 32x32
Row 02, Col 04: feature_steam_boiler.png - Steam boiler, feature, target 32x32
Row 02, Col 05: feature_steam_hammer.png - Steam hammer, feature, target 32x32
Row 02, Col 06: feature_jeweler_bench.png - Jeweler bench, feature, target 32x32
Row 02, Col 07: feature_oil_press.png - Oil press, feature, target 32x32
Row 02, Col 08: feature_blast_furnace.png - Blast furnace, feature, target 32x32
Row 03, Col 01: feature_tanning_table.png - Tanning table, feature, target 32x32
Row 03, Col 02: feature_stonecutting_table.png - Stonecutting table, feature, target 32x32
Row 03, Col 03: feature_forge_bellows.png - Forge bellows, feature, target 32x32
Row 03, Col 04: agent_methodical_builder.png - Agent Methodical Builder, agent, target 32x40
Row 03, Col 05: agent_quiet_miner.png - Agent Quiet Miner, agent, target 32x40
Row 03, Col 06: agent_coastal_provider.png - Agent Coastal Provider, agent, target 32x40
Row 03, Col 07: agent_restless_explorer.png - Agent Restless Explorer, agent, target 32x40
Row 03, Col 08: agent_careful_forager.png - Agent Careful Forager, agent, target 32x40
Row 04, Col 01: agent_competitive_solo.png - Agent Competitive Solo, agent, target 32x40
Row 04, Col 02: agent_social_trader.png - Agent Social Trader, agent, target 32x40
Row 04, Col 03: agent_survival_minmaxer.png - Agent Survival Minmaxer, agent, target 32x40
Row 04, Col 04: ui_unknown.png - Ui Unknown, ui, target 24x24
Row 04, Col 05: ui_selected.png - Ui Selected, ui, target 24x24
Row 04, Col 06: ui_chat.png - Ui Chat, ui, target 24x24
Row 04, Col 07: ui_inventory.png - Ui Inventory, ui, target 24x24
Row 04, Col 08: ui_health.png - Ui Health, ui, target 24x24
Row 05, Col 01: ui_hunger.png - Ui Hunger, ui, target 24x24
Row 05, Col 02: ui_energy.png - Ui Energy, ui, target 24x24
Row 05, Col 03: UNUSED - blank #FF00FF
Row 05, Col 04: UNUSED - blank #FF00FF
Row 05, Col 05: UNUSED - blank #FF00FF
Row 05, Col 06: UNUSED - blank #FF00FF
Row 05, Col 07: UNUSED - blank #FF00FF
Row 05, Col 08: UNUSED - blank #FF00FF
Row 06, Col 01: UNUSED - blank #FF00FF
Row 06, Col 02: UNUSED - blank #FF00FF
Row 06, Col 03: UNUSED - blank #FF00FF
Row 06, Col 04: UNUSED - blank #FF00FF
Row 06, Col 05: UNUSED - blank #FF00FF
Row 06, Col 06: UNUSED - blank #FF00FF
Row 06, Col 07: UNUSED - blank #FF00FF
Row 06, Col 08: UNUSED - blank #FF00FF
Row 07, Col 01: UNUSED - blank #FF00FF
Row 07, Col 02: UNUSED - blank #FF00FF
Row 07, Col 03: UNUSED - blank #FF00FF
Row 07, Col 04: UNUSED - blank #FF00FF
Row 07, Col 05: UNUSED - blank #FF00FF
Row 07, Col 06: UNUSED - blank #FF00FF
Row 07, Col 07: UNUSED - blank #FF00FF
Row 07, Col 08: UNUSED - blank #FF00FF
Row 08, Col 01: UNUSED - blank #FF00FF
Row 08, Col 02: UNUSED - blank #FF00FF
Row 08, Col 03: UNUSED - blank #FF00FF
Row 08, Col 04: UNUSED - blank #FF00FF
Row 08, Col 05: UNUSED - blank #FF00FF
Row 08, Col 06: UNUSED - blank #FF00FF
Row 08, Col 07: UNUSED - blank #FF00FF
Row 08, Col 08: UNUSED - blank #FF00FF

        Before generating, internally check that this batch has 34 requested sprites and 30 unused blank cells.
```

## 04_basic_items_food_and_building

Purpose: Basic resources, food, early tools, metal weapons, and gem-edged gear

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 04_basic_items_food_and_building
        - Batch purpose: Basic resources, food, early tools, metal weapons, and gem-edged gear

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: item_soil.png - Handful of soil, item, target 32x32
Row 01, Col 02: item_sand.png - Clean sand, item, target 32x32
Row 01, Col 03: item_clay_lump.png - Clay lump, item, target 32x32
Row 01, Col 04: item_snow.png - Packed snow, item, target 32x32
Row 01, Col 05: item_stone.png - Stone, item, target 32x32
Row 01, Col 06: item_pebble.png - Pebble, item, target 32x32
Row 01, Col 07: item_flint.png - Flint, item, target 32x32
Row 01, Col 08: item_coal.png - Coal, item, target 32x32
Row 02, Col 01: item_copper_ore.png - Copper ore, item, target 32x32
Row 02, Col 02: item_iron_ore.png - Iron ore, item, target 32x32
Row 02, Col 03: item_gold_ore.png - Gold ore, item, target 32x32
Row 02, Col 04: item_diamond.png - Rough diamond, item, target 32x32
Row 02, Col 05: item_shell.png - Shell, item, target 32x32
Row 02, Col 06: item_glass.png - Glass, item, target 32x32
Row 02, Col 07: item_glass_bottle.png - Glass bottle, item, target 32x32
Row 02, Col 08: item_charcoal.png - Charcoal, item, target 32x32
Row 03, Col 01: item_copper_ingot.png - Copper ingot, item, target 32x32
Row 03, Col 02: item_iron_ingot.png - Iron ingot, item, target 32x32
Row 03, Col 03: item_gold_ingot.png - Gold ingot, item, target 32x32
Row 03, Col 04: item_hide.png - Hide, item, target 32x32
Row 03, Col 05: item_leather.png - Leather, item, target 32x32
Row 03, Col 06: item_venom_sac.png - Venom sac, item, target 32x32
Row 03, Col 07: item_grass_fiber.png - Grass fiber, item, target 32x32
Row 03, Col 08: item_reeds.png - Reeds, item, target 32x32
Row 04, Col 01: item_cordage.png - Cordage, item, target 32x32
Row 04, Col 02: item_flower.png - Wild flower, item, target 32x32
Row 04, Col 03: item_herb.png - Bitter herb, item, target 32x32
Row 04, Col 04: item_mushroom.png - Mushroom, item, target 32x32
Row 04, Col 05: item_berries.png - Berries, item, target 32x32
Row 04, Col 06: item_blueberries.png - Blueberries, item, target 32x32
Row 04, Col 07: item_wild_seed.png - Wild seed, item, target 32x32
Row 04, Col 08: item_seaweed.png - Seaweed, item, target 32x32
Row 05, Col 01: item_cactus_flesh.png - Cactus flesh, item, target 32x32
Row 05, Col 02: item_cactus_spine.png - Cactus spine, item, target 32x32
Row 05, Col 03: item_raw_fish.png - Raw fish, item, target 32x32
Row 05, Col 04: item_crab_meat.png - Crab meat, item, target 32x32
Row 05, Col 05: item_raw_meat.png - Raw meat, item, target 32x32
Row 05, Col 06: item_cooked_fish.png - Cooked fish, item, target 32x32
Row 05, Col 07: item_cooked_crab.png - Cooked crab, item, target 32x32
Row 05, Col 08: item_cooked_meat.png - Cooked meat, item, target 32x32
Row 06, Col 01: item_egg.png - Egg, item, target 32x32
Row 06, Col 02: item_fried_egg.png - Fried egg, item, target 32x32
Row 06, Col 03: item_bread.png - Bread, item, target 32x32
Row 06, Col 04: item_birch_log.png - Birch log, item, target 32x32
Row 06, Col 05: item_oak_log.png - Oak log, item, target 32x32
Row 06, Col 06: item_pine_log.png - Pine log, item, target 32x32
Row 06, Col 07: item_fruit_log.png - Fruitwood log, item, target 32x32
Row 06, Col 08: item_stick.png - Stick, item, target 32x32
Row 07, Col 01: item_bark.png - Bark, item, target 32x32
Row 07, Col 02: item_resin.png - Resin, item, target 32x32
Row 07, Col 03: item_plank.png - Plank, item, target 32x32
Row 07, Col 04: item_clay_pot.png - Clay pot, item, target 32x32
Row 07, Col 05: item_workbench.png - Workbench, item, target 32x32
Row 07, Col 06: item_campfire.png - Campfire, item, target 32x32
Row 07, Col 07: item_kiln.png - Kiln, item, target 32x32
Row 07, Col 08: item_potion_stand.png - Potion stand, item, target 32x32
Row 08, Col 01: item_torch.png - Torch, item, target 32x32
Row 08, Col 02: item_wooden_shield.png - Wooden shield, item, target 32x32
Row 08, Col 03: item_copper_axe.png - Copper axe, item, target 32x32
Row 08, Col 04: item_copper_sword.png - Copper sword, item, target 32x32
Row 08, Col 05: item_iron_axe.png - Iron axe, item, target 32x32
Row 08, Col 06: item_iron_sword.png - Iron sword, item, target 32x32
Row 08, Col 07: item_diamond_edged_pickaxe.png - Diamond-edged pickaxe, item, target 32x32
Row 08, Col 08: item_diamond_edged_sword.png - Diamond-edged sword, item, target 32x32

        Before generating, internally check that this batch has 64 requested sprites and 0 unused blank cells.
```

## 05_building_armor_and_raw_resources

Purpose: Building pieces, storage, shelter, armor, jewelry, potions, stone tools, and raw resources

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 05_building_armor_and_raw_resources
        - Batch purpose: Building pieces, storage, shelter, armor, jewelry, potions, stone tools, and raw resources

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: item_wooden_floor.png - Wooden floor, item, target 32x32
Row 01, Col 02: item_stone_floor.png - Stone floor, item, target 32x32
Row 01, Col 03: item_wooden_wall.png - Wooden wall, item, target 32x32
Row 01, Col 04: item_stone_wall.png - Stone wall, item, target 32x32
Row 01, Col 05: item_wooden_crate.png - Wooden crate, item, target 32x32
Row 01, Col 06: item_wooden_door.png - Wooden door, item, target 32x32
Row 01, Col 07: item_bedroll.png - Bedroll, item, target 32x32
Row 01, Col 08: item_tent.png - Tent, item, target 32x32
Row 02, Col 01: item_sack.png - Sack, item, target 32x32
Row 02, Col 02: item_copper_ring.png - Copper ring, item, target 32x32
Row 02, Col 03: item_gold_ring.png - Gold ring, item, target 32x32
Row 02, Col 04: item_gold_necklace.png - Gold necklace, item, target 32x32
Row 02, Col 05: item_diamond_ring.png - Diamond ring, item, target 32x32
Row 02, Col 06: item_diamond_amulet.png - Diamond amulet, item, target 32x32
Row 02, Col 07: item_leather_cap.png - Leather cap, item, target 32x32
Row 02, Col 08: item_leather_gloves.png - Leather gloves, item, target 32x32
Row 03, Col 01: item_leather_tunic.png - Leather tunic, item, target 32x32
Row 03, Col 02: item_leather_pants.png - Leather pants, item, target 32x32
Row 03, Col 03: item_leather_boots.png - Leather boots, item, target 32x32
Row 03, Col 04: item_iron_helmet.png - Iron helmet, item, target 32x32
Row 03, Col 05: item_iron_gauntlets.png - Iron gauntlets, item, target 32x32
Row 03, Col 06: item_iron_chestplate.png - Iron chestplate, item, target 32x32
Row 03, Col 07: item_iron_greaves.png - Iron greaves, item, target 32x32
Row 03, Col 08: item_iron_boots.png - Iron boots, item, target 32x32
Row 04, Col 01: item_healing_potion.png - Healing potion, item, target 32x32
Row 04, Col 02: item_stamina_potion.png - Stamina potion, item, target 32x32
Row 04, Col 03: item_antidote.png - Antidote, item, target 32x32
Row 04, Col 04: item_stone_knife.png - Stone knife, item, target 32x32
Row 04, Col 05: item_stone_axe.png - Stone axe, item, target 32x32
Row 04, Col 06: item_stone_shovel.png - Stone shovel, item, target 32x32
Row 04, Col 07: item_wooden_pickaxe.png - Wooden pickaxe, item, target 32x32
Row 04, Col 08: item_stone_pickaxe.png - Stone pickaxe, item, target 32x32
Row 05, Col 01: item_wooden_spear.png - Wooden spear, item, target 32x32
Row 05, Col 02: item_bow.png - Bow, item, target 32x32
Row 05, Col 03: item_arrow.png - Arrow, item, target 32x32
Row 05, Col 04: item_fishing_rod.png - Fishing rod, item, target 32x32
Row 05, Col 05: item_fish_net.png - Fish net, item, target 32x32
Row 05, Col 06: item_copper_pickaxe.png - Copper pickaxe, item, target 32x32
Row 05, Col 07: item_iron_pickaxe.png - Iron pickaxe, item, target 32x32
Row 05, Col 08: item_diamond_pickaxe.png - Diamond pickaxe, item, target 32x32
Row 06, Col 01: item_flint_shard.png - Flint shard, item, target 32x32
Row 06, Col 02: item_obsidian_shard.png - Obsidian shard, item, target 32x32
Row 06, Col 03: item_limestone.png - Limestone, item, target 32x32
Row 06, Col 04: item_granite.png - Granite, item, target 32x32
Row 06, Col 05: item_slate.png - Slate, item, target 32x32
Row 06, Col 06: item_basalt.png - Basalt, item, target 32x32
Row 06, Col 07: item_sulfur_stone.png - Sulfur stone, item, target 32x32
Row 06, Col 08: item_saltpeter.png - Saltpeter, item, target 32x32
Row 07, Col 01: item_high_quality_clay.png - High quality clay, item, target 32x32
Row 07, Col 02: item_kaolin.png - Kaolin, item, target 32x32
Row 07, Col 03: item_chalk.png - Chalk, item, target 32x32
Row 07, Col 04: item_gypsum.png - Gypsum, item, target 32x32
Row 07, Col 05: item_sandstone.png - Sandstone, item, target 32x32
Row 07, Col 06: item_rock_salt.png - Rock salt, item, target 32x32
Row 07, Col 07: item_amber.png - Amber, item, target 32x32
Row 07, Col 08: item_river_pearl.png - River pearl, item, target 32x32
Row 08, Col 01: item_flax.png - Flax, item, target 32x32
Row 08, Col 02: item_hemp.png - Hemp, item, target 32x32
Row 08, Col 03: item_cotton.png - Cotton, item, target 32x32
Row 08, Col 04: item_reed_fiber.png - Reed fiber, item, target 32x32
Row 08, Col 05: item_birch_bark.png - Birch bark, item, target 32x32
Row 08, Col 06: item_willow_withe.png - Willow withe, item, target 32x32
Row 08, Col 07: item_dry_straw.png - Dry straw, item, target 32x32
Row 08, Col 08: item_resinous_wood.png - Resinous wood, item, target 32x32

        Before generating, internally check that this batch has 64 requested sprites and 0 unused blank cells.
```

## 06_plants_animal_parts_and_workshop_tools

Purpose: Plant materials, animal parts, metal components, processed materials, and workshop tools

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 06_plants_animal_parts_and_workshop_tools
        - Batch purpose: Plant materials, animal parts, metal components, processed materials, and workshop tools

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: item_oak_acorn.png - Oak acorn, item, target 32x32
Row 01, Col 02: item_pine_cone.png - Pine cone, item, target 32x32
Row 01, Col 03: item_maple_sap.png - Maple sap, item, target 32x32
Row 01, Col 04: item_nuts.png - Nuts, item, target 32x32
Row 01, Col 05: item_chamomile.png - Chamomile, item, target 32x32
Row 01, Col 06: item_yarrow.png - Yarrow, item, target 32x32
Row 01, Col 07: item_mint.png - Mint, item, target 32x32
Row 01, Col 08: item_nettle.png - Nettle, item, target 32x32
Row 02, Col 01: item_rawhide.png - Rawhide, item, target 32x32
Row 02, Col 02: item_thick_hide.png - Thick hide, item, target 32x32
Row 02, Col 03: item_rabbit_fur.png - Rabbit fur, item, target 32x32
Row 02, Col 04: item_fox_fur.png - Fox fur, item, target 32x32
Row 02, Col 05: item_sinew.png - Sinew, item, target 32x32
Row 02, Col 06: item_bone.png - Bone, item, target 32x32
Row 02, Col 07: item_deer_antler.png - Deer antler, item, target 32x32
Row 02, Col 08: item_boar_tusk.png - Boar tusk, item, target 32x32
Row 03, Col 01: item_bird_feather.png - Bird feather, item, target 32x32
Row 03, Col 02: item_down.png - Down, item, target 32x32
Row 03, Col 03: item_beeswax.png - Beeswax, item, target 32x32
Row 03, Col 04: item_honeycomb.png - Honeycomb, item, target 32x32
Row 03, Col 05: item_copper_nails.png - Copper nails, item, target 32x32
Row 03, Col 06: item_iron_nails.png - Iron nails, item, target 32x32
Row 03, Col 07: item_copper_rivets.png - Copper rivets, item, target 32x32
Row 03, Col 08: item_iron_brackets.png - Iron brackets, item, target 32x32
Row 04, Col 01: item_iron_chain.png - Iron chain, item, target 32x32
Row 04, Col 02: item_copper_wire.png - Copper wire, item, target 32x32
Row 04, Col 03: item_iron_wire.png - Iron wire, item, target 32x32
Row 04, Col 04: item_hardened_steel.png - Hardened steel, item, target 32x32
Row 04, Col 05: item_glass_tube.png - Glass tube, item, target 32x32
Row 04, Col 06: item_glass_lens.png - Glass lens, item, target 32x32
Row 04, Col 07: item_polished_plank.png - Polished plank, item, target 32x32
Row 04, Col 08: item_leather_belt.png - Leather belt, item, target 32x32
Row 05, Col 01: item_rope_coil.png - Rope coil, item, target 32x32
Row 05, Col 02: item_cloth.png - Cloth roll, item, target 32x32
Row 05, Col 03: item_canvas.png - Canvas sheet, item, target 32x32
Row 05, Col 04: item_charcoal_sack.png - Charcoal sack, item, target 32x32
Row 05, Col 05: item_sling_stones.png - Sling stones, item, target 32x32
Row 05, Col 06: item_flint_arrows.png - Flint arrows, item, target 32x32
Row 05, Col 07: item_copper_arrows.png - Copper arrows, item, target 32x32
Row 05, Col 08: item_iron_arrows.png - Iron arrows, item, target 32x32
Row 06, Col 01: item_harpoons.png - Harpoons, item, target 32x32
Row 06, Col 02: item_fish_hook.png - Fish hook, item, target 32x32
Row 06, Col 03: item_copper_hook.png - Copper hook, item, target 32x32
Row 06, Col 04: item_iron_hook.png - Iron hook, item, target 32x32
Row 06, Col 05: item_float_bobber.png - Float bobber, item, target 32x32
Row 06, Col 06: item_bait.png - Bait, item, target 32x32
Row 06, Col 07: item_fish_oil.png - Fish oil, item, target 32x32
Row 06, Col 08: item_flax_seed.png - Flax seeds, item, target 32x32
Row 07, Col 01: item_cabbage_seed.png - Cabbage seeds, item, target 32x32
Row 07, Col 02: item_carrot_seed.png - Carrot seeds, item, target 32x32
Row 07, Col 03: item_potato_seed.png - Potato seeds, item, target 32x32
Row 07, Col 04: item_pumpkin_seed.png - Pumpkin seeds, item, target 32x32
Row 07, Col 05: item_corn_seed.png - Corn seeds, item, target 32x32
Row 07, Col 06: item_manure.png - Manure, item, target 32x32
Row 07, Col 07: item_compost.png - Compost bag, item, target 32x32
Row 07, Col 08: item_fertilizer.png - Fertilizer sack, item, target 32x32
Row 08, Col 01: item_fat.png - Rendered fat, item, target 32x32
Row 08, Col 02: item_brass.png - Brass, item, target 32x32
Row 08, Col 03: item_stone_hammer.png - Stone hammer, item, target 32x32
Row 08, Col 04: item_flint_hammer.png - Flint hammer, item, target 32x32
Row 08, Col 05: item_stone_chisel.png - Stone chisel, item, target 32x32
Row 08, Col 06: item_stone_hoe.png - Stone hoe, item, target 32x32
Row 08, Col 07: item_stone_sickle.png - Stone sickle, item, target 32x32
Row 08, Col 08: item_wooden_mallet.png - Wooden mallet, item, target 32x32

        Before generating, internally check that this batch has 64 requested sprites and 0 unused blank cells.
```

## 07_metal_tools_weapons_fishing_farming

Purpose: Metal tools, weapons, ammunition, fishing gear, farming supplies, lighting, navigation, and food

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 07_metal_tools_weapons_fishing_farming
        - Batch purpose: Metal tools, weapons, ammunition, fishing gear, farming supplies, lighting, navigation, and food

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: item_copper_hammer.png - Copper hammer, item, target 32x32
Row 01, Col 02: item_copper_chisel.png - Copper chisel, item, target 32x32
Row 01, Col 03: item_copper_hoe.png - Copper hoe, item, target 32x32
Row 01, Col 04: item_copper_saw.png - Copper saw, item, target 32x32
Row 01, Col 05: item_iron_saw.png - Iron saw, item, target 32x32
Row 01, Col 06: item_iron_hammer.png - Iron hammer, item, target 32x32
Row 01, Col 07: item_iron_chisel.png - Iron chisel, item, target 32x32
Row 01, Col 08: item_sling.png - Sling, item, target 32x32
Row 02, Col 01: item_bolas.png - Bolas, item, target 32x32
Row 02, Col 02: item_atlatl.png - Atlatl, item, target 32x32
Row 02, Col 03: item_throwing_spear.png - Throwing spear, item, target 32x32
Row 02, Col 04: item_shortbow.png - Shortbow, item, target 32x32
Row 02, Col 05: item_longbow.png - Longbow, item, target 32x32
Row 02, Col 06: item_composite_bow.png - Composite bow, item, target 32x32
Row 02, Col 07: item_crossbow.png - Crossbow, item, target 32x32
Row 02, Col 08: item_iron_spear.png - Iron spear, item, target 32x32
Row 03, Col 01: item_halberd.png - Halberd, item, target 32x32
Row 03, Col 02: item_mace.png - Mace, item, target 32x32
Row 03, Col 03: item_warhammer.png - War hammer, item, target 32x32
Row 03, Col 04: item_harpoon.png - Harpoon, item, target 32x32
Row 03, Col 05: item_fish_trap.png - Fish trap, item, target 32x32
Row 03, Col 06: item_crab_trap.png - Crab trap, item, target 32x32
Row 03, Col 07: item_watering_can.png - Watering can, item, target 32x32
Row 03, Col 08: item_wooden_bucket.png - Wooden bucket, item, target 32x32
Row 04, Col 01: item_iron_bucket.png - Iron bucket, item, target 32x32
Row 04, Col 02: item_torch_resin.png - Resin torch, item, target 32x32
Row 04, Col 03: item_candle.png - Candle, item, target 32x32
Row 04, Col 04: item_wax_candle.png - Wax candle, item, target 32x32
Row 04, Col 05: item_oil_lamp.png - Oil lamp, item, target 32x32
Row 04, Col 06: item_lantern.png - Lantern, item, target 32x32
Row 04, Col 07: item_reflector.png - Reflector, item, target 32x32
Row 04, Col 08: item_compass.png - Compass, item, target 32x32
Row 05, Col 01: item_spyglass.png - Spyglass, item, target 32x32
Row 05, Col 02: item_terrain_map.png - Terrain map, item, target 32x32
Row 05, Col 03: item_sextant.png - Sextant, item, target 32x32
Row 05, Col 04: item_barometer.png - Barometer, item, target 32x32
Row 05, Col 05: item_thermometer.png - Thermometer, item, target 32x32
Row 05, Col 06: item_mechanical_clock.png - Mechanical clock, item, target 32x32
Row 05, Col 07: item_survey_tripod.png - Survey tripod, item, target 32x32
Row 05, Col 08: item_dried_fish.png - Dried fish, item, target 32x32
Row 06, Col 01: item_dried_meat.png - Dried meat, item, target 32x32
Row 06, Col 02: item_smoked_fish.png - Smoked fish, item, target 32x32
Row 06, Col 03: item_jerky.png - Jerky, item, target 32x32
Row 06, Col 04: item_stew.png - Stew, item, target 32x32
Row 06, Col 05: item_vegetable_stew.png - Vegetable stew, item, target 32x32
Row 06, Col 06: item_fish_soup.png - Fish soup, item, target 32x32
Row 06, Col 07: item_fried_mushrooms.png - Fried mushrooms, item, target 32x32
Row 06, Col 08: item_nut_mix.png - Nut mix, item, target 32x32
Row 07, Col 01: item_flatbread.png - Flatbread, item, target 32x32
Row 07, Col 02: item_cheese.png - Cheese, item, target 32x32
Row 07, Col 03: item_butter.png - Butter, item, target 32x32
Row 07, Col 04: item_chamomile_tea.png - Chamomile infusion, item, target 32x32
Row 07, Col 05: item_mint_tea.png - Mint infusion, item, target 32x32
Row 07, Col 06: item_carpenter_table.png - Carpenter table, item, target 32x32
Row 07, Col 07: item_tanning_table.png - Tanning table, item, target 32x32
Row 07, Col 08: item_stonecutting_table.png - Stonecutting table, item, target 32x32
Row 08, Col 01: item_forge_bellows.png - Forge bellows, item, target 32x32
Row 08, Col 02: item_smelter.png - Smelter, item, target 32x32
Row 08, Col 03: item_blast_furnace.png - Blast furnace, item, target 32x32
Row 08, Col 04: item_jeweler_bench.png - Jeweler bench, item, target 32x32
Row 08, Col 05: item_loom.png - Loom, item, target 32x32
Row 08, Col 06: item_pottery_wheel.png - Pottery wheel, item, target 32x32
Row 08, Col 07: item_oil_press.png - Oil press, item, target 32x32
Row 08, Col 08: item_wicker_basket.png - Wicker basket, item, target 32x32

        Before generating, internally check that this batch has 64 requested sprites and 0 unused blank cells.
```

## 08_stations_building_medicine

Purpose: Station icons, storage, construction, machines, medicine, and treatment items

Prompt:

```text
Create ONE pixel-art sprite atlas for a top-down survival sandbox game.

        FILE/BATCH:
        - Batch name: 08_stations_building_medicine
        - Batch purpose: Station icons, storage, construction, machines, medicine, and treatment items

        HARD TECHNICAL REQUIREMENTS:
        - Output one image only.
        - Exact layout: 8 columns x 8 rows, row-major order.
        - Cell size: 128x128 px. Ideal final image size: 1024x1024 px.
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
        Row 01, Col 01: item_straw_roof.png - Straw roof bundle, item, target 32x32
Row 01, Col 02: item_wattle_wall.png - Wattle wall, item, target 32x32
Row 01, Col 03: item_signal_fire.png - Signal fire, item, target 32x32
Row 01, Col 04: item_cart.png - Cart, item, target 32x32
Row 01, Col 05: item_windmill.png - Windmill, item, target 32x32
Row 01, Col 06: item_water_wheel.png - Water wheel, item, target 32x32
Row 01, Col 07: item_pump.png - Pump, item, target 32x32
Row 01, Col 08: item_steam_boiler.png - Steam boiler, item, target 32x32
Row 02, Col 01: item_steam_hammer.png - Steam hammer, item, target 32x32
Row 02, Col 02: item_bandage.png - Bandage, item, target 32x32
Row 02, Col 03: item_improved_bandage.png - Improved bandage, item, target 32x32
Row 02, Col 04: item_splint.png - Splint, item, target 32x32
Row 02, Col 05: item_antiseptic.png - Antiseptic, item, target 32x32
Row 02, Col 06: item_painkiller.png - Painkiller, item, target 32x32
Row 02, Col 07: item_honey_ointment.png - Honey ointment, item, target 32x32
Row 02, Col 08: item_compress.png - Compress, item, target 32x32
Row 03, Col 01: UNUSED - blank #FF00FF
Row 03, Col 02: UNUSED - blank #FF00FF
Row 03, Col 03: UNUSED - blank #FF00FF
Row 03, Col 04: UNUSED - blank #FF00FF
Row 03, Col 05: UNUSED - blank #FF00FF
Row 03, Col 06: UNUSED - blank #FF00FF
Row 03, Col 07: UNUSED - blank #FF00FF
Row 03, Col 08: UNUSED - blank #FF00FF
Row 04, Col 01: UNUSED - blank #FF00FF
Row 04, Col 02: UNUSED - blank #FF00FF
Row 04, Col 03: UNUSED - blank #FF00FF
Row 04, Col 04: UNUSED - blank #FF00FF
Row 04, Col 05: UNUSED - blank #FF00FF
Row 04, Col 06: UNUSED - blank #FF00FF
Row 04, Col 07: UNUSED - blank #FF00FF
Row 04, Col 08: UNUSED - blank #FF00FF
Row 05, Col 01: UNUSED - blank #FF00FF
Row 05, Col 02: UNUSED - blank #FF00FF
Row 05, Col 03: UNUSED - blank #FF00FF
Row 05, Col 04: UNUSED - blank #FF00FF
Row 05, Col 05: UNUSED - blank #FF00FF
Row 05, Col 06: UNUSED - blank #FF00FF
Row 05, Col 07: UNUSED - blank #FF00FF
Row 05, Col 08: UNUSED - blank #FF00FF
Row 06, Col 01: UNUSED - blank #FF00FF
Row 06, Col 02: UNUSED - blank #FF00FF
Row 06, Col 03: UNUSED - blank #FF00FF
Row 06, Col 04: UNUSED - blank #FF00FF
Row 06, Col 05: UNUSED - blank #FF00FF
Row 06, Col 06: UNUSED - blank #FF00FF
Row 06, Col 07: UNUSED - blank #FF00FF
Row 06, Col 08: UNUSED - blank #FF00FF
Row 07, Col 01: UNUSED - blank #FF00FF
Row 07, Col 02: UNUSED - blank #FF00FF
Row 07, Col 03: UNUSED - blank #FF00FF
Row 07, Col 04: UNUSED - blank #FF00FF
Row 07, Col 05: UNUSED - blank #FF00FF
Row 07, Col 06: UNUSED - blank #FF00FF
Row 07, Col 07: UNUSED - blank #FF00FF
Row 07, Col 08: UNUSED - blank #FF00FF
Row 08, Col 01: UNUSED - blank #FF00FF
Row 08, Col 02: UNUSED - blank #FF00FF
Row 08, Col 03: UNUSED - blank #FF00FF
Row 08, Col 04: UNUSED - blank #FF00FF
Row 08, Col 05: UNUSED - blank #FF00FF
Row 08, Col 06: UNUSED - blank #FF00FF
Row 08, Col 07: UNUSED - blank #FF00FF
Row 08, Col 08: UNUSED - blank #FF00FF

        Before generating, internally check that this batch has 16 requested sprites and 48 unused blank cells.
```
