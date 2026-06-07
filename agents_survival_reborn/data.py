from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Color = tuple[int, int, int]
SpriteKind = Literal["terrain", "feature", "agent", "item", "ui"]


@dataclass(frozen=True)
class SpriteSpec:
    sprite_id: str
    name: str
    kind: SpriteKind
    size: tuple[int, int]
    path: str
    notes: str


@dataclass(frozen=True)
class TerrainDef:
    terrain_id: str
    name: str
    color: Color
    passable: bool = True
    tags: tuple[str, ...] = ()
    sprite: str = ""


@dataclass(frozen=True)
class Loot:
    item: str
    low: int
    high: int
    chance: float = 1.0


@dataclass(frozen=True)
class FeatureDef:
    feature_id: str
    name: str
    color: Color
    tags: tuple[str, ...] = ()
    passable: bool = False
    max_hp: int = 1
    required_tool: str | None = None
    min_power: int = 1
    loot: tuple[Loot, ...] = ()
    sprite: str = ""
    depletes: bool = True


@dataclass(frozen=True)
class ItemDef:
    item_id: str
    name: str
    tags: tuple[str, ...] = ()
    max_stack: int = 99
    durability: int = 0
    tool_tags: tuple[str, ...] = ()
    tool_power: int = 0
    food: int = 0
    sprite: str = ""
    equip_slot: str = ""
    armor: int = 0


@dataclass(frozen=True)
class Ingredient:
    query: str
    count: int

    @property
    def is_tag(self) -> bool:
        return self.query.startswith("tag:")

    @property
    def tag(self) -> str:
        return self.query[4:]


@dataclass(frozen=True)
class RecipeDef:
    recipe_id: str
    name: str
    ingredients: tuple[Ingredient, ...]
    outputs: tuple[tuple[str, int], ...]
    station: str | None = None
    hint: str = ""


def ing(query: str, count: int = 1) -> Ingredient:
    return Ingredient(query, count)


TERRAINS: dict[str, TerrainDef] = {
    "deep_water": TerrainDef("deep_water", "Deep water", (21, 61, 124), False, ("water",), "terrain_deep_water"),
    "shallow_water": TerrainDef("shallow_water", "Shallow water", (43, 129, 178), False, ("water",), "terrain_shallow_water"),
    "coast": TerrainDef("coast", "Coast", (215, 198, 132), True, ("sand", "coast"), "terrain_coast"),
    "sand": TerrainDef("sand", "Sand", (218, 194, 112), True, ("sand", "dry"), "terrain_sand"),
    "grass": TerrainDef("grass", "Grassland", (78, 155, 70), True, ("earth", "grass"), "terrain_grass"),
    "meadow": TerrainDef("meadow", "Meadow", (95, 177, 85), True, ("earth", "grass"), "terrain_meadow"),
    "forest_floor": TerrainDef("forest_floor", "Forest floor", (48, 116, 58), True, ("earth", "forest"), "terrain_forest_floor"),
    "rock": TerrainDef("rock", "Rocky cliffs", (100, 105, 108), True, ("rock", "mountain"), "terrain_rock"),
    "hills": TerrainDef("hills", "Hills", (126, 144, 90), True, ("hill", "earth"), "terrain_hills"),
    "clay_hills": TerrainDef("clay_hills", "Clay hills", (177, 111, 78), True, ("hill", "clay"), "terrain_clay_hills"),
    "swamp": TerrainDef("swamp", "Swamp", (65, 108, 78), True, ("wet", "earth"), "terrain_swamp"),
    "snow": TerrainDef("snow", "Snowfield", (222, 233, 234), True, ("cold",), "terrain_snow"),
    "tundra": TerrainDef("tundra", "Tundra", (151, 172, 156), True, ("cold", "earth"), "terrain_tundra"),
    "jungle": TerrainDef("jungle", "Jungle", (38, 128, 66), True, ("forest", "wet"), "terrain_jungle"),
    "mushroom_grove": TerrainDef("mushroom_grove", "Mushroom grove", (102, 94, 130), True, ("forest",), "terrain_mushroom_grove"),
    "badlands": TerrainDef("badlands", "Badlands", (168, 94, 57), True, ("dry", "rock"), "terrain_badlands"),
}


