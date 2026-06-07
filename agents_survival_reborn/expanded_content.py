from __future__ import annotations

from collections.abc import Iterable

from .data import FeatureDef, Ingredient, ItemDef, Loot, RecipeDef, TerrainDef, ing


def apply_expanded_content(
    terrains: dict[str, TerrainDef],
    features: dict[str, FeatureDef],
    items: dict[str, ItemDef],
    recipes: tuple[RecipeDef, ...],
    placeable_items: frozenset[str],
) -> tuple[tuple[RecipeDef, ...], frozenset[str]]:
    terrains.update(EXTRA_TERRAINS)
    features.update(EXTRA_FEATURES)
    new_items = _item_defs()
    items.update(new_items)
    for item_id in EXTRA_PLACEABLES:
        if item_id in items and item_id not in features:
            item = items[item_id]
            tags = tuple(tag for tag in item.tags if tag in {"station", "building", "machine", "vehicle", "roof", "wall", "light", "warmth", "container"}) or ("station",)
            passable = "wall" not in item.tags
            features[item_id] = FeatureDef(item_id, item.name, (128, 104, 76), tags, passable, 999, None, 1, (), f"feature_{item_id}", False)
    merged_recipes = _merge_recipes(recipes, _recipe_defs())
    placeable = set(placeable_items)
    placeable.update(EXTRA_PLACEABLES)
    return merged_recipes, frozenset(placeable)


EXTRA_TERRAINS: dict[str, TerrainDef] = {
    "limestone_karst": TerrainDef("limestone_karst", "Limestone karst", (168, 166, 137), True, ("rock", "karst", "chalk"), "terrain_limestone_karst"),
    "basalt_field": TerrainDef("basalt_field", "Basalt field", (72, 76, 80), True, ("rock", "volcanic"), "terrain_basalt_field"),
    "salt_flat": TerrainDef("salt_flat", "Salt flat", (210, 206, 179), True, ("dry", "salt"), "terrain_salt_flat"),
    "flax_meadow": TerrainDef("flax_meadow", "Flax meadow", (102, 164, 86), True, ("earth", "grass", "fiber"), "terrain_flax_meadow"),
    "willow_wetland": TerrainDef("willow_wetland", "Willow wetland", (74, 126, 86), True, ("wet", "fiber"), "terrain_willow_wetland"),
    "chalk_downs": TerrainDef("chalk_downs", "Chalk downs", (190, 190, 160), True, ("hill", "chalk"), "terrain_chalk_downs"),
    "bee_grove": TerrainDef("bee_grove", "Bee grove", (88, 145, 68), True, ("forest", "flower"), "terrain_bee_grove"),
}


EXTRA_FEATURES: dict[str, FeatureDef] = {
    "flint_nodule": FeatureDef("flint_nodule", "Flint nodule", (74, 78, 78), ("stone", "sharp", "rock"), False, 2, "pickaxe", 1, (Loot("flint_shard", 1, 3), Loot("flint", 1, 1, 0.45)), "feature_flint_nodule"),
    "obsidian_glass": FeatureDef("obsidian_glass", "Obsidian glass", (30, 32, 38), ("stone", "sharp", "volcanic"), False, 3, "pickaxe", 2, (Loot("obsidian_shard", 1, 3),), "feature_obsidian_glass"),
    "limestone_outcrop": FeatureDef("limestone_outcrop", "Limestone outcrop", (178, 176, 145), ("stone", "rock", "lime"), False, 3, "pickaxe", 1, (Loot("limestone", 2, 5), Loot("chalk", 1, 2, 0.35)), "feature_limestone_outcrop"),
    "granite_outcrop": FeatureDef("granite_outcrop", "Granite outcrop", (116, 105, 103), ("stone", "rock"), False, 4, "pickaxe", 2, (Loot("granite", 2, 4),), "feature_granite_outcrop"),
    "slate_outcrop": FeatureDef("slate_outcrop", "Slate outcrop", (79, 88, 94), ("stone", "rock"), False, 3, "pickaxe", 1, (Loot("slate", 2, 5),), "feature_slate_outcrop"),
    "basalt_outcrop": FeatureDef("basalt_outcrop", "Basalt outcrop", (55, 58, 62), ("stone", "rock", "volcanic"), False, 4, "pickaxe", 2, (Loot("basalt", 2, 5),), "feature_basalt_outcrop"),
    "sulfur_deposit": FeatureDef("sulfur_deposit", "Sulfur deposit", (203, 181, 62), ("ore", "alchemy", "rock"), False, 2, "pickaxe", 1, (Loot("sulfur_stone", 1, 4),), "feature_sulfur_deposit"),
    "saltpeter_deposit": FeatureDef("saltpeter_deposit", "Saltpeter crust", (218, 214, 184), ("ore", "alchemy", "dry"), True, 1, "shovel", 1, (Loot("saltpeter", 1, 4),), "feature_saltpeter_deposit"),
    "kaolin_patch": FeatureDef("kaolin_patch", "Kaolin clay patch", (218, 214, 198), ("clay", "earth"), True, 1, "shovel", 1, (Loot("kaolin", 2, 5), Loot("high_quality_clay", 1, 2, 0.35)), "feature_kaolin_patch"),
    "gypsum_crystals": FeatureDef("gypsum_crystals", "Gypsum crystals", (207, 204, 190), ("stone", "rock"), False, 2, "pickaxe", 1, (Loot("gypsum", 1, 4),), "feature_gypsum_crystals"),
    "sandstone_outcrop": FeatureDef("sandstone_outcrop", "Sandstone outcrop", (188, 142, 88), ("stone", "rock", "sand"), False, 2, "pickaxe", 1, (Loot("sandstone", 2, 5),), "feature_sandstone_outcrop"),
    "rock_salt_crust": FeatureDef("rock_salt_crust", "Rock salt crust", (226, 220, 194), ("stone", "salt", "dry"), True, 1, "pickaxe", 1, (Loot("rock_salt", 1, 4),), "feature_rock_salt_crust"),
    "amber_root": FeatureDef("amber_root", "Amber-bearing roots", (193, 116, 36), ("tree", "gem"), False, 2, "axe", 1, (Loot("amber", 1, 2), Loot("resinous_wood", 1, 2)), "feature_amber_root"),
    "pearl_mussels": FeatureDef("pearl_mussels", "River pearl mussels", (176, 177, 162), ("water", "food", "gem"), True, 1, "fish", 1, (Loot("river_pearl", 1, 1, 0.35), Loot("shell", 1, 2)), "feature_pearl_mussels"),
    "flax_patch": FeatureDef("flax_patch", "Flax patch", (112, 158, 94), ("plant", "fiber"), True, 1, None, 1, (Loot("flax", 2, 5), Loot("flax_seed", 1, 2, 0.45)), "feature_flax_patch"),
    "hemp_patch": FeatureDef("hemp_patch", "Hemp patch", (86, 138, 75), ("plant", "fiber"), True, 1, None, 1, (Loot("hemp", 2, 5),), "feature_hemp_patch"),
    "cotton_bolls": FeatureDef("cotton_bolls", "Cotton bolls", (221, 219, 203), ("plant", "fiber"), True, 1, None, 1, (Loot("cotton", 2, 5),), "feature_cotton_bolls"),
    "willow_stand": FeatureDef("willow_stand", "Willow stand", (92, 139, 74), ("plant", "wood", "fiber"), False, 2, "axe", 1, (Loot("willow_withe", 2, 5), Loot("stick", 1, 3)), "feature_willow_stand"),
    "straw_patch": FeatureDef("straw_patch", "Dry straw patch", (182, 161, 83), ("plant", "fiber", "dry"), True, 1, None, 1, (Loot("dry_straw", 2, 5),), "feature_straw_patch"),
    "medicinal_flowers": FeatureDef("medicinal_flowers", "Medicinal flowers", (196, 184, 90), ("plant", "medicine"), True, 1, None, 1, (Loot("chamomile", 1, 3), Loot("yarrow", 1, 2, 0.65)), "feature_medicinal_flowers"),
    "mint_patch": FeatureDef("mint_patch", "Mint patch", (89, 162, 93), ("plant", "medicine"), True, 1, None, 1, (Loot("mint", 1, 4),), "feature_mint_patch"),
    "nettles": FeatureDef("nettles", "Nettles", (69, 134, 66), ("plant", "fiber", "medicine"), True, 1, None, 1, (Loot("nettle", 1, 4), Loot("grass_fiber", 1, 2)), "feature_nettles"),
    "beehive": FeatureDef("beehive", "Beehive", (196, 145, 54), ("food", "wax"), False, 2, "axe", 1, (Loot("beeswax", 1, 3), Loot("honeycomb", 1, 3)), "feature_beehive"),
}

