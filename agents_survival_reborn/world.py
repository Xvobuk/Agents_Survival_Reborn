from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass

from .data import FEATURES, ITEMS, PLACEABLE_ITEMS, TERRAINS, FeatureDef, Loot


@dataclass
class Tile:
    terrain: str
    feature: str | None = None
    floor: str | None = None
    hp: int = 0
    shade: int = 0


@dataclass
class Interaction:
    ok: bool
    text: str
    loot: Counter[str]
    topic: str = ""


class World:
    def __init__(self, width: int, height: int, seed: int) -> None:
        self.width = width
        self.height = height
        self.seed = seed
        self.rng = random.Random(seed)
        self.tiles: list[list[Tile]] = []
        self._generate()

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def can_enter(self, agent: object, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        tile = self.tile(x, y)
        terrain = TERRAINS[tile.terrain]
        if not terrain.passable:
            if "water" in terrain.tags and (agent.inventory.get("raft", 0) or agent.inventory.get("boat", 0)):
                return True
            return False
        if tile.feature and not FEATURES[tile.feature].passable:
            return False
        return True

    def neighbors(self, x: int, y: int, *, include_center: bool = False):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0 and not include_center:
                    continue
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny):
                    yield nx, ny

    def has_station_near(self, x: int, y: int, station: str) -> bool:
        return any(self.tile(nx, ny).feature == station for nx, ny in self.neighbors(x, y, include_center=True))

    def place_station(self, x: int, y: int, item_id: str) -> bool:
        if not self.can_place_station(x, y, item_id):
            return False
        tile = self.tile(x, y)
        item = ITEMS[item_id]
        if "floor" in item.tags:
            tile.floor = item_id
            return True
        tile.feature = item_id
        tile.hp = FEATURES[item_id].max_hp
        return True

    def can_place_station(self, x: int, y: int, item_id: str) -> bool:
        if item_id not in PLACEABLE_ITEMS or not self.in_bounds(x, y):
            return False
        tile = self.tile(x, y)
        item = ITEMS[item_id]
        if "water" in TERRAINS[tile.terrain].tags:
            return False
        if "floor" in item.tags:
            if tile.floor:
                return False
            if not tile.feature:
                return True
            feature = FEATURES[tile.feature]
            return bool(set(feature.tags) & {"station", "storage", "rest", "shelter", "camp"})
        return tile.feature is None

    def advance_wildlife(self, occupied: set[tuple[int, int]] | None = None) -> None:
        occupied = occupied or set()
        movers: list[tuple[int, int, str]] = []
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if not tile.feature:
                    continue
                feature = FEATURES[tile.feature]
                if "animal" in feature.tags or "fish" in feature.tags:
                    movers.append((x, y, tile.feature))
        self.rng.shuffle(movers)
        moved_from: set[tuple[int, int]] = set()
        moved_to: set[tuple[int, int]] = set()
        for x, y, feature_id in movers:
            if (x, y) in moved_from:
                continue
            tile = self.tile(x, y)
            if tile.feature != feature_id:
                continue
            if self.rng.random() > self._wildlife_move_chance(feature_id):
                continue
            candidates = [
                (nx, ny)
                for nx, ny in self.neighbors(x, y)
                if (nx, ny) not in occupied
                and (nx, ny) not in moved_to
                and not self.tile(nx, ny).feature
                and not self.tile(nx, ny).floor
                and self._wildlife_can_enter(feature_id, self.tile(nx, ny).terrain)
            ]
            if not candidates:
                continue
            nx, ny = self.rng.choice(candidates)
            target = self.tile(nx, ny)
            target.feature = feature_id
            target.hp = FEATURES[feature_id].max_hp
            tile.feature = None
            tile.hp = 0
            moved_from.add((x, y))
            moved_to.add((nx, ny))

    def interact(self, agent: object, x: int, y: int) -> Interaction:
        if not self.in_bounds(x, y):
            return Interaction(False, "nothing is reachable there", Counter())
        tile = self.tile(x, y)
        if tile.feature:
            return self._interact_feature(agent, tile, x, y)
        return self._interact_terrain(agent, tile)

    def _interact_feature(self, agent: object, tile: Tile, x: int, y: int) -> Interaction:
        feature = FEATURES[tile.feature or ""]
        if feature.feature_id in {"workbench", "campfire", "kiln", "potion_stand"} or set(feature.tags) & {"station", "machine", "vehicle", "container"}:
            return Interaction(True, f"checked {feature.name.lower()}", Counter(), "station")
        if feature.feature_id == "tent":
            agent.energy = min(100.0, agent.energy + 18.0)
            agent.hunger = max(0.0, agent.hunger - 1.5)
            return Interaction(True, "rested in tent", Counter(), "rest")
        if feature.feature_id == "bedroll":
            bonus, size = self.house_rest_bonus(x, y)
            agent.energy = min(100.0, agent.energy + 10.0 + bonus)
            agent.hunger = max(0.0, agent.hunger - max(0.35, 1.0 - bonus * 0.03))
            if bonus:
                return Interaction(True, f"rested on bedroll inside a {size}-tile house", Counter(), "rest")
            return Interaction(True, "rested on bedroll", Counter(), "rest")
        if feature.feature_id in {"wooden_wall", "stone_wall", "wattle_wall"}:
            tile.feature = None
            tile.hp = 0
            loot = self._give(agent, Counter({feature.feature_id: 1}))
            return Interaction(True, f"dismantled {feature.name.lower()}", loot, "building")
        if feature.feature_id in {"wooden_crate", "wooden_door", "straw_roof"}:
            return Interaction(True, f"checked {feature.name.lower()}", Counter(), "building")
        if feature.feature_id == "cave":
            tool = self._tool(agent, "pickaxe", feature.min_power)
            if not tool:
                return Interaction(False, "a cave mouth needs a pickaxe", Counter(), "blocked")
            self._damage_tool(agent, tool)
            loot = self._cave_loot()
            loot = self._give(agent, loot)
            return Interaction(True, "worked inside a cave", loot, "ore")
        if feature.required_tool:
            tool = self._tool(agent, feature.required_tool, feature.min_power)
            if not tool:
                partial = self._partial_loot(feature)
                if partial:
                    partial = self._give(agent, partial)
                    return Interaction(True, f"picked around {feature.name.lower()}", partial, self._topic(feature))
                return Interaction(False, f"{feature.name.lower()} needs {feature.required_tool}", Counter(), "blocked")
            self._damage_tool(agent, tool)
            tile.hp -= max(1, ITEMS[tool].tool_power)
            if tile.hp > 0:
                partial = self._partial_loot(feature)
                partial = self._give(agent, partial)
                return Interaction(True, f"worked on {feature.name.lower()}", partial, self._topic(feature))
        else:
            tile.hp -= 1

        loot = self._roll(feature.loot)
        loot = self._give(agent, loot)
        if feature.depletes:
            tile.feature = None
            tile.hp = 0
        else:
            tile.hp = feature.max_hp
        return Interaction(True, f"harvested {feature.name.lower()}", loot, self._topic(feature))

    @staticmethod
    def _wildlife_move_chance(feature_id: str) -> float:
        if feature_id == "crab":
            return 0.55
        if feature_id in {"fish_school", "salmon_school", "eel"}:
            return 0.72
        if feature_id in {"rabbit", "frog", "gull"}:
            return 0.5
        return 0.34

    @staticmethod
    def _wildlife_can_enter(feature_id: str, terrain: str) -> bool:
        terrain_tags = TERRAINS[terrain].tags
        if feature_id in {"fish_school", "salmon_school", "eel"}:
            return "water" in terrain_tags
        if feature_id == "crab":
            return terrain in {"sand", "coast"}
        if feature_id in {"gull", "turtle"}:
            return terrain in {"coast", "sand"}
        if feature_id in {"frog", "duck"}:
            return terrain in {"swamp", "willow_wetland", "coast", "shallow_water"} or "wet" in terrain_tags
        if feature_id == "rabbit":
            return terrain in {"grass", "meadow", "flax_meadow", "forest_floor", "tundra", "bee_grove"}
        if feature_id in {"deer", "fox", "boar", "wolf", "bear"}:
            return terrain in {"forest_floor", "jungle", "meadow", "grass", "flax_meadow", "mushroom_grove", "bee_grove"}
        if feature_id == "snake":
            return terrain in {"sand", "badlands", "grass", "meadow", "coast"}
        return TERRAINS[terrain].passable

    def _interact_terrain(self, agent: object, tile: Tile) -> Interaction:
        terrain = TERRAINS[tile.terrain]
        loot: Counter[str] = Counter()
        if "water" in terrain.tags:
            tool = self._tool(agent, "net", 1) or self._tool(agent, "fishing", 1)
            if not tool:
                return Interaction(False, "water needs a rod or net", Counter(), "blocked")
            self._damage_tool(agent, tool)
            loot["raw_fish"] += self.rng.randint(2, 6) if "net" in ITEMS[tool].tool_tags else self.rng.randint(1, 2)
            if self.rng.random() < 0.25:
                loot["seaweed"] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "fished water", loot, "fish")
        if "coast" in terrain.tags:
            loot["sand"] += self.rng.randint(1, 2)
            if self.rng.random() < 0.55:
                loot["shell"] += 1
            if self.rng.random() < 0.08:
                loot["river_pearl"] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "searched the coast", loot, "coast")
        if "grass" in terrain.tags or "forest" in terrain.tags:
            loot["grass_fiber"] += self.rng.randint(1, 3)
            if self.rng.random() < 0.35:
                loot["stick"] += 1
            if self.rng.random() < 0.18:
                loot["berries"] += 1
            if "fiber" in terrain.tags:
                loot[self.rng.choice(("flax", "hemp", "cotton"))] += self.rng.randint(1, 2)
            if "flower" in terrain.tags and self.rng.random() < 0.2:
                loot[self.rng.choice(("chamomile", "yarrow", "mint", "honeycomb", "beeswax"))] += 1
            if self.rng.random() < 0.09:
                loot[self.rng.choice(("flax_seed", "cabbage_seed", "carrot_seed", "potato_seed", "pumpkin_seed", "corn_seed"))] += 1
            if self.rng.random() < 0.035:
                loot["manure"] += 1
            if "forest" in terrain.tags and self.rng.random() < 0.18:
                loot[self.rng.choice(("birch_bark", "pine_cone", "oak_acorn", "nuts", "maple_sap"))] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "foraged ground cover", loot, "plants")
        if "wet" in terrain.tags:
            loot["reeds"] += self.rng.randint(1, 3)
            if "fiber" in terrain.tags:
                loot["willow_withe"] += self.rng.randint(1, 2)
            if self.rng.random() < 0.3:
                loot[self.rng.choice(("herb", "mint", "nettle", "reed_fiber"))] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "foraged wet plants", loot, "plants")
        if "salt" in terrain.tags:
            loot["rock_salt"] += self.rng.randint(1, 3)
            if self.rng.random() < 0.35:
                loot["saltpeter"] += self.rng.randint(1, 2)
            loot = self._give(agent, loot)
            return Interaction(True, "scraped salt flats", loot, "salt")
        if "clay" in terrain.tags:
            loot["clay_lump"] += self.rng.randint(1, 4)
            if self.rng.random() < 0.25:
                loot[self.rng.choice(("high_quality_clay", "kaolin"))] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "dug clay", loot, "clay")
        if "rock" in terrain.tags or "hill" in terrain.tags:
            pick = self._tool(agent, "pickaxe", 1)
            if pick:
                self._damage_tool(agent, pick)
                loot["stone"] += self.rng.randint(2, 4)
                if self.rng.random() < 0.2:
                    loot["coal"] += 1
                if "volcanic" in terrain.tags:
                    loot[self.rng.choice(("basalt", "obsidian_shard", "sulfur_stone"))] += self.rng.randint(1, 2)
                elif "chalk" in terrain.tags or "karst" in terrain.tags:
                    loot[self.rng.choice(("limestone", "chalk", "gypsum", "flint_shard"))] += self.rng.randint(1, 2)
                elif self.rng.random() < 0.18:
                    loot[self.rng.choice(("granite", "slate", "sandstone"))] += self.rng.randint(1, 2)
            else:
                loot["pebble"] += self.rng.randint(1, 3)
                if self.rng.random() < 0.35:
                    loot["flint"] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "gathered rock", loot, "rock")
        if "sand" in terrain.tags or "dry" in terrain.tags:
            loot["sand"] += self.rng.randint(1, 3)
            if self.rng.random() < 0.2:
                loot["flint"] += 1
            if self.rng.random() < 0.12:
                loot[self.rng.choice(("dry_straw", "sandstone", "rock_salt"))] += 1
            loot = self._give(agent, loot)
            return Interaction(True, "scooped dry ground", loot, "sand")
        loot["soil"] += 1
        loot = self._give(agent, loot)
        return Interaction(True, "gathered soil", loot, "earth")

    def house_rest_bonus(self, x: int, y: int) -> tuple[float, int]:
        tile = self.tile(x, y)
        if not tile.floor:
            return 0.0, 0
        enclosed, size = self._enclosed_floor_region(x, y)
        if not enclosed:
            return 0.0, size
        return min(24.0, 4.0 + size * 1.25), size

    def _enclosed_floor_region(self, x: int, y: int) -> tuple[bool, int]:
        stack = [(x, y)]
        seen: set[tuple[int, int]] = set()
        enclosed = True
        while stack and len(seen) <= 256:
            cx, cy = stack.pop()
            if (cx, cy) in seen or not self.in_bounds(cx, cy):
                continue
            current = self.tile(cx, cy)
            if not current.floor:
                continue
            seen.add((cx, cy))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if not self.in_bounds(nx, ny):
                    enclosed = False
                    continue
                neighbor = self.tile(nx, ny)
                if neighbor.floor:
                    if (nx, ny) not in seen:
                        stack.append((nx, ny))
                    continue
                if neighbor.feature not in {"wooden_wall", "stone_wall", "wattle_wall", "wooden_door"}:
                    enclosed = False
        return enclosed and bool(seen), len(seen)

    @staticmethod
    def _give(agent: object, loot: Counter[str]) -> Counter[str]:
        if hasattr(agent, "add_items"):
            return agent.add_items(loot)
        return loot

    def _tool(self, agent: object, tag: str, power: int) -> str | None:
        best: tuple[int, int, str] | None = None
        for item_id, count in agent.inventory.items():
            if count <= 0:
                continue
            item = ITEMS[item_id]
            if tag not in item.tool_tags or item.tool_power < power:
                continue
            durability = agent.tool_durability.get(item_id, item.durability)
            if durability <= 0:
                continue
            candidate = (item.tool_power, durability, item_id)
            if best is None or candidate > best:
                best = candidate
        return best[2] if best else None

    def _damage_tool(self, agent: object, item_id: str) -> None:
        item = ITEMS[item_id]
        if not item.durability:
            return
        current = agent.tool_durability.get(item_id, item.durability) - 1
        if current <= 0:
            agent.inventory[item_id] -= 1
            if agent.inventory[item_id] <= 0:
                del agent.inventory[item_id]
            agent.tool_durability.pop(item_id, None)
        else:
            agent.tool_durability[item_id] = current

    def _roll(self, loot_table: tuple[Loot, ...]) -> Counter[str]:
        loot: Counter[str] = Counter()
        for entry in loot_table:
            if self.rng.random() <= entry.chance:
                loot[entry.item] += self.rng.randint(entry.low, entry.high)
        return loot

    def _partial_loot(self, feature: FeatureDef) -> Counter[str]:
        loot: Counter[str] = Counter()
        if "tree" in feature.tags and self.rng.random() < 0.45:
            loot["stick"] += 1
        elif ("ore" in feature.tags or "rock" in feature.tags or "stone" in feature.tags) and self.rng.random() < 0.45:
            loot["pebble"] += self.rng.randint(1, 2)
            if self.rng.random() < 0.18:
                loot["flint"] += 1
        return loot

    def _cave_loot(self) -> Counter[str]:
        loot: Counter[str] = Counter()
        roll = self.rng.random()
        if roll < 0.12:
            loot["coal"] += self.rng.randint(1, 4)
        elif roll < 0.28:
            loot["copper_ore"] += self.rng.randint(1, 3)
        elif roll < 0.43:
            loot["iron_ore"] += self.rng.randint(1, 3)
        elif roll < 0.55:
            loot["gold_ore"] += self.rng.randint(1, 2)
        elif roll < 0.62:
            loot["diamond"] += 1
        elif roll < 0.72:
            loot[self.rng.choice(("limestone", "granite", "slate", "basalt"))] += self.rng.randint(1, 3)
        elif roll < 0.82:
            loot[self.rng.choice(("sulfur_stone", "saltpeter", "gypsum", "kaolin"))] += self.rng.randint(1, 2)
        elif roll < 0.91:
            loot[self.rng.choice(("flint_shard", "obsidian_shard", "sandstone", "rock_salt"))] += self.rng.randint(1, 2)
        else:
            loot[self.rng.choice(("amber", "river_pearl", "diamond"))] += 1
        loot["stone"] += self.rng.randint(1, 3)
        return loot

    @staticmethod
    def _topic(feature: FeatureDef) -> str:
        if "ore" in feature.tags or "rock" in feature.tags:
            return "ore"
        if "food" in feature.tags:
            return "food"
        if "tree" in feature.tags:
            return "wood"
        if "plant" in feature.tags:
            return "plants"
        return ""

    def _generate(self) -> None:
        height = self._noise(4, 5)
        moisture = self._noise(17, 4)
        temp = self._noise(31, 3)
        self.tiles = []
        for y in range(self.height):
            row: list[Tile] = []
            for x in range(self.width):
                h = height[y][x]
                m = moisture[y][x]
                t = temp[y][x] - y / self.height * 0.2
                terrain = self._terrain(h, m, t)
                row.append(Tile(terrain, shade=self.rng.randint(-12, 12)))
            self.tiles.append(row)
        self._coasts()
        self._features()

    def _terrain(self, h: float, m: float, t: float) -> str:
        if h < 0.27:
            return "deep_water"
        if h < 0.34:
            return "shallow_water"
        if m < 0.24 and t > 0.38 and h < 0.66:
            return "salt_flat"
        if h < 0.39:
            return "coast"
        if h > 0.79:
            if t < 0.35:
                return "snow"
            if m < 0.42 and t > 0.48:
                return "basalt_field"
            if m < 0.58:
                return "limestone_karst"
            return "rock"
        if h > 0.68:
            if m < 0.22 and t > 0.42:
                return "basalt_field"
            if m < 0.32:
                return "badlands"
            if m < 0.42 and t < 0.65:
                return "chalk_downs"
            if m < 0.5:
                return "clay_hills"
            return "hills"
        if t < 0.26:
            return "tundra"
        if m > 0.78 and t > 0.45:
            return "jungle"
        if m > 0.74 and t > 0.34:
            return "willow_wetland"
        if m > 0.72:
            return "swamp"
        if m < 0.23 and t > 0.34:
            return "sand"
        if 0.52 < m < 0.72 and 0.38 < t < 0.74 and h > 0.45:
            return "flax_meadow"
        if 0.58 < m < 0.76 and 0.36 < t < 0.72 and h > 0.43:
            return "bee_grove"
        if 0.48 < m < 0.64 and 0.35 < t < 0.72 and h > 0.48:
            return "forest_floor"
        if 0.62 < m < 0.72 and t < 0.6:
            return "mushroom_grove"
        return "meadow" if m > 0.46 else "grass"

    def _coasts(self) -> None:
        original = [[tile.terrain for tile in row] for row in self.tiles]
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if original[y][x] in {"deep_water", "shallow_water"}:
                    continue
                water = sum(1 for nx, ny in self.neighbors(x, y) if original[ny][nx] in {"deep_water", "shallow_water"})
                if water >= 2 and original[y][x] not in {"rock", "snow"}:
                    tile.terrain = "coast"

    def _features(self) -> None:
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                feature = self._feature_for(tile.terrain, self.rng.random())
                if feature:
                    tile.feature = feature
                    tile.hp = FEATURES[feature].max_hp

    def _feature_for(self, terrain: str, roll: float) -> str | None:
        if terrain == "deep_water":
            if roll < 0.04:
                return "fish_school"
            if roll < 0.072:
                return "salmon_school"
            if roll < 0.092:
                return "eel"
            if roll < 0.112:
                return "kelp"
            if roll < 0.13:
                return "reef"
            if roll < 0.142:
                return "pearl_mussels"
            return None
        if terrain == "shallow_water":
            if roll < 0.05:
                return "fish_school"
            if roll < 0.075:
                return "salmon_school"
            if roll < 0.098:
                return "duck"
            if roll < 0.13:
                return "kelp"
            if roll < 0.15:
                return "pearl_mussels"
            return None
        if terrain == "coast":
            if roll < 0.055:
                return "crab"
            if roll < 0.075:
                return "gull"
            if roll < 0.09:
                return "turtle"
            if roll < 0.12:
                return "reeds"
            if roll < 0.137:
                return "pearl_mussels"
            return None
        if terrain == "sand":
            if roll < 0.055:
                return "cactus"
            if roll < 0.075:
                return "crab"
            if roll < 0.09:
                return "gull"
            if roll < 0.098:
                return "snake"
            if roll < 0.11:
                return "stone_outcrop"
            if roll < 0.13:
                return "sandstone_outcrop"
            if roll < 0.14:
                return "rock_salt_crust"
            return None
        if terrain in {"grass", "meadow"}:
            if roll < 0.055:
                return "rabbit"
            if roll < 0.065:
                return "snake"
            if roll < 0.08:
                return "grass_tuft"
            if roll < 0.13:
                return "flower_patch"
            if roll < 0.17:
                return "berry_bush"
            if roll < 0.2:
                return "birch_tree"
            if roll < 0.22:
                return "medicinal_flowers"
        if terrain == "flax_meadow":
            if roll < 0.045:
                return "rabbit"
            if roll < 0.085:
                return self.rng.choice(("flax_patch", "hemp_patch", "cotton_bolls"))
            if roll < 0.13:
                return "grass_tuft"
            if roll < 0.165:
                return "medicinal_flowers"
            if roll < 0.2:
                return "berry_bush"
            if roll < 0.215:
                return "deer"
            return None
        if terrain == "bee_grove":
            if roll < 0.045:
                return self.rng.choice(("rabbit", "deer", "fox"))
            if roll < 0.12:
                return self.rng.choice(("birch_tree", "oak_tree", "fruit_tree"))
            if roll < 0.17:
                return "beehive"
            if roll < 0.205:
                return "medicinal_flowers"
            if roll < 0.24:
                return "berry_bush"
            return None
        if terrain in {"forest_floor", "jungle"}:
            if roll < 0.04:
                return self.rng.choice(("rabbit", "deer", "fox", "boar"))
            if roll < 0.055:
                return self.rng.choice(("wolf", "bear"))
            if roll < 0.16:
                return self.rng.choice(("birch_tree", "oak_tree", "pine_tree", "fruit_tree"))
            if roll < 0.22:
                return "berry_bush"
            if roll < 0.26:
                return "mushrooms"
            if roll < 0.29:
                return "herbs"
            if roll < 0.31:
                return self.rng.choice(("amber_root", "beehive", "nettles"))
        if terrain == "swamp":
            if roll < 0.045:
                return self.rng.choice(("frog", "duck"))
            return "reeds" if roll < 0.16 else "mushrooms" if roll < 0.24 else "herbs" if roll < 0.28 else None
        if terrain == "willow_wetland":
            if roll < 0.05:
                return self.rng.choice(("frog", "duck", "turtle"))
            if roll < 0.13:
                return "willow_stand"
            if roll < 0.18:
                return "reeds"
            if roll < 0.215:
                return "mint_patch"
            if roll < 0.25:
                return "nettles"
            if roll < 0.265:
                return "pearl_mussels"
            return None
        if terrain == "salt_flat":
            if roll < 0.07:
                return "rock_salt_crust"
            if roll < 0.12:
                return "saltpeter_deposit"
            if roll < 0.145:
                return "sulfur_deposit"
            if roll < 0.16:
                return "snake"
            return None
        if terrain == "mushroom_grove":
            return "rabbit" if roll < 0.035 else "mushrooms" if roll < 0.18 else "pine_tree" if roll < 0.24 else None
        if terrain in {"rock", "hills", "badlands", "clay_hills", "limestone_karst", "chalk_downs", "basalt_field"}:
            return self._rock_feature(terrain, roll)
        if terrain == "snow":
            return "pine_tree" if roll < 0.06 else "snowdrift" if roll < 0.12 else None
        if terrain == "tundra":
            return "rabbit" if roll < 0.025 else "grass_tuft" if roll < 0.065 else "berry_bush" if roll < 0.095 else "pine_tree" if roll < 0.115 else None
        return None

    def _rock_feature(self, terrain: str, roll: float) -> str | None:
        if terrain == "limestone_karst":
            return "limestone_outcrop" if roll < 0.08 else "cave" if roll < 0.12 else "flint_nodule" if roll < 0.155 else "gypsum_crystals" if roll < 0.18 else "kaolin_patch" if roll < 0.2 else None
        if terrain == "chalk_downs":
            return "limestone_outcrop" if roll < 0.055 else "flint_nodule" if roll < 0.105 else "gypsum_crystals" if roll < 0.135 else "deer" if roll < 0.155 else None
        if terrain == "basalt_field":
            return "basalt_outcrop" if roll < 0.075 else "obsidian_glass" if roll < 0.115 else "sulfur_deposit" if roll < 0.15 else "cave" if roll < 0.17 else None
        if terrain == "clay_hills":
            return "clay_patch" if roll < 0.09 else "kaolin_patch" if roll < 0.12 else "stone_outcrop" if roll < 0.16 else "copper_vein" if roll < 0.18 else None
        if terrain == "badlands":
            return "stone_outcrop" if roll < 0.06 else "sandstone_outcrop" if roll < 0.085 else "coal_vein" if roll < 0.115 else "copper_vein" if roll < 0.14 else "gold_vein" if roll < 0.15 else None
        if roll < 0.05:
            return self.rng.choice(("stone_outcrop", "granite_outcrop", "slate_outcrop"))
        if roll < 0.075:
            return "cave"
        if roll < 0.098:
            return "coal_vein"
        if roll < 0.12:
            return "copper_vein"
        if roll < 0.139:
            return "iron_vein"
        if roll < 0.15:
            return "gold_vein"
        if roll < 0.156:
            return "diamond_vein"
        return None

    def _noise(self, salt: int, octaves: int) -> list[list[float]]:
        values = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        total = 0.0
        for octave in range(octaves):
            scale = max(4, 34 // (2**octave))
            amp = 1.0 / (2**octave)
            total += amp
            rng = random.Random(self.seed + salt * 997 + octave * 7919)
            gw = self.width // scale + 3
            gh = self.height // scale + 3
            grid = [[rng.random() for _ in range(gw)] for _ in range(gh)]
            for y in range(self.height):
                gy = y / scale
                y0 = int(math.floor(gy))
                sy = self._smooth(gy - y0)
                for x in range(self.width):
                    gx = x / scale
                    x0 = int(math.floor(gx))
                    sx = self._smooth(gx - x0)
                    n00, n10 = grid[y0][x0], grid[y0][x0 + 1]
                    n01, n11 = grid[y0 + 1][x0], grid[y0 + 1][x0 + 1]
                    nx0 = n00 * (1 - sx) + n10 * sx
                    nx1 = n01 * (1 - sx) + n11 * sx
                    values[y][x] += (nx0 * (1 - sy) + nx1 * sy) * amp
        return [[value / total for value in row] for row in values]

    @staticmethod
    def _smooth(t: float) -> float:
        return t * t * (3 - 2 * t)