FEATURES: dict[str, FeatureDef] = {
    "cactus": FeatureDef("cactus", "Cactus", (45, 148, 75), ("plant", "desert", "food"), False, 2, None, 1, (Loot("cactus_flesh", 1, 3), Loot("cactus_spine", 1, 2, 0.6)), "feature_cactus"),
    "crab": FeatureDef("crab", "Crab", (207, 78, 55), ("animal", "coast", "food"), True, 1, None, 1, (Loot("crab_meat", 1, 2), Loot("shell", 1, 1, 0.5)), "feature_crab"),
    "fish_school": FeatureDef("fish_school", "Fish school", (129, 211, 228), ("fish", "water", "food"), True, 1, "fish", 1, (Loot("raw_fish", 1, 4),), "feature_fish_school"),
    "salmon_school": FeatureDef("salmon_school", "Salmon school", (226, 126, 102), ("fish", "water", "food"), True, 1, "fish", 1, (Loot("raw_fish", 2, 5),), "feature_salmon_school"),
    "eel": FeatureDef("eel", "Eel", (74, 88, 92), ("fish", "water", "food"), True, 1, "fish", 1, (Loot("raw_fish", 1, 2),), "feature_eel"),
    "kelp": FeatureDef("kelp", "Kelp", (49, 144, 91), ("plant", "water", "food"), True, 1, None, 1, (Loot("seaweed", 1, 4),), "feature_kelp"),
    "reef": FeatureDef("reef", "Reef", (236, 151, 110), ("water", "stone"), False, 2, "pickaxe", 1, (Loot("stone", 1, 2), Loot("shell", 1, 2, 0.5)), "feature_reef"),
    "grass_tuft": FeatureDef("grass_tuft", "Tall grass", (115, 195, 86), ("plant", "fiber"), True, 1, None, 1, (Loot("grass_fiber", 1, 3), Loot("wild_seed", 1, 1, 0.35)), "feature_grass_tuft"),
    "flower_patch": FeatureDef("flower_patch", "Flower patch", (226, 98, 152), ("plant", "flower"), True, 1, None, 1, (Loot("flower", 1, 3),), "feature_flower_patch"),
    "berry_bush": FeatureDef("berry_bush", "Berry bush", (105, 65, 139), ("plant", "food"), False, 1, None, 1, (Loot("berries", 2, 5), Loot("blueberries", 1, 3, 0.45), Loot("stick", 1, 2, 0.3)), "feature_berry_bush"),
    "herbs": FeatureDef("herbs", "Herbs", (136, 195, 85), ("plant", "medicine"), True, 1, None, 1, (Loot("herb", 1, 3),), "feature_herbs"),
    "reeds": FeatureDef("reeds", "Reeds", (128, 169, 84), ("plant", "fiber", "wet"), True, 1, None, 1, (Loot("reeds", 1, 4),), "feature_reeds"),
    "mushrooms": FeatureDef("mushrooms", "Mushrooms", (176, 103, 167), ("plant", "food"), True, 1, None, 1, (Loot("mushroom", 1, 4),), "feature_mushrooms"),
    "rabbit": FeatureDef("rabbit", "Rabbit", (176, 165, 139), ("animal", "grass", "food"), True, 1, None, 1, (Loot("raw_meat", 1, 1),), "feature_rabbit"),
    "deer": FeatureDef("deer", "Deer", (146, 101, 59), ("animal", "forest", "food"), True, 2, "spear", 1, (Loot("raw_meat", 2, 5),), "feature_deer"),
    "fox": FeatureDef("fox", "Fox", (196, 97, 45), ("animal", "forest"), True, 1, "spear", 1, (Loot("raw_meat", 1, 2, 0.65),), "feature_fox"),
    "boar": FeatureDef("boar", "Boar", (92, 70, 55), ("animal", "forest", "food"), True, 3, "spear", 1, (Loot("raw_meat", 2, 4),), "feature_boar"),
    "wolf": FeatureDef("wolf", "Wolf", (89, 91, 94), ("animal", "predator", "hostile", "forest"), True, 3, "spear", 1, (Loot("raw_meat", 1, 3), Loot("hide", 1, 2, 0.7)), "feature_wolf"),
    "bear": FeatureDef("bear", "Bear", (84, 62, 45), ("animal", "predator", "hostile", "forest"), False, 6, "spear", 2, (Loot("raw_meat", 3, 6), Loot("hide", 2, 4)), "feature_bear"),
    "snake": FeatureDef("snake", "Snake", (74, 116, 62), ("animal", "predator", "hostile", "dry"), True, 2, "blade", 1, (Loot("raw_meat", 1, 1), Loot("venom_sac", 1, 1, 0.55)), "feature_snake"),
    "frog": FeatureDef("frog", "Frog", (68, 151, 78), ("animal", "wet", "food"), True, 1, None, 1, (Loot("raw_meat", 1, 1, 0.55),), "feature_frog"),
    "duck": FeatureDef("duck", "Duck", (129, 113, 70), ("animal", "wet", "food"), True, 1, "bow", 1, (Loot("raw_meat", 1, 2), Loot("egg", 1, 1, 0.25)), "feature_duck"),
    "gull": FeatureDef("gull", "Gull", (214, 217, 208), ("animal", "coast", "food"), True, 1, "bow", 1, (Loot("raw_meat", 1, 1), Loot("egg", 1, 1, 0.2)), "feature_gull"),
    "turtle": FeatureDef("turtle", "Turtle", (78, 125, 86), ("animal", "coast", "food"), True, 2, None, 1, (Loot("raw_meat", 1, 2), Loot("shell", 1, 1, 0.8)), "feature_turtle"),
    "birch_tree": FeatureDef("birch_tree", "Birch tree", (187, 218, 182), ("tree", "wood"), False, 3, "axe", 1, (Loot("birch_log", 1, 3), Loot("stick", 1, 3), Loot("bark", 1, 2, 0.8)), "feature_birch_tree"),
    "oak_tree": FeatureDef("oak_tree", "Oak tree", (69, 119, 52), ("tree", "wood"), False, 4, "axe", 1, (Loot("oak_log", 1, 4), Loot("stick", 1, 3), Loot("bark", 1, 3, 0.8)), "feature_oak_tree"),
    "pine_tree": FeatureDef("pine_tree", "Pine tree", (42, 104, 70), ("tree", "wood"), False, 3, "axe", 1, (Loot("pine_log", 1, 3), Loot("stick", 1, 4), Loot("resin", 1, 2, 0.55)), "feature_pine_tree"),
    "fruit_tree": FeatureDef("fruit_tree", "Fruit tree", (62, 143, 68), ("tree", "wood", "food"), False, 3, "axe", 1, (Loot("fruit_log", 1, 3), Loot("berries", 2, 5), Loot("stick", 1, 3)), "feature_fruit_tree"),
    "stone_outcrop": FeatureDef("stone_outcrop", "Stone outcrop", (126, 130, 132), ("stone", "rock"), False, 3, "pickaxe", 1, (Loot("stone", 2, 5), Loot("flint", 1, 2, 0.35)), "feature_stone_outcrop"),
    "cave": FeatureDef("cave", "Cave mouth", (45, 45, 50), ("cave", "ore", "rock"), False, 1, "pickaxe", 1, (), "feature_cave", False),
    "coal_vein": FeatureDef("coal_vein", "Coal vein", (42, 42, 44), ("ore", "rock"), False, 2, "pickaxe", 1, (Loot("coal", 2, 5), Loot("stone", 1, 2, 0.65)), "feature_coal_vein"),
    "copper_vein": FeatureDef("copper_vein", "Copper vein", (185, 105, 64), ("ore", "metal", "rock"), False, 3, "pickaxe", 1, (Loot("copper_ore", 1, 4), Loot("stone", 1, 3, 0.75)), "feature_copper_vein"),
    "iron_vein": FeatureDef("iron_vein", "Iron vein", (154, 139, 126), ("ore", "metal", "rock"), False, 4, "pickaxe", 2, (Loot("iron_ore", 1, 4), Loot("stone", 1, 3, 0.8)), "feature_iron_vein"),
    "gold_vein": FeatureDef("gold_vein", "Gold vein", (231, 185, 68), ("ore", "metal", "rock"), False, 4, "pickaxe", 2, (Loot("gold_ore", 1, 3), Loot("stone", 1, 2, 0.7)), "feature_gold_vein"),
    "diamond_vein": FeatureDef("diamond_vein", "Diamond vein", (89, 221, 226), ("ore", "gem", "rock"), False, 5, "pickaxe", 3, (Loot("diamond", 1, 2), Loot("stone", 1, 4, 0.9)), "feature_diamond_vein"),
    "clay_patch": FeatureDef("clay_patch", "Clay patch", (177, 111, 82), ("clay", "earth"), True, 1, "shovel", 1, (Loot("clay_lump", 2, 5),), "feature_clay_patch"),
    "snowdrift": FeatureDef("snowdrift", "Snowdrift", (236, 244, 245), ("snow", "cold"), True, 1, "shovel", 1, (Loot("snow", 2, 6),), "feature_snowdrift"),
    "workbench": FeatureDef("workbench", "Workbench", (134, 92, 56), ("station",), True, 999, None, 1, (), "feature_workbench", False),
    "campfire": FeatureDef("campfire", "Campfire", (220, 103, 44), ("station", "warmth"), True, 999, None, 1, (), "feature_campfire", False),
    "kiln": FeatureDef("kiln", "Kiln", (128, 90, 74), ("station", "warmth"), True, 999, None, 1, (), "feature_kiln", False),
    "potion_stand": FeatureDef("potion_stand", "Potion stand", (104, 80, 136), ("station", "alchemy"), True, 999, None, 1, (), "feature_potion_stand", False),
    "tent": FeatureDef("tent", "Tent", (92, 128, 96), ("shelter", "rest"), True, 999, None, 1, (), "feature_tent", False),
    "wooden_crate": FeatureDef("wooden_crate", "Wooden crate", (121, 82, 45), ("storage", "wood"), True, 999, None, 1, (), "feature_wooden_crate", False),
    "wooden_door": FeatureDef("wooden_door", "Wooden door", (116, 74, 42), ("building", "wood"), True, 999, None, 1, (), "feature_wooden_door", False),
    "wooden_wall": FeatureDef("wooden_wall", "Wooden wall", (116, 83, 52), ("wall", "building", "wood"), False, 999, None, 1, (), "feature_wooden_wall", False),
    "stone_wall": FeatureDef("stone_wall", "Stone wall", (112, 116, 118), ("wall", "building", "stone"), False, 999, None, 1, (), "feature_stone_wall", False),
    "bedroll": FeatureDef("bedroll", "Bedroll", (82, 122, 66), ("rest", "camp"), True, 999, None, 1, (), "feature_bedroll", False),
}