EXTRA_FEATURES.update(
    {
        "rabbit": FeatureDef("rabbit", "Rabbit", (176, 165, 139), ("animal", "grass", "food"), True, 1, None, 1, (Loot("raw_meat", 1, 1), Loot("rabbit_fur", 1, 1, 0.7), Loot("bone", 1, 1, 0.45), Loot("sinew", 1, 1, 0.35)), "feature_rabbit"),
        "deer": FeatureDef("deer", "Deer", (146, 101, 59), ("animal", "forest", "food"), True, 2, "spear", 1, (Loot("raw_meat", 2, 5), Loot("rawhide", 1, 2), Loot("sinew", 1, 2, 0.65), Loot("bone", 1, 3, 0.8), Loot("deer_antler", 1, 2, 0.35)), "feature_deer"),
        "fox": FeatureDef("fox", "Fox", (196, 97, 45), ("animal", "forest"), True, 1, "spear", 1, (Loot("raw_meat", 1, 2, 0.65), Loot("fox_fur", 1, 1, 0.65), Loot("bone", 1, 1, 0.45), Loot("sinew", 1, 1, 0.35)), "feature_fox"),
        "boar": FeatureDef("boar", "Boar", (92, 70, 55), ("animal", "forest", "food"), True, 3, "spear", 1, (Loot("raw_meat", 2, 4), Loot("thick_hide", 1, 2, 0.65), Loot("boar_tusk", 1, 2, 0.45), Loot("fat", 1, 2, 0.55), Loot("bone", 1, 2, 0.75)), "feature_boar"),
        "wolf": FeatureDef("wolf", "Wolf", (89, 91, 94), ("animal", "predator", "hostile", "forest"), True, 3, "spear", 1, (Loot("raw_meat", 1, 3), Loot("hide", 1, 2, 0.7), Loot("thick_hide", 1, 1, 0.35), Loot("bone", 1, 2, 0.7), Loot("sinew", 1, 1, 0.5)), "feature_wolf"),
        "bear": FeatureDef("bear", "Bear", (84, 62, 45), ("animal", "predator", "hostile", "forest"), False, 6, "spear", 2, (Loot("raw_meat", 3, 6), Loot("hide", 2, 4), Loot("thick_hide", 2, 4), Loot("fat", 1, 3, 0.75), Loot("bone", 2, 4, 0.85)), "feature_bear"),
        "duck": FeatureDef("duck", "Duck", (129, 113, 70), ("animal", "wet", "food"), True, 1, "bow", 1, (Loot("raw_meat", 1, 2), Loot("egg", 1, 1, 0.25), Loot("bird_feather", 1, 3, 0.85), Loot("down", 1, 2, 0.55)), "feature_duck"),
        "gull": FeatureDef("gull", "Gull", (214, 217, 208), ("animal", "coast", "food"), True, 1, "bow", 1, (Loot("raw_meat", 1, 1), Loot("egg", 1, 1, 0.2), Loot("bird_feather", 1, 3, 0.85), Loot("down", 1, 1, 0.45)), "feature_gull"),
        "birch_tree": FeatureDef("birch_tree", "Birch tree", (187, 218, 182), ("tree", "wood"), False, 3, "axe", 1, (Loot("birch_log", 1, 3), Loot("stick", 1, 3), Loot("bark", 1, 2, 0.8), Loot("birch_bark", 1, 2, 0.65)), "feature_birch_tree"),
        "oak_tree": FeatureDef("oak_tree", "Oak tree", (69, 119, 52), ("tree", "wood"), False, 4, "axe", 1, (Loot("oak_log", 1, 4), Loot("stick", 1, 3), Loot("bark", 1, 3, 0.8), Loot("oak_acorn", 1, 3, 0.45)), "feature_oak_tree"),
        "pine_tree": FeatureDef("pine_tree", "Pine tree", (42, 104, 70), ("tree", "wood"), False, 3, "axe", 1, (Loot("pine_log", 1, 3), Loot("stick", 1, 4), Loot("resin", 1, 2, 0.55), Loot("pine_cone", 1, 3, 0.45), Loot("resinous_wood", 1, 2, 0.35)), "feature_pine_tree"),
        "fruit_tree": FeatureDef("fruit_tree", "Fruit tree", (62, 143, 68), ("tree", "wood", "food"), False, 3, "axe", 1, (Loot("fruit_log", 1, 3), Loot("berries", 2, 5), Loot("stick", 1, 3), Loot("nuts", 1, 3, 0.35), Loot("maple_sap", 1, 2, 0.25)), "feature_fruit_tree"),
    }
)


