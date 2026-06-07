from __future__ import annotations

from collections import Counter

from .data import ITEMS, RECIPES, RECIPES_BY_ID, Ingredient, RecipeDef


def add_items(inventory: Counter[str], items: Counter[str] | dict[str, int]) -> None:
    for item_id, count in items.items():
        if count > 0:
            item = ITEMS[item_id]
            inventory[item_id] = min(item.max_stack, inventory[item_id] + count)


def matching_items(inventory: Counter[str], ingredient: Ingredient) -> list[str]:
    if ingredient.is_tag:
        return [
            item_id
            for item_id, count in inventory.items()
            if count > 0 and ingredient.tag in ITEMS[item_id].tags
        ]
    return [ingredient.query] if inventory.get(ingredient.query, 0) > 0 else []


def has_ingredients(inventory: Counter[str], recipe: RecipeDef) -> bool:
    shadow = Counter(inventory)
    for ingredient in recipe.ingredients:
        remaining = ingredient.count
        for item_id in matching_items(shadow, ingredient):
            take = min(shadow[item_id], remaining)
            shadow[item_id] -= take
            remaining -= take
            if remaining <= 0:
                break
        if remaining > 0:
            return False
    return True


def consume_ingredients(inventory: Counter[str], recipe: RecipeDef) -> Counter[str]:
    consumed: Counter[str] = Counter()
    for ingredient in recipe.ingredients:
        remaining = ingredient.count
        for item_id in matching_items(inventory, ingredient):
            take = min(inventory[item_id], remaining)
            inventory[item_id] -= take
            if inventory[item_id] <= 0:
                del inventory[item_id]
            consumed[item_id] += take
            remaining -= take
            if remaining <= 0:
                break
    return consumed


def craftable_known(agent: object, world: object) -> list[RecipeDef]:
    result: list[RecipeDef] = []
    for recipe_id in getattr(agent, "known_recipes", set()):
        recipe = RECIPES_BY_ID.get(recipe_id)
        if recipe and station_available(agent, world, recipe) and has_ingredients(agent.inventory, recipe) and has_output_space(agent, recipe):
            result.append(recipe)
    return result


def discoverable(agent: object, world: object) -> list[RecipeDef]:
    result: list[RecipeDef] = []
    known = getattr(agent, "known_recipes", set())
    for recipe in RECIPES:
        if recipe.recipe_id in known:
            continue
        if station_available(agent, world, recipe) and has_ingredients(agent.inventory, recipe) and has_output_space(agent, recipe):
            result.append(recipe)
    return result


def station_available(agent: object, world: object, recipe: RecipeDef) -> bool:
    if recipe.station is None:
        return True
    if agent.inventory.get(recipe.station, 0) > 0:
        return True
    return world.has_station_near(agent.x, agent.y, recipe.station)


def craft(agent: object, recipe: RecipeDef, *, quality_bonus: int = 0) -> Counter[str]:
    consume_ingredients(agent.inventory, recipe)
    outputs = Counter(dict(recipe.outputs))
    if hasattr(agent, "add_items"):
        outputs = agent.add_items(outputs)
    else:
        add_items(agent.inventory, outputs)
    for item_id in outputs:
        item = ITEMS[item_id]
        if item.durability:
            boosted = round(item.durability * (1.0 + quality_bonus * 0.08))
            agent.tool_durability[item_id] = max(agent.tool_durability.get(item_id, 0), boosted)
        if item.food > 0 and quality_bonus and hasattr(agent, "food_quality"):
            agent.food_quality[item_id] = max(agent.food_quality.get(item_id, 0), quality_bonus)
    return outputs


def has_output_space(agent: object, recipe: RecipeDef) -> bool:
    shadow = Counter(getattr(agent, "inventory", Counter()))
    slot_limit = getattr(agent, "inventory_slot_limit", 999)
    for ingredient in recipe.ingredients:
        remaining = ingredient.count
        for item_id in matching_items(shadow, ingredient):
            take = min(shadow[item_id], remaining)
            shadow[item_id] -= take
            if shadow[item_id] <= 0:
                del shadow[item_id]
            remaining -= take
            if remaining <= 0:
                break
        if remaining > 0:
            return False
    for item_id, count in recipe.outputs:
        item = ITEMS[item_id]
        current = shadow.get(item_id, 0)
        if current + count > item.max_stack:
            return False
        if current <= 0 and sum(1 for value in shadow.values() if value > 0) >= slot_limit:
            return False
        shadow[item_id] += count
    return True