ITEMS: dict[str, ItemDef] = {
    "soil": ItemDef("soil", "Handful of soil", ("material", "earth"), sprite="item_soil"),
    "sand": ItemDef("sand", "Clean sand", ("material", "sand"), sprite="item_sand"),
    "clay_lump": ItemDef("clay_lump", "Clay lump", ("material", "clay"), sprite="item_clay_lump"),
    "snow": ItemDef("snow", "Packed snow", ("material", "cold"), sprite="item_snow"),
    "stone": ItemDef("stone", "Stone", ("material", "rock"), sprite="item_stone"),
    "pebble": ItemDef("pebble", "Pebble", ("material", "rock"), sprite="item_pebble"),
    "flint": ItemDef("flint", "Flint", ("material", "sharp"), sprite="item_flint"),
    "coal": ItemDef("coal", "Coal", ("material", "fuel", "ore"), sprite="item_coal"),
    "copper_ore": ItemDef("copper_ore", "Copper ore", ("material", "ore", "metal"), sprite="item_copper_ore"),
    "iron_ore": ItemDef("iron_ore", "Iron ore", ("material", "ore", "metal"), sprite="item_iron_ore"),
    "gold_ore": ItemDef("gold_ore", "Gold ore", ("material", "ore", "metal"), sprite="item_gold_ore"),
    "diamond": ItemDef("diamond", "Rough diamond", ("material", "gem"), sprite="item_diamond"),
    "shell": ItemDef("shell", "Shell", ("material", "coast"), sprite="item_shell"),
    "glass": ItemDef("glass", "Glass", ("material", "crafted"), sprite="item_glass"),
    "glass_bottle": ItemDef("glass_bottle", "Glass bottle", ("container", "glass", "alchemy"), max_stack=16, sprite="item_glass_bottle"),
    "charcoal": ItemDef("charcoal", "Charcoal", ("material", "fuel"), sprite="item_charcoal"),
    "copper_ingot": ItemDef("copper_ingot", "Copper ingot", ("material", "metal"), sprite="item_copper_ingot"),
    "iron_ingot": ItemDef("iron_ingot", "Iron ingot", ("material", "metal"), sprite="item_iron_ingot"),
    "gold_ingot": ItemDef("gold_ingot", "Gold ingot", ("material", "metal"), sprite="item_gold_ingot"),
    "hide": ItemDef("hide", "Hide", ("material", "leather"), sprite="item_hide"),
    "leather": ItemDef("leather", "Leather", ("material", "leather", "crafted"), sprite="item_leather"),
    "venom_sac": ItemDef("venom_sac", "Venom sac", ("material", "alchemy", "venom"), sprite="item_venom_sac"),
    "grass_fiber": ItemDef("grass_fiber", "Grass fiber", ("material", "fiber"), sprite="item_grass_fiber"),
    "reeds": ItemDef("reeds", "Reeds", ("material", "fiber"), sprite="item_reeds"),
    "cordage": ItemDef("cordage", "Cordage", ("material", "fiber", "crafted"), sprite="item_cordage"),
    "flower": ItemDef("flower", "Wild flower", ("material", "plant"), sprite="item_flower"),
    "herb": ItemDef("herb", "Bitter herb", ("material", "medicine"), food=1, sprite="item_herb"),
    "mushroom": ItemDef("mushroom", "Mushroom", ("food", "plant"), food=6, sprite="item_mushroom"),
    "berries": ItemDef("berries", "Berries", ("food", "plant"), food=8, sprite="item_berries"),
    "blueberries": ItemDef("blueberries", "Blueberries", ("food", "plant"), food=9, sprite="item_blueberries"),
    "wild_seed": ItemDef("wild_seed", "Wild seed", ("material", "plant"), sprite="item_wild_seed"),
    "seaweed": ItemDef("seaweed", "Seaweed", ("food", "plant"), food=4, sprite="item_seaweed"),
    "cactus_flesh": ItemDef("cactus_flesh", "Cactus flesh", ("food", "plant"), food=7, sprite="item_cactus_flesh"),
    "cactus_spine": ItemDef("cactus_spine", "Cactus spine", ("material", "sharp"), sprite="item_cactus_spine"),
    "raw_fish": ItemDef("raw_fish", "Raw fish", ("food", "raw", "fish"), food=9, sprite="item_raw_fish"),
    "crab_meat": ItemDef("crab_meat", "Crab meat", ("food", "raw"), food=8, sprite="item_crab_meat"),
    "raw_meat": ItemDef("raw_meat", "Raw meat", ("food", "raw", "meat"), food=10, sprite="item_raw_meat"),
    "cooked_fish": ItemDef("cooked_fish", "Cooked fish", ("food", "cooked"), food=24, sprite="item_cooked_fish"),
    "cooked_crab": ItemDef("cooked_crab", "Cooked crab", ("food", "cooked"), food=20, sprite="item_cooked_crab"),
    "cooked_meat": ItemDef("cooked_meat", "Cooked meat", ("food", "cooked", "meat"), food=26, sprite="item_cooked_meat"),
    "egg": ItemDef("egg", "Egg", ("food", "raw"), food=6, sprite="item_egg"),
    "fried_egg": ItemDef("fried_egg", "Fried egg", ("food", "cooked"), food=18, sprite="item_fried_egg"),
    "bread": ItemDef("bread", "Bread", ("food", "cooked"), food=20, sprite="item_bread"),
    "birch_log": ItemDef("birch_log", "Birch log", ("material", "wood", "log"), sprite="item_birch_log"),
    "oak_log": ItemDef("oak_log", "Oak log", ("material", "wood", "log"), sprite="item_oak_log"),
    "pine_log": ItemDef("pine_log", "Pine log", ("material", "wood", "log"), sprite="item_pine_log"),
    "fruit_log": ItemDef("fruit_log", "Fruitwood log", ("material", "wood", "log"), sprite="item_fruit_log"),
    "stick": ItemDef("stick", "Stick", ("material", "wood"), sprite="item_stick"),
    "bark": ItemDef("bark", "Bark", ("material", "wood", "fiber"), sprite="item_bark"),
    "resin": ItemDef("resin", "Resin", ("material", "glue"), sprite="item_resin"),
    "plank": ItemDef("plank", "Plank", ("material", "wood", "crafted"), sprite="item_plank"),
    "clay_pot": ItemDef("clay_pot", "Clay pot", ("container", "crafted", "clay"), max_stack=16, sprite="item_clay_pot"),
    "workbench": ItemDef("workbench", "Workbench", ("station", "crafted"), 1, sprite="item_workbench"),
    "campfire": ItemDef("campfire", "Campfire", ("station", "crafted"), 1, sprite="item_campfire"),
    "kiln": ItemDef("kiln", "Kiln", ("station", "crafted"), 1, sprite="item_kiln"),
    "potion_stand": ItemDef("potion_stand", "Potion stand", ("station", "crafted", "alchemy"), 1, sprite="item_potion_stand"),
    "torch": ItemDef("torch", "Torch", ("tool", "light", "crafted"), max_stack=8, durability=80, tool_tags=("light",), tool_power=1, sprite="item_torch"),
    "wooden_shield": ItemDef("wooden_shield", "Wooden shield", ("tool", "defense", "crafted"), max_stack=1, durability=120, tool_tags=("shield",), tool_power=1, sprite="item_wooden_shield"),
    "copper_axe": ItemDef("copper_axe", "Copper axe", ("tool", "axe", "weapon", "metal"), 1, 105, ("axe", "chop", "weapon"), 2, sprite="item_copper_axe"),
    "copper_sword": ItemDef("copper_sword", "Copper sword", ("tool", "weapon", "metal"), 1, 115, ("sword", "weapon", "spear"), 2, sprite="item_copper_sword"),
    "iron_axe": ItemDef("iron_axe", "Iron axe", ("tool", "axe", "weapon", "metal"), 1, 175, ("axe", "chop", "weapon"), 3, sprite="item_iron_axe"),
    "iron_sword": ItemDef("iron_sword", "Iron sword", ("tool", "weapon", "metal"), 1, 190, ("sword", "weapon", "spear"), 3, sprite="item_iron_sword"),
    "diamond_edged_pickaxe": ItemDef("diamond_edged_pickaxe", "Diamond-edged pickaxe", ("tool", "pickaxe", "gem"), 1, 360, ("pickaxe", "mine"), 6, sprite="item_diamond_edged_pickaxe"),
    "diamond_edged_sword": ItemDef("diamond_edged_sword", "Diamond-edged sword", ("tool", "weapon", "gem"), 1, 340, ("sword", "weapon", "spear"), 5, sprite="item_diamond_edged_sword"),
    "wooden_floor": ItemDef("wooden_floor", "Wooden floor", ("building", "floor", "wood", "crafted"), max_stack=32, sprite="item_wooden_floor"),
    "stone_floor": ItemDef("stone_floor", "Stone floor", ("building", "floor", "stone", "crafted"), max_stack=32, sprite="item_stone_floor"),
    "wooden_wall": ItemDef("wooden_wall", "Wooden wall", ("building", "wall", "wood", "crafted"), max_stack=32, sprite="item_wooden_wall"),
    "stone_wall": ItemDef("stone_wall", "Stone wall", ("building", "wall", "stone", "crafted"), max_stack=32, sprite="item_stone_wall"),
    "wooden_crate": ItemDef("wooden_crate", "Wooden crate", ("container", "crafted", "wood"), max_stack=16, sprite="item_wooden_crate"),
    "wooden_door": ItemDef("wooden_door", "Wooden door", ("building", "crafted", "wood"), max_stack=16, sprite="item_wooden_door"),
    "bedroll": ItemDef("bedroll", "Bedroll", ("crafted", "rest"), max_stack=1, sprite="item_bedroll"),
    "tent": ItemDef("tent", "Tent", ("shelter", "crafted", "rest"), max_stack=1, sprite="item_tent"),
    "sack": ItemDef("sack", "Sack", ("container", "crafted", "fiber"), max_stack=16, sprite="item_sack"),
    "copper_ring": ItemDef("copper_ring", "Copper ring", ("jewelry", "copper", "crafted"), max_stack=10, sprite="item_copper_ring", equip_slot="ring"),
    "gold_ring": ItemDef("gold_ring", "Gold ring", ("jewelry", "gold", "crafted"), max_stack=10, sprite="item_gold_ring", equip_slot="ring"),
    "gold_necklace": ItemDef("gold_necklace", "Gold necklace", ("jewelry", "gold", "crafted"), max_stack=1, sprite="item_gold_necklace", equip_slot="neck"),
    "diamond_ring": ItemDef("diamond_ring", "Diamond ring", ("jewelry", "diamond", "crafted"), max_stack=10, sprite="item_diamond_ring", equip_slot="ring"),
    "diamond_amulet": ItemDef("diamond_amulet", "Diamond amulet", ("jewelry", "diamond", "crafted"), max_stack=1, sprite="item_diamond_amulet", equip_slot="neck"),
    "leather_cap": ItemDef("leather_cap", "Leather cap", ("armor", "leather", "crafted"), 1, 90, sprite="item_leather_cap", equip_slot="head", armor=1),
    "leather_gloves": ItemDef("leather_gloves", "Leather gloves", ("armor", "leather", "crafted"), 1, 80, sprite="item_leather_gloves", equip_slot="hands", armor=1),
    "leather_tunic": ItemDef("leather_tunic", "Leather tunic", ("armor", "leather", "crafted"), 1, 130, sprite="item_leather_tunic", equip_slot="chest", armor=2),
    "leather_pants": ItemDef("leather_pants", "Leather pants", ("armor", "leather", "crafted"), 1, 110, sprite="item_leather_pants", equip_slot="legs", armor=1),
    "leather_boots": ItemDef("leather_boots", "Leather boots", ("armor", "leather", "crafted"), 1, 90, sprite="item_leather_boots", equip_slot="feet", armor=1),
    "iron_helmet": ItemDef("iron_helmet", "Iron helmet", ("armor", "iron", "crafted"), 1, 220, sprite="item_iron_helmet", equip_slot="head", armor=3),
    "iron_gauntlets": ItemDef("iron_gauntlets", "Iron gauntlets", ("armor", "iron", "crafted"), 1, 190, sprite="item_iron_gauntlets", equip_slot="hands", armor=2),
    "iron_chestplate": ItemDef("iron_chestplate", "Iron chestplate", ("armor", "iron", "crafted"), 1, 320, sprite="item_iron_chestplate", equip_slot="chest", armor=5),
    "iron_greaves": ItemDef("iron_greaves", "Iron greaves", ("armor", "iron", "crafted"), 1, 260, sprite="item_iron_greaves", equip_slot="legs", armor=3),
    "iron_boots": ItemDef("iron_boots", "Iron boots", ("armor", "iron", "crafted"), 1, 210, sprite="item_iron_boots", equip_slot="feet", armor=2),
    "healing_potion": ItemDef("healing_potion", "Healing potion", ("potion", "medicine", "crafted"), max_stack=8, food=2, sprite="item_healing_potion"),
    "stamina_potion": ItemDef("stamina_potion", "Stamina potion", ("potion", "crafted"), max_stack=8, food=1, sprite="item_stamina_potion"),
    "antidote": ItemDef("antidote", "Antidote", ("potion", "medicine", "crafted"), max_stack=8, food=1, sprite="item_antidote"),
    "stone_knife": ItemDef("stone_knife", "Stone knife", ("tool", "blade"), 1, 38, ("blade", "harvest"), 1, sprite="item_stone_knife"),
    "stone_axe": ItemDef("stone_axe", "Stone axe", ("tool", "axe"), 1, 48, ("axe", "chop"), 1, sprite="item_stone_axe"),
    "stone_shovel": ItemDef("stone_shovel", "Stone shovel", ("tool", "shovel"), 1, 45, ("shovel", "dig"), 1, sprite="item_stone_shovel"),
    "wooden_pickaxe": ItemDef("wooden_pickaxe", "Wooden pickaxe", ("tool", "pickaxe", "wood"), 1, 32, ("pickaxe", "mine"), 1, sprite="item_wooden_pickaxe"),
    "stone_pickaxe": ItemDef("stone_pickaxe", "Stone pickaxe", ("tool", "pickaxe"), 1, 55, ("pickaxe", "mine"), 1, sprite="item_stone_pickaxe"),
    "wooden_spear": ItemDef("wooden_spear", "Wooden spear", ("tool", "weapon"), 1, 40, ("spear", "hunt"), 1, sprite="item_wooden_spear"),
    "bow": ItemDef("bow", "Bow", ("tool", "weapon"), 1, 75, ("bow", "hunt"), 2, sprite="item_bow"),
    "arrow": ItemDef("arrow", "Arrow", ("ammo", "sharp", "crafted"), sprite="item_arrow"),
    "fishing_rod": ItemDef("fishing_rod", "Fishing rod", ("tool", "fishing"), 1, 45, ("fishing", "fish"), 1, sprite="item_fishing_rod"),
    "fish_net": ItemDef("fish_net", "Fish net", ("tool", "net"), 1, 65, ("net", "fish"), 2, sprite="item_fish_net"),
    "copper_pickaxe": ItemDef("copper_pickaxe", "Copper pickaxe", ("tool", "metal"), 1, 95, ("pickaxe", "mine"), 2, sprite="item_copper_pickaxe"),
    "iron_pickaxe": ItemDef("iron_pickaxe", "Iron pickaxe", ("tool", "metal"), 1, 155, ("pickaxe", "mine"), 3, sprite="item_iron_pickaxe"),
    "diamond_pickaxe": ItemDef("diamond_pickaxe", "Diamond pickaxe", ("tool", "gem"), 1, 280, ("pickaxe", "mine"), 5, sprite="item_diamond_pickaxe"),
}