EXTRA_PLACEABLES = {
    "carpenter_table",
    "tanning_table",
    "stonecutting_table",
    "forge_bellows",
    "smelter",
    "blast_furnace",
    "jeweler_bench",
    "loom",
    "pottery_wheel",
    "oil_press",
    "straw_roof",
    "wattle_wall",
    "signal_fire",
    "cart",
    "windmill",
    "water_wheel",
    "pump",
    "steam_boiler",
    "steam_hammer",
}


ATLAS_SPRITES = {
    "flint_hammer",
    "stone_chisel",
    "wicker_basket",
    "straw_roof",
    "copper_nails",
    "iron_nails",
    "copper_saw",
    "iron_saw",
    "leather_belt",
    "cloth",
    "canvas",
    "charcoal_sack",
    "sling",
    "bolas",
    "atlatl",
    "longbow",
    "crossbow",
    "harpoon",
    "fish_trap",
    "crab_trap",
    "compost",
    "fertilizer",
    "watering_can",
    "wooden_bucket",
    "dried_meat",
    "smoked_fish",
    "vegetable_stew",
    "flatbread",
    "bandage",
    "splint",
    "honey_ointment",
    "wax_candle",
    "oil_lamp",
    "compass",
    "spyglass",
    "sextant",
}


def _item_defs() -> dict[str, ItemDef]:
    data: dict[str, ItemDef] = {}

    def add(item_id: str, name: str, tags: tuple[str, ...], max_stack: int = 99, durability: int = 0, tool_tags: tuple[str, ...] = (), tool_power: int = 0, food: int = 0, equip_slot: str = "", armor: int = 0) -> None:
        data[item_id] = ItemDef(item_id, name, tags, max_stack, durability, tool_tags, tool_power, food, f"item_{item_id}", equip_slot, armor)

    for item_id, name, tags in MATERIALS:
        add(item_id, name, tags)
    for item_id, name, tags, durability, tool_tags, power in TOOLS:
        add(item_id, name, tags, 1, durability, tool_tags, power)
    for item_id, name, tags, food in FOODS:
        add(item_id, name, tags, 16 if "meal" in tags else 24, food=food)
    for item_id, name, tags in STATIONS:
        add(item_id, name, tags, 1)
    return data


MATERIALS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("flint_shard", "Flint shard", ("material", "sharp", "stone")),
    ("obsidian_shard", "Obsidian shard", ("material", "sharp", "stone")),
    ("limestone", "Limestone", ("material", "stone", "lime")),
    ("granite", "Granite", ("material", "stone")),
    ("slate", "Slate", ("material", "stone")),
    ("basalt", "Basalt", ("material", "stone", "volcanic")),
    ("sulfur_stone", "Sulfur stone", ("material", "alchemy", "mineral")),
    ("saltpeter", "Saltpeter", ("material", "alchemy", "mineral")),
    ("high_quality_clay", "High quality clay", ("material", "clay")),
    ("kaolin", "Kaolin", ("material", "clay")),
    ("chalk", "Chalk", ("material", "mineral")),
    ("gypsum", "Gypsum", ("material", "mineral")),
    ("sandstone", "Sandstone", ("material", "stone", "sand")),
    ("rock_salt", "Rock salt", ("material", "salt")),
    ("amber", "Amber", ("material", "gem", "resin")),
    ("river_pearl", "River pearl", ("material", "gem")),
    ("flax", "Flax", ("material", "fiber", "plant")),
    ("hemp", "Hemp", ("material", "fiber", "plant")),
    ("cotton", "Cotton", ("material", "fiber", "plant")),
    ("reed_fiber", "Reed fiber", ("material", "fiber", "plant")),
    ("birch_bark", "Birch bark", ("material", "fiber", "wood")),
    ("willow_withe", "Willow withe", ("material", "fiber", "wood")),
    ("dry_straw", "Dry straw", ("material", "fiber", "dry")),
    ("resinous_wood", "Resinous wood", ("material", "wood", "fuel")),
    ("oak_acorn", "Oak acorn", ("material", "seed", "food")),
    ("pine_cone", "Pine cone", ("material", "seed", "fuel")),
    ("maple_sap", "Maple sap", ("material", "food", "sweet")),
    ("nuts", "Nuts", ("food", "plant")),
    ("chamomile", "Chamomile", ("material", "medicine", "plant")),
    ("yarrow", "Yarrow", ("material", "medicine", "plant")),
    ("mint", "Mint", ("material", "medicine", "plant")),
    ("nettle", "Nettle", ("material", "medicine", "fiber")),
    ("rawhide", "Rawhide", ("material", "leather")),
    ("thick_hide", "Thick hide", ("material", "leather")),
    ("rabbit_fur", "Rabbit fur", ("material", "fur")),
    ("fox_fur", "Fox fur", ("material", "fur")),
    ("sinew", "Sinew", ("material", "fiber", "animal")),
    ("bone", "Bone", ("material", "bone")),
    ("deer_antler", "Deer antler", ("material", "bone")),
    ("boar_tusk", "Boar tusk", ("material", "bone", "sharp")),
    ("bird_feather", "Bird feather", ("material", "feather")),
    ("down", "Down", ("material", "feather")),
    ("beeswax", "Beeswax", ("material", "wax")),
    ("honeycomb", "Honeycomb", ("food", "wax")),
    ("copper_nails", "Copper nails", ("material", "metal", "fastener")),
    ("iron_nails", "Iron nails", ("material", "metal", "fastener")),
    ("copper_rivets", "Copper rivets", ("material", "metal", "fastener")),
    ("iron_brackets", "Iron brackets", ("material", "metal", "fastener")),
    ("iron_chain", "Iron chain", ("material", "metal")),
    ("copper_wire", "Copper wire", ("material", "metal", "wire")),
    ("iron_wire", "Iron wire", ("material", "metal", "wire")),
    ("hardened_steel", "Hardened steel", ("material", "metal", "steel")),
    ("glass_tube", "Glass tube", ("material", "glass", "crafted")),
    ("glass_lens", "Glass lens", ("material", "glass", "crafted")),
    ("polished_plank", "Polished plank", ("material", "wood", "crafted")),
    ("leather_belt", "Leather belt", ("material", "leather", "crafted")),
    ("rope_coil", "Rope coil", ("material", "fiber", "crafted")),
    ("cloth", "Cloth roll", ("material", "fiber", "crafted")),
    ("canvas", "Canvas sheet", ("material", "fiber", "crafted")),
    ("charcoal_sack", "Charcoal sack", ("material", "fuel", "container")),
    ("sling_stones", "Sling stones", ("ammo", "stone")),
    ("flint_arrows", "Flint arrows", ("ammo", "sharp")),
    ("copper_arrows", "Copper arrows", ("ammo", "metal")),
    ("iron_arrows", "Iron arrows", ("ammo", "metal")),
    ("harpoons", "Harpoons", ("ammo", "metal", "fish")),
    ("fish_hook", "Fish hook", ("material", "fish")),
    ("copper_hook", "Copper hook", ("material", "fish", "metal")),
    ("iron_hook", "Iron hook", ("material", "fish", "metal")),
    ("float_bobber", "Float bobber", ("material", "fish", "wood")),
    ("bait", "Bait", ("material", "fish", "food")),
    ("fish_oil", "Fish oil", ("material", "oil", "fuel")),
    ("flax_seed", "Flax seeds", ("seed", "farm")),
    ("cabbage_seed", "Cabbage seeds", ("seed", "farm")),
    ("carrot_seed", "Carrot seeds", ("seed", "farm")),
    ("potato_seed", "Potato seeds", ("seed", "farm")),
    ("pumpkin_seed", "Pumpkin seeds", ("seed", "farm")),
    ("corn_seed", "Corn seeds", ("seed", "farm")),
    ("manure", "Manure", ("material", "farm")),
    ("compost", "Compost bag", ("material", "farm")),
    ("fertilizer", "Fertilizer sack", ("material", "farm")),
    ("fat", "Rendered fat", ("material", "oil", "animal")),
    ("brass", "Brass", ("material", "metal")),
)


TOOLS: tuple[tuple[str, str, tuple[str, ...], int, tuple[str, ...], int], ...] = (
    ("stone_hammer", "Stone hammer", ("tool", "hammer", "stone"), 55, ("hammer", "build"), 1),
    ("flint_hammer", "Flint hammer", ("tool", "hammer", "stone"), 70, ("hammer", "build"), 1),
    ("stone_chisel", "Stone chisel", ("tool", "chisel", "stone"), 60, ("chisel", "carve"), 1),
    ("stone_hoe", "Stone hoe", ("tool", "hoe", "farm"), 52, ("hoe", "farm"), 1),
    ("stone_sickle", "Stone sickle", ("tool", "sickle", "harvest"), 48, ("sickle", "harvest"), 1),
    ("wooden_mallet", "Wooden mallet", ("tool", "hammer", "wood"), 45, ("hammer", "build"), 1),
    ("copper_hammer", "Copper hammer", ("tool", "hammer", "metal"), 110, ("hammer", "build"), 2),
    ("copper_chisel", "Copper chisel", ("tool", "chisel", "metal"), 105, ("chisel", "carve"), 2),
    ("copper_hoe", "Copper hoe", ("tool", "hoe", "metal", "farm"), 100, ("hoe", "farm"), 2),
    ("copper_saw", "Copper saw", ("tool", "saw", "metal"), 100, ("saw", "wood"), 2),
    ("iron_saw", "Iron saw", ("tool", "saw", "metal"), 180, ("saw", "wood"), 3),
    ("iron_hammer", "Iron hammer", ("tool", "hammer", "metal"), 190, ("hammer", "build"), 3),
    ("iron_chisel", "Iron chisel", ("tool", "chisel", "metal"), 175, ("chisel", "carve"), 3),
    ("sling", "Sling", ("tool", "weapon", "ranged"), 60, ("sling", "weapon"), 1),
    ("bolas", "Bolas", ("tool", "weapon", "ranged"), 50, ("bolas", "weapon"), 1),
    ("atlatl", "Atlatl", ("tool", "weapon", "ranged"), 85, ("atlatl", "spear", "weapon"), 2),
    ("throwing_spear", "Throwing spear", ("tool", "weapon", "spear"), 70, ("spear", "weapon"), 2),
    ("shortbow", "Shortbow", ("tool", "weapon", "bow"), 80, ("bow", "hunt"), 2),
    ("longbow", "Longbow", ("tool", "weapon", "bow"), 125, ("bow", "hunt"), 3),
    ("composite_bow", "Composite bow", ("tool", "weapon", "bow"), 160, ("bow", "hunt"), 4),
    ("crossbow", "Crossbow", ("tool", "weapon", "bow"), 190, ("bow", "weapon"), 4),
    ("iron_spear", "Iron spear", ("tool", "weapon", "spear"), 180, ("spear", "weapon"), 3),
    ("halberd", "Halberd", ("tool", "weapon", "spear"), 220, ("spear", "weapon"), 4),
    ("mace", "Mace", ("tool", "weapon", "hammer"), 170, ("hammer", "weapon"), 3),
    ("warhammer", "War hammer", ("tool", "weapon", "hammer"), 230, ("hammer", "weapon"), 4),
    ("harpoon", "Harpoon", ("tool", "fish", "weapon"), 110, ("fish", "spear"), 2),
    ("fish_trap", "Fish trap", ("tool", "fish", "trap"), 90, ("trap", "fish"), 2),
    ("crab_trap", "Crab trap", ("tool", "fish", "trap"), 80, ("trap", "fish"), 2),
    ("watering_can", "Watering can", ("tool", "farm"), 100, ("water", "farm"), 1),
    ("wooden_bucket", "Wooden bucket", ("tool", "container"), 75, ("water",), 1),
    ("iron_bucket", "Iron bucket", ("tool", "container"), 160, ("water",), 2),
    ("torch_resin", "Resin torch", ("tool", "light"), 100, ("light",), 2),
    ("candle", "Candle", ("tool", "light"), 80, ("light",), 1),
    ("wax_candle", "Wax candle", ("tool", "light"), 130, ("light",), 2),
    ("oil_lamp", "Oil lamp", ("tool", "light"), 220, ("light",), 3),
    ("lantern", "Lantern", ("tool", "light"), 260, ("light",), 4),
    ("reflector", "Reflector", ("tool", "light"), 180, ("light",), 2),
    ("compass", "Compass", ("tool", "navigation"), 220, ("navigate",), 2),
    ("spyglass", "Spyglass", ("tool", "navigation"), 180, ("navigate",), 2),
    ("terrain_map", "Terrain map", ("tool", "navigation"), 80, ("navigate",), 1),
    ("sextant", "Sextant", ("tool", "navigation"), 220, ("navigate",), 3),
    ("barometer", "Barometer", ("tool", "navigation"), 160, ("weather",), 2),
    ("thermometer", "Thermometer", ("tool", "navigation"), 130, ("weather",), 2),
    ("mechanical_clock", "Mechanical clock", ("tool", "machine"), 240, ("machine",), 3),
    ("survey_tripod", "Survey tripod", ("tool", "navigation"), 160, ("navigate",), 2),
)