RECIPES: tuple[RecipeDef, ...] = (
    RecipeDef("cordage_from_fiber", "Cordage", (ing("tag:fiber", 3),), (("cordage", 1),), None, "fiber can be twisted together"),
    RecipeDef("stone_from_pebbles", "Knapped stone", (ing("pebble", 3),), (("stone", 1),), None, "small stones can be knapped into a usable head"),
    RecipeDef("sticks_from_log", "Split sticks", (ing("tag:log", 1),), (("stick", 4),), None, "logs split into sticks"),
    RecipeDef("planks_from_log", "Rough planks", (ing("tag:log", 1),), (("plank", 3),), None, "logs split into planks"),
    RecipeDef("stone_knife", "Stone knife", (ing("flint"), ing("stick"), ing("cordage")), (("stone_knife", 1),), None, "flint plus handle"),
    RecipeDef("stone_axe", "Stone axe", (ing("stone", 2), ing("stick"), ing("cordage")), (("stone_axe", 1),), None, "stone head, handle, binding"),
    RecipeDef("pebble_axe", "Stone axe", (ing("pebble", 2), ing("stick"), ing("cordage")), (("stone_axe", 1),), None, "small stones can still bite into wood"),
    RecipeDef("stone_shovel", "Stone shovel", (ing("stone"), ing("stick", 2), ing("cordage")), (("stone_shovel", 1),), None, "digging tool"),
    RecipeDef("wooden_pickaxe", "Wooden pickaxe", (ing("stick", 3), ing("cordage"), ing("flint")), (("wooden_pickaxe", 1),), None, "crude mining tool"),
    RecipeDef("stone_pickaxe", "Stone pickaxe", (ing("stone", 3), ing("stick", 2), ing("cordage")), (("stone_pickaxe", 1),), None, "early mining tool"),
    RecipeDef("wooden_spear", "Wooden spear", (ing("stick", 2), ing("flint"), ing("cordage")), (("wooden_spear", 1),), None, "crabs are easier with reach"),
    RecipeDef("fishing_rod", "Fishing rod", (ing("stick", 2), ing("cordage", 2), ing("grass_fiber")), (("fishing_rod", 1),), None, "coastal fishing tool"),
    RecipeDef("workbench", "Workbench", (ing("plank", 4), ing("stick", 2), ing("cordage")), (("workbench", 1),), None, "crafting station"),
    RecipeDef("campfire", "Campfire", (ing("stone", 5), ing("stick", 3), ing("tag:fiber")), (("campfire", 1),), None, "cooking station"),
    RecipeDef("fish_net", "Fish net", (ing("cordage", 5), ing("reeds", 2), ing("stick")), (("fish_net", 1),), "workbench", "deep water fishing"),
    RecipeDef("cooked_fish", "Cooked fish", (ing("raw_fish"),), (("cooked_fish", 1),), "campfire", "food is better cooked"),
    RecipeDef("cooked_crab", "Cooked crab", (ing("crab_meat"),), (("cooked_crab", 1),), "campfire", "crab cooks well"),
    RecipeDef("cooked_meat", "Cooked meat", (ing("raw_meat"),), (("cooked_meat", 1),), "campfire", "meat is safer cooked"),
    RecipeDef("fried_egg", "Fried egg", (ing("egg"),), (("fried_egg", 1),), "campfire", "eggs cook quickly"),
    RecipeDef("bread", "Camp bread", (ing("wild_seed", 4), ing("charcoal")), (("bread", 1),), "campfire", "seeds can become rough bread"),
    RecipeDef("charcoal", "Charcoal", (ing("tag:log"),), (("charcoal", 2),), "campfire", "fuel from wood"),
    RecipeDef("torch", "Torch", (ing("stick"), ing("charcoal"), ing("tag:fiber")), (("torch", 1),), None, "light on a handle"),
    RecipeDef("kiln", "Kiln", (ing("clay_lump", 8), ing("stone", 4), ing("charcoal", 2)), (("kiln", 1),), "workbench", "hotter crafting station"),
    RecipeDef("clay_pot", "Clay pot", (ing("clay_lump", 4),), (("clay_pot", 1),), "kiln", "fired clay container"),
    RecipeDef("glass", "Glass", (ing("sand", 3), ing("charcoal")), (("glass", 1),), "kiln", "sand melts into glass"),
    RecipeDef("glass_bottles", "Glass bottles", (ing("glass", 2), ing("charcoal")), (("glass_bottle", 3),), "kiln", "small bottles for potions"),
    RecipeDef("copper_ingot", "Copper ingot", (ing("copper_ore", 2), ing("coal")), (("copper_ingot", 1),), "kiln", "smelt ore"),
    RecipeDef("iron_ingot", "Iron ingot", (ing("iron_ore", 2), ing("coal")), (("iron_ingot", 1),), "kiln", "stronger metal"),
    RecipeDef("gold_ingot", "Gold ingot", (ing("gold_ore", 2), ing("coal")), (("gold_ingot", 1),), "kiln", "precious metal"),
    RecipeDef("potion_stand", "Potion stand", (ing("glass_bottle", 2), ing("stone", 3), ing("copper_ingot")), (("potion_stand", 1),), "workbench", "alchemy station"),
    RecipeDef("leather", "Leather", (ing("hide", 2), ing("resin")), (("leather", 2),), "workbench", "worked hide"),
    RecipeDef("wooden_shield", "Wooden shield", (ing("plank", 3), ing("cordage", 2)), (("wooden_shield", 1),), "workbench", "defense from rough planks"),
    RecipeDef("wooden_floor", "Wooden floor", (ing("plank", 1),), (("wooden_floor", 2),), "workbench", "floor pieces for a house"),
    RecipeDef("stone_floor", "Stone floor", (ing("stone", 2),), (("stone_floor", 2),), "workbench", "cool durable floor pieces"),
    RecipeDef("wooden_wall", "Wooden wall", (ing("plank", 2), ing("stick", 1)), (("wooden_wall", 2),), "workbench", "wooden house walls"),
    RecipeDef("stone_wall", "Stone wall", (ing("stone", 3), ing("clay_lump", 1)), (("stone_wall", 2),), "workbench", "sturdy stone walls"),
    RecipeDef("wooden_crate", "Wooden crate", (ing("plank", 4), ing("stick", 2)), (("wooden_crate", 1),), "workbench", "wooden storage"),
    RecipeDef("wooden_door", "Wooden door", (ing("plank", 3), ing("stick"), ing("cordage")), (("wooden_door", 1),), "workbench", "base building piece"),
    RecipeDef("bedroll", "Bedroll", (ing("grass_fiber", 4), ing("reeds", 2), ing("cordage", 2)), (("bedroll", 1),), "workbench", "portable rest kit"),
    RecipeDef("pine_tent", "Tent", (ing("pine_log", 3), ing("stick", 10)), (("tent", 1),), "workbench", "pine logs and branches make a small shelter"),
    RecipeDef("sack", "Sack", (ing("tag:fiber", 4), ing("cordage", 1)), (("sack", 1),), "workbench", "soft storage"),
    RecipeDef("bow", "Bow", (ing("stick", 2), ing("cordage", 2)), (("bow", 1),), "workbench", "ranged hunting tool"),
    RecipeDef("arrows", "Arrows", (ing("stick"), ing("flint"), ing("tag:fiber")), (("arrow", 4),), "workbench", "sharp light ammunition"),
    RecipeDef("copper_pickaxe", "Copper pickaxe", (ing("copper_ingot", 3), ing("stick", 2), ing("cordage")), (("copper_pickaxe", 1),), "workbench", "mine better ore"),
    RecipeDef("copper_axe", "Copper axe", (ing("copper_ingot", 2), ing("stick", 2), ing("cordage")), (("copper_axe", 1),), "workbench", "copper chopping tool"),
    RecipeDef("copper_sword", "Copper sword", (ing("copper_ingot", 2), ing("stick"), ing("resin")), (("copper_sword", 1),), "workbench", "first metal weapon"),
    RecipeDef("iron_pickaxe", "Iron pickaxe", (ing("iron_ingot", 3), ing("stick", 2), ing("cordage")), (("iron_pickaxe", 1),), "workbench", "deep mining"),
    RecipeDef("iron_axe", "Iron axe", (ing("iron_ingot", 2), ing("stick", 2), ing("cordage")), (("iron_axe", 1),), "workbench", "strong chopping tool"),
    RecipeDef("iron_sword", "Iron sword", (ing("iron_ingot", 2), ing("stick"), ing("resin")), (("iron_sword", 1),), "workbench", "reliable weapon"),
    RecipeDef("diamond_pickaxe", "Diamond pickaxe", (ing("diamond", 2), ing("iron_ingot", 2), ing("stick", 2), ing("cordage", 2)), (("diamond_pickaxe", 1),), "workbench", "top-tier mining"),
    RecipeDef("diamond_edged_pickaxe", "Diamond-edged pickaxe", (ing("diamond"), ing("iron_pickaxe"), ing("resin", 2)), (("diamond_edged_pickaxe", 1),), "workbench", "diamond coating"),
    RecipeDef("diamond_edged_sword", "Diamond-edged sword", (ing("diamond"), ing("iron_sword"), ing("resin", 2)), (("diamond_edged_sword", 1),), "workbench", "diamond weapon edge"),
    RecipeDef("copper_ring", "Copper ring", (ing("copper_ingot"),), (("copper_ring", 2),), "workbench", "simple rings"),
    RecipeDef("gold_ring", "Gold ring", (ing("gold_ingot"),), (("gold_ring", 2),), "workbench", "soft precious rings"),
    RecipeDef("gold_necklace", "Gold necklace", (ing("gold_ingot", 2), ing("cordage")), (("gold_necklace", 1),), "workbench", "prestige jewelry"),
    RecipeDef("diamond_ring", "Diamond ring", (ing("gold_ring"), ing("diamond")), (("diamond_ring", 1),), "workbench", "gem ring"),
    RecipeDef("diamond_amulet", "Diamond amulet", (ing("gold_necklace"), ing("diamond", 2)), (("diamond_amulet", 1),), "workbench", "gem amulet"),
    RecipeDef("leather_cap", "Leather cap", (ing("leather", 2), ing("cordage")), (("leather_cap", 1),), "workbench", "light head armor"),
    RecipeDef("leather_gloves", "Leather gloves", (ing("leather", 2), ing("cordage")), (("leather_gloves", 1),), "workbench", "hand protection"),
    RecipeDef("leather_tunic", "Leather tunic", (ing("leather", 4), ing("cordage", 2)), (("leather_tunic", 1),), "workbench", "light chest armor"),
    RecipeDef("leather_pants", "Leather pants", (ing("leather", 3), ing("cordage", 2)), (("leather_pants", 1),), "workbench", "light leg armor"),
    RecipeDef("leather_boots", "Leather boots", (ing("leather", 2), ing("cordage")), (("leather_boots", 1),), "workbench", "light foot armor"),
    RecipeDef("iron_helmet", "Iron helmet", (ing("iron_ingot", 3), ing("leather")), (("iron_helmet", 1),), "workbench", "metal head armor"),
    RecipeDef("iron_gauntlets", "Iron gauntlets", (ing("iron_ingot", 2), ing("leather")), (("iron_gauntlets", 1),), "workbench", "metal hand armor"),
    RecipeDef("iron_chestplate", "Iron chestplate", (ing("iron_ingot", 6), ing("leather", 2)), (("iron_chestplate", 1),), "workbench", "heavy chest armor"),
    RecipeDef("iron_greaves", "Iron greaves", (ing("iron_ingot", 4), ing("leather", 2)), (("iron_greaves", 1),), "workbench", "metal leg armor"),
    RecipeDef("iron_boots", "Iron boots", (ing("iron_ingot", 3), ing("leather")), (("iron_boots", 1),), "workbench", "metal foot armor"),
    RecipeDef("healing_potion", "Healing potion", (ing("glass_bottle"), ing("herb", 2), ing("flower")), (("healing_potion", 1),), "potion_stand", "red restorative potion"),
    RecipeDef("stamina_potion", "Stamina potion", (ing("glass_bottle"), ing("berries"), ing("seaweed")), (("stamina_potion", 1),), "potion_stand", "bright energy potion"),
    RecipeDef("antidote", "Antidote", (ing("glass_bottle"), ing("venom_sac"), ing("herb")), (("antidote", 1),), "potion_stand", "turn venom into medicine"),
)