FOODS: tuple[tuple[str, str, tuple[str, ...], int], ...] = (
    ("dried_fish", "Dried fish", ("food", "cooked", "fish"), 20),
    ("dried_meat", "Dried meat", ("food", "cooked", "meat"), 22),
    ("smoked_fish", "Smoked fish", ("food", "cooked", "fish"), 26),
    ("jerky", "Jerky", ("food", "cooked", "meat"), 28),
    ("stew", "Stew", ("food", "cooked", "meal"), 32),
    ("vegetable_stew", "Vegetable stew", ("food", "cooked", "meal"), 30),
    ("fish_soup", "Fish soup", ("food", "cooked", "meal"), 34),
    ("fried_mushrooms", "Fried mushrooms", ("food", "cooked", "plant"), 20),
    ("nut_mix", "Nut mix", ("food", "plant"), 18),
    ("flatbread", "Flatbread", ("food", "cooked"), 22),
    ("cheese", "Cheese", ("food", "cooked"), 24),
    ("butter", "Butter", ("food", "cooked"), 18),
    ("chamomile_tea", "Chamomile infusion", ("food", "medicine", "tea"), 8),
    ("mint_tea", "Mint infusion", ("food", "medicine", "tea"), 8),
)


STATIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("carpenter_table", "Carpenter table", ("station", "wood", "crafted")),
    ("tanning_table", "Tanning table", ("station", "leather", "crafted")),
    ("stonecutting_table", "Stonecutting table", ("station", "stone", "crafted")),
    ("forge_bellows", "Forge bellows", ("station", "metal", "crafted")),
    ("smelter", "Smelter", ("station", "metal", "warmth", "crafted")),
    ("blast_furnace", "Blast furnace", ("station", "metal", "warmth", "crafted")),
    ("jeweler_bench", "Jeweler bench", ("station", "jewelry", "crafted")),
    ("loom", "Loom", ("station", "fiber", "crafted")),
    ("pottery_wheel", "Pottery wheel", ("station", "clay", "crafted")),
    ("oil_press", "Oil press", ("station", "oil", "crafted")),
    ("wicker_basket", "Wicker basket", ("container", "fiber", "crafted")),
    ("straw_roof", "Straw roof bundle", ("building", "roof", "fiber", "crafted")),
    ("wattle_wall", "Wattle wall", ("building", "wall", "fiber", "crafted")),
    ("signal_fire", "Signal fire", ("station", "light", "warmth", "crafted")),
    ("cart", "Cart", ("vehicle", "crafted")),
    ("windmill", "Windmill", ("machine", "crafted")),
    ("water_wheel", "Water wheel", ("machine", "crafted")),
    ("pump", "Pump", ("machine", "crafted")),
    ("steam_boiler", "Steam boiler", ("machine", "crafted")),
    ("steam_hammer", "Steam hammer", ("machine", "crafted")),
    ("bandage", "Bandage", ("medicine", "crafted")),
    ("improved_bandage", "Improved bandage", ("medicine", "crafted")),
    ("splint", "Splint", ("medicine", "crafted")),
    ("antiseptic", "Antiseptic", ("medicine", "crafted")),
    ("painkiller", "Painkiller", ("medicine", "crafted")),
    ("honey_ointment", "Honey ointment", ("medicine", "crafted")),
    ("compress", "Compress", ("medicine", "crafted")),
)


def _recipe_defs() -> tuple[RecipeDef, ...]:
    recipes: list[RecipeDef] = []

    def r(recipe_id: str, name: str, ingredients: Iterable[Ingredient], outputs: Iterable[tuple[str, int]], station: str | None = None, hint: str = "") -> None:
        recipes.append(RecipeDef(recipe_id, name, tuple(ingredients), tuple(outputs), station, hint))

    r("flint_hammer", "Flint hammer", (ing("flint_shard", 2), ing("stick"), ing("cordage")), (("flint_hammer", 1),), None, "sharper stone hammer")
    r("stone_hammer", "Stone hammer", (ing("stone", 2), ing("stick"), ing("cordage")), (("stone_hammer", 1),), None, "basic building hammer")
    r("stone_chisel", "Stone chisel", (ing("flint_shard"), ing("stick"), ing("cordage")), (("stone_chisel", 1),), None, "stone carving edge")
    r("stone_hoe", "Stone hoe", (ing("stone"), ing("stick", 2), ing("cordage")), (("stone_hoe", 1),), None, "basic farming tool")
    r("stone_sickle", "Stone sickle", (ing("flint_shard"), ing("stick"), ing("cordage")), (("stone_sickle", 1),), None, "harvesting blade")
    r("wooden_mallet", "Wooden mallet", (ing("tag:log"), ing("stick"), ing("cordage")), (("wooden_mallet", 1),), None, "soft hammer")
    r("rope_coil", "Rope coil", (ing("tag:fiber", 8),), (("rope_coil", 1),), None, "thick rope")
    r("reed_fiber", "Reed fiber", (ing("reeds", 2),), (("reed_fiber", 2),), None, "split reeds")
    r("cloth", "Cloth roll", (ing("flax", 3),), (("cloth", 1),), "loom", "woven cloth")
    r("cloth_from_cotton", "Cloth roll", (ing("cotton", 3),), (("cloth", 1),), "loom", "soft woven cloth")
    r("canvas", "Canvas sheet", (ing("hemp", 3), ing("cloth")), (("canvas", 1),), "loom", "sturdy fabric")
    r("leather_belt", "Leather belt", (ing("leather"), ing("copper_rivets")), (("leather_belt", 1),), "tanning_table", "strap and fastening")
    r("leather_from_rawhide", "Leather", (ing("rawhide", 2), ing("resin")), (("leather", 2),), "tanning_table", "worked rawhide")
    r("leather_from_thick_hide", "Leather", (ing("thick_hide"), ing("resin")), (("leather", 2),), "tanning_table", "heavy hide can be softened")
    r("cordage_from_sinew", "Cordage", (ing("sinew", 2),), (("cordage", 1),), None, "animal fiber binding")
    r("wicker_basket", "Wicker basket", (ing("willow_withe", 4), ing("cordage")), (("wicker_basket", 1),), None, "woven carrying basket")
    r("straw_roof", "Straw roof bundle", (ing("dry_straw", 6), ing("cordage")), (("straw_roof", 1),), "carpenter_table", "thatch roofing bundle")
    r("wattle_wall", "Wattle wall", (ing("willow_withe", 4), ing("dry_straw", 2), ing("clay_lump")), (("wattle_wall", 2),), "carpenter_table", "woven clay wall")
    r("carpenter_table", "Carpenter table", (ing("plank", 6), ing("stone_hammer"), ing("wooden_mallet")), (("carpenter_table", 1),), "workbench", "woodworking station")
    r("tanning_table", "Tanning table", (ing("plank", 4), ing("leather"), ing("stone_knife")), (("tanning_table", 1),), "workbench", "leatherworking station")
    r("stonecutting_table", "Stonecutting table", (ing("stone", 8), ing("stone_chisel"), ing("stone_hammer")), (("stonecutting_table", 1),), "workbench", "stone shaping station")
    r("forge_bellows", "Forge bellows", (ing("leather", 3), ing("plank", 3), ing("rope_coil")), (("forge_bellows", 1),), "workbench", "hotter metalwork")
    r("smelter", "Smelter", (ing("stone", 8), ing("clay_lump", 6), ing("forge_bellows")), (("smelter", 1),), "workbench", "dedicated ore furnace")
    r("blast_furnace", "Blast furnace", (ing("iron_ingot", 6), ing("basalt", 8), ing("forge_bellows"), ing("charcoal", 4)), (("blast_furnace", 1),), "smelter", "steel heat")
    r("jeweler_bench", "Jeweler bench", (ing("plank", 4), ing("glass_lens"), ing("copper_chisel")), (("jeweler_bench", 1),), "workbench", "fine gem work")
    r("loom", "Loom", (ing("plank", 5), ing("stick", 4), ing("cordage", 4)), (("loom", 1),), "workbench", "fiber station")
    r("pottery_wheel", "Pottery wheel", (ing("plank", 3), ing("stone", 4), ing("high_quality_clay", 2)), (("pottery_wheel", 1),), "workbench", "fine clay work")
    r("oil_press", "Oil press", (ing("plank", 5), ing("stone", 4), ing("iron_brackets", 2)), (("oil_press", 1),), "carpenter_table", "oil station")
    r("copper_nails", "Copper nails", (ing("copper_ingot"),), (("copper_nails", 8),), "workbench", "soft fasteners")
    r("iron_nails", "Iron nails", (ing("iron_ingot"),), (("iron_nails", 8),), "workbench", "hard fasteners")
    r("copper_rivets", "Copper rivets", (ing("copper_ingot"),), (("copper_rivets", 6),), "workbench", "metal fastening")
    r("iron_brackets", "Iron brackets", (ing("iron_ingot", 2),), (("iron_brackets", 2),), "workbench", "structural brackets")
    r("iron_chain", "Iron chain", (ing("iron_ingot", 3), ing("iron_hammer")), (("iron_chain", 1),), "workbench", "linked iron")
    r("copper_wire", "Copper wire", (ing("copper_ingot"),), (("copper_wire", 3),), "jeweler_bench", "drawn copper")
    r("iron_wire", "Iron wire", (ing("iron_ingot"),), (("iron_wire", 3),), "jeweler_bench", "drawn iron")
    r("hardened_steel", "Hardened steel", (ing("iron_ingot", 2), ing("charcoal", 2), ing("limestone")), (("hardened_steel", 1),), "blast_furnace", "carbon steel")
    r("brass", "Brass", (ing("copper_ingot", 2), ing("sulfur_stone")), (("brass", 1),), "smelter", "experimental copper alloy")
    r("glass_tube", "Glass tube", (ing("glass", 2),), (("glass_tube", 1),), "kiln", "thin glass tube")
    r("glass_lens", "Glass lens", (ing("glass", 2), ing("sand")), (("glass_lens", 1),), "jeweler_bench", "polished lens")
    r("polished_plank", "Polished plank", (ing("plank", 2), ing("resin")), (("polished_plank", 2),), "carpenter_table", "finished wood")
    r("stone_floor_from_limestone", "Stone floor", (ing("limestone", 2),), (("stone_floor", 2),), "stonecutting_table", "cut pale floor slabs")
    r("stone_floor_from_granite", "Stone floor", (ing("granite", 2),), (("stone_floor", 2),), "stonecutting_table", "cut hard floor slabs")
    r("stone_wall_from_slate", "Stone wall", (ing("slate", 3), ing("clay_lump")), (("stone_wall", 2),), "stonecutting_table", "layered stone wall")
    r("stone_wall_from_sandstone", "Stone wall", (ing("sandstone", 3), ing("clay_lump")), (("stone_wall", 2),), "stonecutting_table", "warm sandstone wall")
    r("chalk_to_lime", "Limestone", (ing("chalk", 2),), (("limestone", 1),), "kiln", "burned chalky stone")
    r("gypsum_plaster", "High quality clay", (ing("gypsum"), ing("clay_lump", 2)), (("high_quality_clay", 2),), "pottery_wheel", "fine plastered clay")
    r("copper_hammer", "Copper hammer", (ing("copper_ingot", 2), ing("stick"), ing("leather_belt")), (("copper_hammer", 1),), "workbench", "metal hammer")
    r("copper_chisel", "Copper chisel", (ing("copper_ingot"), ing("stick")), (("copper_chisel", 1),), "workbench", "metal chisel")
    r("copper_hoe", "Copper hoe", (ing("copper_ingot", 2), ing("stick", 2), ing("cordage")), (("copper_hoe", 1),), "workbench", "farm tool")
    r("copper_saw", "Copper saw", (ing("copper_ingot", 2), ing("plank"), ing("leather_belt")), (("copper_saw", 1),), "workbench", "wood cutting saw")
    r("iron_saw", "Iron saw", (ing("iron_ingot", 2), ing("polished_plank"), ing("leather_belt")), (("iron_saw", 1),), "workbench", "strong saw")
    r("iron_hammer", "Iron hammer", (ing("iron_ingot", 2), ing("stick"), ing("leather_belt")), (("iron_hammer", 1),), "workbench", "heavy hammer")
    r("iron_chisel", "Iron chisel", (ing("iron_ingot"), ing("stick")), (("iron_chisel", 1),), "workbench", "hard chisel")
    r("sling", "Sling", (ing("leather"), ing("cordage", 2)), (("sling", 1),), None, "simple ranged weapon")
    r("sling_stones", "Sling stones", (ing("pebble", 3),), (("sling_stones", 6),), None, "rounded ammo")
    r("bolas", "Bolas", (ing("stone", 2), ing("rope_coil")), (("bolas", 1),), None, "entangling weapon")
    r("atlatl", "Atlatl", (ing("stick", 2), ing("leather_belt")), (("atlatl", 1),), "workbench", "spear thrower")
    r("throwing_spear", "Throwing spear", (ing("stick", 2), ing("flint_shard"), ing("sinew")), (("throwing_spear", 1),), None, "light spear")
    r("shortbow", "Shortbow", (ing("stick", 2), ing("sinew")), (("shortbow", 1),), "workbench", "small bow")
    r("longbow", "Longbow", (ing("willow_withe", 2), ing("sinew", 2), ing("leather_belt")), (("longbow", 1),), "carpenter_table", "long ranged bow")
    r("composite_bow", "Composite bow", (ing("longbow"), ing("deer_antler"), ing("resin"), ing("sinew", 2)), (("composite_bow", 1),), "carpenter_table", "reinforced bow")
    r("crossbow", "Crossbow", (ing("iron_ingot", 2), ing("polished_plank", 2), ing("iron_wire"), ing("iron_brackets")), (("crossbow", 1),), "carpenter_table", "mechanical bow")
    r("flint_arrows", "Flint arrows", (ing("stick", 2), ing("flint_shard"), ing("bird_feather")), (("flint_arrows", 6),), "workbench", "flint arrowheads")
    r("copper_arrows", "Copper arrows", (ing("stick", 2), ing("copper_ingot"), ing("bird_feather")), (("copper_arrows", 6),), "workbench", "copper arrowheads")
    r("iron_arrows", "Iron arrows", (ing("stick", 2), ing("iron_ingot"), ing("bird_feather")), (("iron_arrows", 6),), "workbench", "iron arrowheads")
    r("iron_spear", "Iron spear", (ing("iron_ingot", 2), ing("stick", 2), ing("leather_belt")), (("iron_spear", 1),), "workbench", "metal spear")
    r("halberd", "Halberd", (ing("iron_spear"), ing("iron_axe"), ing("iron_brackets")), (("halberd", 1),), "workbench", "polearm")
    r("mace", "Mace", (ing("iron_ingot", 3), ing("stick"), ing("leather_belt")), (("mace", 1),), "workbench", "blunt weapon")
    r("warhammer", "War hammer", (ing("iron_hammer"), ing("iron_ingot", 2), ing("leather_belt")), (("warhammer", 1),), "workbench", "heavy weapon")
    r("fish_hook", "Fish hook", (ing("bone"),), (("fish_hook", 2),), None, "bone hook")
    r("copper_hook", "Copper hook", (ing("copper_wire"),), (("copper_hook", 2),), "workbench", "metal hook")
    r("iron_hook", "Iron hook", (ing("iron_wire"),), (("iron_hook", 2),), "workbench", "strong hook")
    r("float_bobber", "Float bobber", (ing("birch_bark"), ing("resin")), (("float_bobber", 2),), None, "fishing float")
    r("fish_trap", "Fish trap", (ing("willow_withe", 5), ing("cordage", 2)), (("fish_trap", 1),), "workbench", "passive fishing")
    r("crab_trap", "Crab trap", (ing("willow_withe", 4), ing("bait"), ing("cordage", 2)), (("crab_trap", 1),), "workbench", "passive crab fishing")
    r("harpoon", "Harpoon", (ing("iron_ingot"), ing("stick", 2), ing("rope_coil")), (("harpoon", 1),), "workbench", "fishing spear")
    r("harpoons", "Harpoons", (ing("iron_ingot"), ing("stick", 2), ing("rope_coil")), (("harpoons", 2),), "workbench", "harpoon ammo")
    r("bait", "Bait", (ing("mushroom"), ing("raw_meat")), (("bait", 3),), None, "fish bait")
    r("dried_fish", "Dried fish", (ing("raw_fish"), ing("rock_salt")), (("dried_fish", 1),), "campfire", "preserved fish")
    r("fish_oil", "Fish oil", (ing("raw_fish", 2),), (("fish_oil", 1),), "oil_press", "pressed fish oil")
    r("compost", "Compost bag", (ing("grass_fiber", 4), ing("mushroom"), ing("soil")), (("compost", 1),), None, "rotted plant matter")
    r("fertilizer", "Fertilizer sack", (ing("compost"), ing("manure"), ing("rock_salt")), (("fertilizer", 1),), None, "strong soil booster")
    r("watering_can", "Watering can", (ing("iron_ingot", 2), ing("copper_nails")), (("watering_can", 1),), "workbench", "watering crops")
    r("wooden_bucket", "Wooden bucket", (ing("plank", 3), ing("copper_nails"), ing("resin")), (("wooden_bucket", 1),), "carpenter_table", "liquid container")
    r("iron_bucket", "Iron bucket", (ing("iron_ingot", 3),), (("iron_bucket", 1),), "workbench", "metal bucket")
    r("dried_meat", "Dried meat", (ing("raw_meat"), ing("rock_salt")), (("dried_meat", 1),), "campfire", "preserved meat")
    r("smoked_fish", "Smoked fish", (ing("raw_fish"), ing("resinous_wood")), (("smoked_fish", 1),), "campfire", "smoked fish")
    r("jerky", "Jerky", (ing("raw_meat"), ing("rock_salt"), ing("resinous_wood")), (("jerky", 1),), "campfire", "smoked meat")
    r("stew", "Stew", (ing("raw_meat"), ing("mushroom"), ing("clay_pot")), (("stew", 1),), "campfire", "meat stew")
    r("vegetable_stew", "Vegetable stew", (ing("berries"), ing("mushroom"), ing("nuts"), ing("clay_pot")), (("vegetable_stew", 1),), "campfire", "plant stew")
    r("fish_soup", "Fish soup", (ing("raw_fish"), ing("seaweed"), ing("clay_pot")), (("fish_soup", 1),), "campfire", "fish soup")
    r("fried_mushrooms", "Fried mushrooms", (ing("mushroom", 2), ing("fish_oil")), (("fried_mushrooms", 1),), "campfire", "fried mushrooms")
    r("nut_mix", "Nut mix", (ing("nuts"), ing("berries")), (("nut_mix", 1),), None, "trail food")
    r("flatbread", "Flatbread", (ing("wild_seed", 3), ing("rock_salt")), (("flatbread", 1),), "campfire", "simple bread")
    r("cheese", "Cheese", (ing("rock_salt"), ing("clay_pot")), (("cheese", 1),), "campfire", "rough dairy stand-in")
    r("butter", "Butter", (ing("fish_oil"), ing("rock_salt")), (("butter", 1),), "oil_press", "fat spread")
    r("bandage", "Bandage", (ing("cloth"),), (("bandage", 2),), None, "wrap wounds")
    r("improved_bandage", "Improved bandage", (ing("bandage"), ing("chamomile")), (("improved_bandage", 1),), "tanning_table", "cleaner bandage")
    r("splint", "Splint", (ing("stick", 2), ing("cloth")), (("splint", 1),), None, "stabilize injury")
    r("antiseptic", "Antiseptic", (ing("sulfur_stone"), ing("mint"), ing("glass_bottle")), (("antiseptic", 1),), "potion_stand", "clean wounds")
    r("chamomile_tea", "Chamomile infusion", (ing("chamomile"), ing("glass_bottle")), (("chamomile_tea", 1),), "campfire", "calming tea")
    r("mint_tea", "Mint infusion", (ing("mint"), ing("glass_bottle")), (("mint_tea", 1),), "campfire", "refreshing tea")
    r("painkiller", "Painkiller", (ing("yarrow"), ing("mint"), ing("glass_bottle")), (("painkiller", 1),), "potion_stand", "pain relief")
    r("honey_ointment", "Honey ointment", (ing("honeycomb"), ing("beeswax"), ing("chamomile")), (("honey_ointment", 1),), "potion_stand", "soothing salve")
    r("compress", "Compress", (ing("cloth"), ing("mint"), ing("yarrow")), (("compress", 1),), None, "herbal compress")
    r("torch_resin", "Resin torch", (ing("torch"), ing("resinous_wood"), ing("resin")), (("torch_resin", 1),), None, "brighter torch")
    r("charcoal_sack", "Charcoal sack", (ing("charcoal", 6), ing("sack")), (("charcoal_sack", 1),), None, "packed fuel")
    r("candle", "Candle", (ing("fat", 1), ing("cordage")), (("candle", 1),), None, "simple candle")
    r("wax_candle", "Wax candle", (ing("beeswax"), ing("cordage")), (("wax_candle", 2),), None, "wax candle")
    r("oil_lamp", "Oil lamp", (ing("clay_pot"), ing("fish_oil"), ing("glass_tube")), (("oil_lamp", 1),), "kiln", "oil light")
    r("lantern", "Lantern", (ing("oil_lamp"), ing("iron_ingot"), ing("glass")), (("lantern", 1),), "workbench", "protected light")
    r("reflector", "Reflector", (ing("copper_ingot"), ing("glass_lens")), (("reflector", 1),), "jeweler_bench", "directed light")
    r("signal_fire", "Signal fire", (ing("resinous_wood", 4), ing("sulfur_stone"), ing("torch")), (("signal_fire", 1),), "workbench", "bright signal")
    r("compass", "Compass", (ing("iron_ingot"), ing("copper_wire"), ing("glass_lens")), (("compass", 1),), "jeweler_bench", "navigation tool")
    r("spyglass", "Spyglass", (ing("glass_lens", 2), ing("copper_ingot", 2), ing("leather_belt")), (("spyglass", 1),), "jeweler_bench", "long sight")
    r("terrain_map", "Terrain map", (ing("birch_bark", 2), ing("charcoal")), (("terrain_map", 1),), None, "drawn map")
    r("sextant", "Sextant", (ing("brass", 1), ing("glass_lens"), ing("copper_wire")), (("sextant", 1),), "jeweler_bench", "navigation instrument")
    r("barometer", "Barometer", (ing("glass_tube"), ing("copper_ingot"), ing("iron_wire")), (("barometer", 1),), "jeweler_bench", "weather instrument")
    r("thermometer", "Thermometer", (ing("glass_tube"), ing("copper_wire")), (("thermometer", 1),), "jeweler_bench", "temperature instrument")
    r("mechanical_clock", "Mechanical clock", (ing("iron_wire", 2), ing("copper_wire", 2), ing("glass_lens")), (("mechanical_clock", 1),), "jeweler_bench", "timekeeping")
    r("survey_tripod", "Survey tripod", (ing("polished_plank", 3), ing("iron_brackets")), (("survey_tripod", 1),), "carpenter_table", "surveying support")
    r("cart", "Cart", (ing("polished_plank", 6), ing("iron_brackets", 2), ing("iron_nails", 4)), (("cart", 1),), "carpenter_table", "hauling cart")
    r("windmill", "Windmill", (ing("polished_plank", 10), ing("canvas", 4), ing("iron_brackets", 4)), (("windmill", 1),), "carpenter_table", "wind machine")
    r("water_wheel", "Water wheel", (ing("polished_plank", 8), ing("iron_brackets", 4), ing("resin")), (("water_wheel", 1),), "carpenter_table", "water power")
    r("pump", "Pump", (ing("iron_ingot", 4), ing("leather_belt", 2), ing("glass_tube")), (("pump", 1),), "workbench", "water pump")
    r("steam_boiler", "Steam boiler", (ing("iron_ingot", 8), ing("copper_wire", 2), ing("pump")), (("steam_boiler", 1),), "blast_furnace", "steam pressure")
    r("steam_hammer", "Steam hammer", (ing("steam_boiler"), ing("hardened_steel", 4), ing("iron_chain", 2)), (("steam_hammer", 1),), "blast_furnace", "late metalworking")
    return tuple(recipes)


def _merge_recipes(base: tuple[RecipeDef, ...], extra: tuple[RecipeDef, ...]) -> tuple[RecipeDef, ...]:
    seen = {recipe.recipe_id for recipe in base}
    merged = list(base)
    for recipe in extra:
        if recipe.recipe_id not in seen:
            merged.append(recipe)
            seen.add(recipe.recipe_id)
    return tuple(merged)