RECIPES_BY_ID = {recipe.recipe_id: recipe for recipe in RECIPES}

PLACEABLE_ITEMS = frozenset(
    {
        "workbench",
        "campfire",
        "kiln",
        "potion_stand",
        "tent",
        "wooden_crate",
        "wooden_door",
        "wooden_floor",
        "stone_floor",
        "wooden_wall",
        "stone_wall",
        "bedroll",
    }
)

from .expanded_content import apply_expanded_content

RECIPES, PLACEABLE_ITEMS = apply_expanded_content(TERRAINS, FEATURES, ITEMS, RECIPES, PLACEABLE_ITEMS)
RECIPES_BY_ID = {recipe.recipe_id: recipe for recipe in RECIPES}


AGENT_SPRITES = (
    "agent_methodical_builder",
    "agent_quiet_miner",
    "agent_coastal_provider",
    "agent_restless_explorer",
    "agent_careful_forager",
    "agent_competitive_solo",
    "agent_social_trader",
    "agent_survival_minmaxer",
)


def sprite_specs() -> list[SpriteSpec]:
    specs: list[SpriteSpec] = []
    for terrain in TERRAINS.values():
        specs.append(SpriteSpec(terrain.sprite, terrain.name, "terrain", (32, 32), f"{terrain.sprite}.png", "seamless terrain tile"))
    for feature in FEATURES.values():
        specs.append(SpriteSpec(feature.sprite, feature.name, "feature", (32, 32), f"{feature.sprite}.png", "world object sprite with transparent background"))
    for item in ITEMS.values():
        specs.append(SpriteSpec(item.sprite, item.name, "item", (32, 32), f"{item.sprite}.png", "inventory icon"))
    for sprite_id in AGENT_SPRITES:
        specs.append(SpriteSpec(sprite_id, sprite_id.replace("_", " ").title(), "agent", (32, 40), f"{sprite_id}.png", "4-direction or neutral survivor sprite; transparent background"))
    for sprite_id in ("ui_unknown", "ui_selected", "ui_chat", "ui_inventory", "ui_health", "ui_hunger", "ui_energy"):
        specs.append(SpriteSpec(sprite_id, sprite_id.replace("_", " ").title(), "ui", (24, 24), f"{sprite_id}.png", "small UI icon"))
    return specs


def item_name(item_id: str) -> str:
    return ITEMS.get(item_id, ItemDef(item_id, item_id)).name
