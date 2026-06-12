from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from .assets import AssetManager
from .constants import HUD_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from .data import FEATURES, ITEMS, PLACEABLE_ITEMS, RECIPES, TERRAINS, Ingredient, RecipeDef, item_name


RECIPE_CATEGORIES = (
    "All",
    "Survival",
    "Stations",
    "Building",
    "Tools",
    "Weapons",
    "Food",
    "Metal",
    "Armor",
    "Jewelry",
    "Alchemy",
    "Farming",
    "Medicine",
    "Navigation",
    "Other",
)


@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    follow: bool = False

    def clamp(self, sim: object, viewport: tuple[int, int]) -> None:
        self.x = max(0, min(self.x, sim.world.width * TILE_SIZE - viewport[0]))
        self.y = max(0, min(self.y, sim.world.height * TILE_SIZE - viewport[1]))


@dataclass
class RecipeBookState:
    open: bool = False
    category: str = "All"
    scroll: int = 0
    selected_recipe_id: str = ""


class Renderer:
    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        pygame.font.init()
        self.font = pygame.font.SysFont("segoeui", 15) or pygame.font.Font(None, 15)
        self.small = pygame.font.SysFont("consolas", 12) or pygame.font.Font(None, 12)
        self.title = pygame.font.SysFont("segoeui", 22, bold=True) or pygame.font.Font(None, 22)
        self.subtitle = pygame.font.SysFont("segoeui", 17, bold=True) or pygame.font.Font(None, 17)
        self._recipe_category_rects: dict[str, pygame.Rect] = {}
        self._recipe_row_rects: dict[str, pygame.Rect] = {}

    def draw(
        self,
        screen: pygame.Surface,
        sim: object,
        camera: Camera,
        selected: int,
        progress: float,
        recorder_status: str,
        paused: bool,
        mouse_pos: tuple[int, int] | None = None,
        recipe_book: RecipeBookState | None = None,
    ) -> None:
        mouse_pos = mouse_pos or pygame.mouse.get_pos()
        screen.fill((10, 12, 15))
        world_view = pygame.Rect(0, 0, screen.get_width() - HUD_WIDTH, screen.get_height())
        world_tooltip = self._world(screen, sim, camera, world_view, selected, progress, mouse_pos)
        hud_tooltip = self._hud(screen, sim, selected, recorder_status, paused, mouse_pos)
        tooltip = hud_tooltip or world_tooltip
        if recipe_book and recipe_book.open:
            tooltip = self._recipe_book(screen, sim, selected, recipe_book, mouse_pos)
        if tooltip:
            self._tooltip(screen, tooltip, mouse_pos)

    def handle_recipe_book_key(self, state: RecipeBookState, key: int) -> None:
        if key in {pygame.K_UP, pygame.K_w}:
            state.scroll = max(0, state.scroll - 1)
        elif key in {pygame.K_DOWN, pygame.K_s}:
            state.scroll += 1
        elif key == pygame.K_PAGEUP:
            state.scroll = max(0, state.scroll - 8)
        elif key == pygame.K_PAGEDOWN:
            state.scroll += 8
        elif key in {pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d}:
            current = RECIPE_CATEGORIES.index(state.category) if state.category in RECIPE_CATEGORIES else 0
            delta = -1 if key in {pygame.K_LEFT, pygame.K_a} else 1
            state.category = RECIPE_CATEGORIES[(current + delta) % len(RECIPE_CATEGORIES)]
            state.scroll = 0
            state.selected_recipe_id = ""

    def handle_recipe_book_click(self, state: RecipeBookState, mouse_pos: tuple[int, int]) -> None:
        for category, rect in self._recipe_category_rects.items():
            if rect.collidepoint(mouse_pos):
                state.category = category
                state.scroll = 0
                state.selected_recipe_id = ""
                return
        for recipe_id, rect in self._recipe_row_rects.items():
            if rect.collidepoint(mouse_pos):
                state.selected_recipe_id = recipe_id
                return

    def _world(self, screen: pygame.Surface, sim: object, camera: Camera, rect: pygame.Rect, selected: int, progress: float, mouse_pos: tuple[int, int]) -> list[str] | None:
        tooltip: list[str] | None = None
        hovered_tile: tuple[int, int] | None = None
        if rect.collidepoint(mouse_pos):
            tx = int((mouse_pos[0] + camera.x) // TILE_SIZE)
            ty = int((mouse_pos[1] + camera.y) // TILE_SIZE)
            if 0 <= tx < sim.world.width and 0 <= ty < sim.world.height:
                hovered_tile = (tx, ty)
        start_x = max(0, int(camera.x // TILE_SIZE) - 1)
        start_y = max(0, int(camera.y // TILE_SIZE) - 1)
        end_x = min(sim.world.width, int((camera.x + rect.width) // TILE_SIZE) + 2)
        end_y = min(sim.world.height, int((camera.y + rect.height) // TILE_SIZE) + 2)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = sim.world.tile(x, y)
                terrain = TERRAINS[tile.terrain]
                sprite = self.assets.get(terrain.sprite)
                dest = pygame.Rect(int(x * TILE_SIZE - camera.x), int(y * TILE_SIZE - camera.y), TILE_SIZE, TILE_SIZE)
                screen.blit(sprite, dest)
                if tile.floor:
                    floor_sprite = self.assets.get(ITEMS[tile.floor].sprite)
                    screen.blit(floor_sprite, dest)
                if tile.shade:
                    shade = max(0, min(255, 128 + tile.shade * 3))
                    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill((shade, shade, shade, 16))
                    screen.blit(overlay, dest)
                if tile.feature:
                    feature = FEATURES[tile.feature]
                    fs = self.assets.get(feature.sprite)
                    screen.blit(fs, dest)
                    if tile.hp and tile.hp < feature.max_hp and feature.max_hp < 999:
                        pygame.draw.rect(screen, (20, 20, 20), (dest.x + 4, dest.y + TILE_SIZE - 6, TILE_SIZE - 8, 3))
                        pygame.draw.rect(screen, (255, 220, 110), (dest.x + 4, dest.y + TILE_SIZE - 6, int((TILE_SIZE - 8) * tile.hp / feature.max_hp), 3))
                if hovered_tile == (x, y):
                    pygame.draw.rect(screen, (255, 236, 120), dest, 2)
                    tooltip = self._tile_tooltip(tile, x, y)
        self._grid(screen, camera, rect, start_x, start_y, end_x, end_y)
        for index, agent in enumerate(sim.agents):
            rx, ry, dx, dy = self._agent_pose(agent, progress)
            sx = int(rx * TILE_SIZE - camera.x + TILE_SIZE / 2)
            sy = int(ry * TILE_SIZE - camera.y + TILE_SIZE / 2)
            if not rect.collidepoint(sx, sy):
                continue
            body = self.assets.get(agent.sprite)
            body_rect = body.get_rect(center=(sx, sy - 4))
            pygame.draw.ellipse(screen, (0, 0, 0, 70), (sx - 12, sy + 8, 24, 8))
            screen.blit(body, body_rect)
            pygame.draw.line(screen, (255, 255, 255), (sx, sy), (int(sx + dx * 14), int(sy + dy * 14)), 2)
            if index == selected:
                pygame.draw.rect(screen, (255, 236, 120), body_rect.inflate(6, 6), 2, border_radius=5)
            name = self.small.render(agent.name, True, (245, 245, 245))
            screen.blit(name, name.get_rect(center=(sx, sy - 28)))
            if body_rect.inflate(8, 8).collidepoint(mouse_pos):
                tooltip = self._agent_tooltip(agent)
        return tooltip

    def _hud(self, screen: pygame.Surface, sim: object, selected: int, recorder_status: str, paused: bool, mouse_pos: tuple[int, int]) -> list[str] | None:
        tooltip: list[str] | None = None
        panel = pygame.Rect(screen.get_width() - HUD_WIDTH, 0, HUD_WIDTH, screen.get_height())
        pygame.draw.rect(screen, (18, 22, 27), panel)
        pygame.draw.line(screen, (70, 78, 88), (panel.left, 0), (panel.left, panel.bottom), 2)
        x, y = panel.left + 16, 16
        y = self._text(screen, "Agents Survival Reborn", x, y, self.title, (242, 244, 247), 28)
        state = "THINKING" if getattr(sim, "round_thinking", False) else "PAUSED" if paused else "RUNNING"
        y = self._text(screen, f"Round {sim.round_index} | {state}", x, y, self.font, (184, 202, 213), 22)
        provider_label = sim.llm.config.provider
        model_label = sim.llm.config.model
        gemini_agent_count = getattr(sim.llm.config, "gemini_agent_count", 0)
        gemini_model = getattr(sim.llm.config, "gemini_model", "gemini")
        if gemini_agent_count > 0 and sim.llm.config.provider != "gemini":
            provider_label = f"{sim.llm.config.provider}+gemini"
            model_label = f"{sim.llm.config.model}+{gemini_model} x{gemini_agent_count}"
        if sim.llm.config.provider in {"compatible", "llama", "ollama"}:
            llm_state = "local" if sim.llm.config.enabled else "offline"
        elif sim.llm.config.provider == "gemini":
            llm_state = "gemini" if sim.llm.config.enabled and sim.llm.config.api_key else "no key" if sim.llm.config.enabled else "offline"
        else:
            llm_state = "on" if sim.llm.config.enabled and sim.llm.config.api_key else "no key" if sim.llm.config.enabled else "offline"
        y = self._wrap(
            screen,
            f"LLM: {llm_state} | {provider_label} | {model_label} | ok {sim.llm.last_successes}/{sim.llm.last_requested} | fallback {sim.llm.last_fallbacks} | provider swap {getattr(sim.llm, 'last_provider_fallbacks', 0)} | {sim.llm.last_duration:.1f}s/{sim.llm.config.timeout:.0f}s",
            x,
            y,
            360,
            self.small,
            (171, 190, 203),
        )
        if sim.llm.last_error:
            y = self._wrap(screen, f"LLM error: {sim.llm.last_error[:120]}", x, y, 360, self.small, (230, 151, 126))
        y = self._wrap(screen, f"Recorder: {recorder_status}", x, y, 360, self.small, (142, 162, 174))
        y = self._wrap(screen, "B: recipe book", x, y, 360, self.small, (142, 162, 174))
        agent = sim.agents[selected % len(sim.agents)]
        y += 8
        y = self._text(screen, f"{agent.name} | {agent.persona.archetype}", x, y, self.title, agent.color, 26)
        y = self._wrap(screen, agent.persona.origin, x, y, 360, self.small, (202, 210, 217))
        y = self._wrap(screen, f"Goal: {agent.persona.long_goal}", x, y, 360, self.small, (202, 210, 217))
        y = self._stat_row(screen, "ui_health", "HP", agent.health, x, y, (216, 72, 82))
        y = self._stat_row(screen, "ui_hunger", "Food", agent.hunger, x, y, (226, 165, 72))
        y = self._stat_row(screen, "ui_energy", "Stamina", agent.energy, x, y, (78, 181, 226))
        equipment = getattr(agent, "equipment", {})
        rings = getattr(agent, "rings", [])
        armor = getattr(agent, "armor_rating", 0)
        worn = [item_name(item_id) for item_id in equipment.values()]
        if rings:
            worn.append(f"{len(rings)} ring{'s' if len(rings) != 1 else ''}")
        gear_text = ", ".join(worn[:4]) if worn else "none"
        y = self._wrap(screen, f"Armor {armor}: {gear_text}", x, y, 360, self.small, (178, 194, 211))
        y = self._wrap(screen, f"Intent: {agent.last_intent}", x, y, 360, self.small, (215, 218, 222))
        y = self._wrap(screen, f"Thought: {agent.last_thought}", x, y, 360, self.small, (184, 214, 190))
        y = self._wrap(screen, f"Last: {agent.last_action}", x, y, 360, self.small, (215, 218, 222))
        y += 8
        y, tooltip = self._inventory_grid(screen, agent, x, y, mouse_pos)
        y += 8
        self._minimap(screen, sim, pygame.Rect(x, y, 360, 140), selected)
        y += 154
        y = self._text(screen, "Chat", x, y, self.font, (242, 244, 247), 21)
        for msg in sim.chat[-12:]:
            y = self._wrap(screen, f"{msg.speaker}: {msg.text}", x, y, 360, self.small, (182, 215, 222))
            if y > screen.get_height() - 18:
                break
        return tooltip

    def _recipe_book(self, screen: pygame.Surface, sim: object, selected: int, state: RecipeBookState, mouse_pos: tuple[int, int]) -> list[str] | None:
        tooltip: list[str] | None = None
        self._recipe_category_rects.clear()
        self._recipe_row_rects.clear()
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(70, 48, screen.get_width() - 140, screen.get_height() - 96)
        pygame.draw.rect(screen, (20, 23, 27), rect, border_radius=8)
        pygame.draw.rect(screen, (106, 118, 130), rect, 1, border_radius=8)
        pygame.draw.rect(screen, (33, 38, 44), (rect.x, rect.y, rect.w, 54), border_top_left_radius=8, border_top_right_radius=8)
        title_img = self.title.render("Recipe Book", True, (247, 243, 224))
        screen.blit(title_img, (rect.x + 22, rect.y + 15))
        help_img = self.small.render("B/Esc close  |  wheel or Up/Down scroll  |  click category/recipe", True, (169, 184, 196))
        screen.blit(help_img, (rect.right - help_img.get_width() - 22, rect.y + 21))

        agent = sim.agents[selected % len(sim.agents)]
        recipes = self._recipes_for_category(state.category)
        if not recipes:
            recipes = list(RECIPES)
        max_scroll = max(0, len(recipes) - 12)
        state.scroll = max(0, min(state.scroll, max_scroll))
        if not state.selected_recipe_id or state.selected_recipe_id not in {recipe.recipe_id for recipe in recipes}:
            state.selected_recipe_id = recipes[min(state.scroll, len(recipes) - 1)].recipe_id if recipes else ""
        selected_recipe = next((recipe for recipe in recipes if recipe.recipe_id == state.selected_recipe_id), recipes[0] if recipes else None)

        categories_rect = pygame.Rect(rect.x + 18, rect.y + 72, 164, rect.h - 94)
        list_rect = pygame.Rect(categories_rect.right + 16, categories_rect.y, 372, categories_rect.h)
        detail_rect = pygame.Rect(list_rect.right + 18, categories_rect.y, rect.right - list_rect.right - 36, categories_rect.h)
        self._recipe_categories(screen, categories_rect, state)
        tooltip = self._recipe_list(screen, list_rect, recipes, state, agent, mouse_pos) or tooltip
        if selected_recipe:
            tooltip = self._recipe_details(screen, detail_rect, selected_recipe, agent, sim, mouse_pos) or tooltip
        return tooltip

    def _recipe_categories(self, screen: pygame.Surface, rect: pygame.Rect, state: RecipeBookState) -> None:
        y = rect.y
        y = self._text(screen, "Categories", rect.x, y, self.subtitle, (236, 239, 242), 24)
        for category in RECIPE_CATEGORIES:
            count = len(self._recipes_for_category(category))
            row = pygame.Rect(rect.x, y, rect.w, 28)
            self._recipe_category_rects[category] = row
            active = category == state.category
            pygame.draw.rect(screen, (58, 70, 80) if active else (28, 33, 39), row, border_radius=5)
            pygame.draw.rect(screen, (126, 143, 158) if active else (55, 64, 73), row, 1, border_radius=5)
            label = self.font.render(category, True, (250, 247, 228) if active else (202, 212, 220))
            screen.blit(label, (row.x + 10, row.y + 5))
            badge = self.small.render(str(count), True, (176, 190, 202))
            screen.blit(badge, badge.get_rect(midright=(row.right - 9, row.centery)))
            y += 32

    def _recipe_list(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        recipes: list[RecipeDef],
        state: RecipeBookState,
        agent: object,
        mouse_pos: tuple[int, int],
    ) -> list[str] | None:
        tooltip: list[str] | None = None
        y = rect.y
        y = self._text(screen, f"{state.category} Recipes", rect.x, y, self.subtitle, (236, 239, 242), 24)
        visible = recipes[state.scroll : state.scroll + 12]
        for recipe in visible:
            row = pygame.Rect(rect.x, y, rect.w, 46)
            self._recipe_row_rects[recipe.recipe_id] = row
            known = recipe.recipe_id in getattr(agent, "known_recipes", set())
            selected = recipe.recipe_id == state.selected_recipe_id
            bg = (66, 73, 76) if selected else (35, 41, 47) if known else (27, 31, 36)
            pygame.draw.rect(screen, bg, row, border_radius=6)
            pygame.draw.rect(screen, (132, 151, 162) if selected else (60, 70, 79), row, 1, border_radius=6)
            icon_x = row.x + 8
            for out_index, (item_id, count) in enumerate(recipe.outputs[:3]):
                icon_rect = pygame.Rect(icon_x + out_index * 30, row.y + 7, 26, 26)
                self._draw_item_icon(screen, item_id, icon_rect, count if count > 1 else 0)
                if icon_rect.collidepoint(mouse_pos):
                    tooltip = self._item_tooltip(item_id, count, agent, prefix="Output")
            text_x = row.x + 104
            name_color = (248, 244, 224) if known else (192, 202, 210)
            screen.blit(self.font.render(recipe.name, True, name_color), (text_x, row.y + 6))
            station = item_name(recipe.station) if recipe.station else "Hand craft"
            status = "known" if known else "hidden from agent"
            meta = self.small.render(f"{station} | {status}", True, (156, 174, 188))
            screen.blit(meta, (text_x, row.y + 26))
            if self._agent_has_recipe_ingredients(agent, recipe):
                pygame.draw.circle(screen, (107, 190, 122), (row.right - 18, row.centery), 5)
            if row.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 236, 120), row, 2, border_radius=6)
            y += 50
        if len(recipes) > 12:
            footer = self.small.render(f"{state.scroll + 1}-{min(len(recipes), state.scroll + 12)} / {len(recipes)}", True, (154, 171, 185))
            screen.blit(footer, (rect.x, rect.bottom - 18))
        return tooltip

    def _recipe_details(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        recipe: RecipeDef,
        agent: object,
        sim: object,
        mouse_pos: tuple[int, int],
    ) -> list[str] | None:
        tooltip: list[str] | None = None
        pygame.draw.rect(screen, (25, 30, 35), rect, border_radius=7)
        pygame.draw.rect(screen, (72, 84, 96), rect, 1, border_radius=7)
        y = rect.y + 18
        x = rect.x + 20
        known = recipe.recipe_id in getattr(agent, "known_recipes", set())
        y = self._text(screen, recipe.name, x, y, self.title, (248, 244, 224), 30)
        category = self._recipe_category(recipe)
        station = item_name(recipe.station) if recipe.station else "Hand craft"
        y = self._wrap(screen, f"{category} recipe | Station: {station}", x, y, rect.w - 40, self.font, (184, 200, 212))
        status_color = (113, 201, 131) if known else (218, 172, 96)
        status = f"{agent.name} knows this recipe" if known else f"Hidden from {agent.name}; agents must discover it themselves"
        y = self._wrap(screen, status, x, y, rect.w - 40, self.font, status_color)

        if recipe.hint:
            y += 5
            y = self._wrap(screen, recipe.hint, x, y, rect.w - 40, self.font, (214, 216, 205))
        y += 12
        y = self._text(screen, "Outputs", x, y, self.subtitle, (236, 239, 242), 24)
        out_x = x
        for item_id, count in recipe.outputs:
            box = pygame.Rect(out_x, y, 54, 54)
            self._draw_item_icon(screen, item_id, box.inflate(-8, -8), count if count > 1 else 0)
            if box.collidepoint(mouse_pos):
                tooltip = self._item_tooltip(item_id, count, agent, prefix="Output")
            label = self.small.render(item_name(item_id)[:18], True, (198, 208, 216))
            screen.blit(label, (out_x, y + 58))
            out_x += 102
        y += 86

        y = self._text(screen, "Ingredients", x, y, self.subtitle, (236, 239, 242), 24)
        for ingredient in recipe.ingredients:
            row = pygame.Rect(x, y, rect.w - 40, 38)
            owned = self._ingredient_owned(agent, ingredient)
            ok = owned >= ingredient.count
            pygame.draw.rect(screen, (32, 40, 36) if ok else (43, 34, 34), row, border_radius=5)
            pygame.draw.rect(screen, (73, 104, 80) if ok else (105, 73, 73), row, 1, border_radius=5)
            icon_rect = pygame.Rect(row.x + 6, row.y + 4, 30, 30)
            icon_item = self._ingredient_icon_item(ingredient)
            if icon_item:
                self._draw_item_icon(screen, icon_item, icon_rect, 0)
                if icon_rect.collidepoint(mouse_pos):
                    tooltip = self._item_tooltip(icon_item, 1, agent, prefix="Ingredient option")
            else:
                pygame.draw.rect(screen, (67, 78, 88), icon_rect, border_radius=4)
            label = self._ingredient_label(ingredient)
            text = self.font.render(f"{label} x{ingredient.count}", True, (230, 234, 237))
            screen.blit(text, (row.x + 44, row.y + 8))
            amount = self.small.render(f"{owned}/{ingredient.count}", True, (154, 222, 166) if ok else (230, 151, 126))
            screen.blit(amount, amount.get_rect(midright=(row.right - 10, row.centery)))
            y += 43

        y += 8
        if recipe.station:
            y = self._text(screen, "Station", x, y, self.subtitle, (236, 239, 242), 24)
            station_item = ITEMS.get(recipe.station)
            station_rect = pygame.Rect(x, y, 42, 42)
            if station_item:
                self._draw_item_icon(screen, recipe.station, station_rect, 0)
            nearby = getattr(sim.world, "has_station_near", lambda *_args: False)(agent.x, agent.y, recipe.station)
            carried = getattr(agent, "inventory", {}).get(recipe.station, 0) > 0
            station_status = "nearby" if nearby else "carried" if carried else "missing nearby"
            screen.blit(self.font.render(f"{station} | {station_status}", True, (208, 218, 226)), (x + 54, y + 11))
            y += 54
        can_attempt = known and self._agent_has_recipe_ingredients(agent, recipe)
        if recipe.station:
            can_attempt = can_attempt and (getattr(agent, "inventory", {}).get(recipe.station, 0) > 0 or getattr(sim.world, "has_station_near", lambda *_args: False)(agent.x, agent.y, recipe.station))
        verdict = "Ready for selected agent" if can_attempt else "Not ready for selected agent"
        pygame.draw.rect(screen, (36, 63, 43) if can_attempt else (64, 47, 37), (x, rect.bottom - 50, rect.w - 40, 32), border_radius=6)
        screen.blit(self.font.render(verdict, True, (235, 241, 233)), (x + 12, rect.bottom - 43))
        return tooltip

    def _draw_item_icon(self, screen: pygame.Surface, item_id: str, rect: pygame.Rect, badge_count: int = 0) -> None:
        item = ITEMS.get(item_id)
        pygame.draw.rect(screen, (18, 21, 25), rect, border_radius=5)
        pygame.draw.rect(screen, (70, 80, 91), rect, 1, border_radius=5)
        if not item:
            return
        icon = self.assets.get(item.sprite)
        icon_rect = icon.get_rect(center=rect.center)
        screen.blit(icon, icon_rect)
        if badge_count:
            badge = self.small.render(str(badge_count), True, (245, 247, 250))
            bg = badge.get_rect(bottomright=(rect.right - 2, rect.bottom - 2)).inflate(4, 2)
            pygame.draw.rect(screen, (8, 10, 12), bg, border_radius=3)
            screen.blit(badge, badge.get_rect(center=bg.center))

    def _recipes_for_category(self, category: str) -> list[RecipeDef]:
        recipes = sorted(RECIPES, key=lambda recipe: (self._recipe_category(recipe), recipe.name, recipe.recipe_id))
        if category == "All":
            return recipes
        return [recipe for recipe in recipes if self._recipe_category(recipe) == category]

    @staticmethod
    def _recipe_category(recipe: RecipeDef) -> str:
        output_tags: set[str] = set()
        output_ids = {item_id for item_id, _count in recipe.outputs}
        for item_id, _count in recipe.outputs:
            item = ITEMS.get(item_id)
            if item:
                output_tags.update(item.tags)
                if item.tool_tags:
                    output_tags.update(item.tool_tags)
        name = recipe.name.lower()
        if output_tags & {"station", "machine", "vehicle"}:
            return "Stations"
        if output_tags & {"building", "wall", "floor", "shelter", "container", "roof"}:
            return "Building"
        if output_tags & {"potion", "alchemy"} or recipe.station == "potion_stand":
            return "Alchemy"
        if output_tags & {"armor"}:
            return "Armor"
        if output_tags & {"jewelry", "gold", "diamond"} and output_tags & {"crafted"}:
            return "Jewelry"
        if output_tags & {"weapon", "bow", "spear", "sword"} or any(word in name for word in ("spear", "sword", "bow", "sling", "bolas", "arrow", "harpoon")):
            return "Weapons"
        if output_tags & {"tool", "pickaxe", "axe", "shovel", "blade", "hammer", "saw", "chisel", "hoe", "bucket"}:
            return "Tools"
        if output_tags & {"food"} or any(word in name for word in ("cooked", "bread", "stew", "soup", "dried", "smoked")):
            return "Food"
        if output_tags & {"metal", "ore", "copper", "iron", "steel"} or any(word in name for word in ("ingot", "nail", "wire", "bracket", "rivet")):
            return "Metal"
        if output_tags & {"medicine"} or any(word in name for word in ("bandage", "splint", "ointment", "antiseptic")):
            return "Medicine"
        if output_tags & {"seed", "compost", "fertilizer", "farm"}:
            return "Farming"
        if output_ids & {"compass", "spyglass", "sextant", "terrain_map"}:
            return "Navigation"
        if not recipe.station:
            return "Survival"
        return "Other"

    @staticmethod
    def _ingredient_label(ingredient: Ingredient) -> str:
        if ingredient.is_tag:
            return f"Any {ingredient.tag}"
        return item_name(ingredient.query)

    @staticmethod
    def _ingredient_icon_item(ingredient: Ingredient) -> str:
        if not ingredient.is_tag:
            return ingredient.query
        matches = sorted(item_id for item_id, item in ITEMS.items() if ingredient.tag in item.tags)
        return matches[0] if matches else ""

    @staticmethod
    def _ingredient_owned(agent: object, ingredient: Ingredient) -> int:
        inventory = getattr(agent, "inventory", {})
        if not ingredient.is_tag:
            return int(inventory.get(ingredient.query, 0))
        total = 0
        for item_id, count in inventory.items():
            item = ITEMS.get(item_id)
            if item and ingredient.tag in item.tags:
                total += int(count)
        return total

    def _agent_has_recipe_ingredients(self, agent: object, recipe: RecipeDef) -> bool:
        return all(self._ingredient_owned(agent, ingredient) >= ingredient.count for ingredient in recipe.ingredients)

    def _minimap(self, screen: pygame.Surface, sim: object, rect: pygame.Rect, selected: int) -> None:
        pygame.draw.rect(screen, (8, 10, 12), rect)
        sx, sy = rect.width / sim.world.width, rect.height / sim.world.height
        for y in range(0, sim.world.height, 2):
            for x in range(0, sim.world.width, 2):
                color = TERRAINS[sim.world.tile(x, y).terrain].color
                pygame.draw.rect(screen, color, (rect.x + int(x * sx), rect.y + int(y * sy), max(1, int(sx * 2) + 1), max(1, int(sy * 2) + 1)))
        for i, agent in enumerate(sim.agents):
            px, py = rect.x + int(agent.x * sx), rect.y + int(agent.y * sy)
            pygame.draw.circle(screen, agent.color, (px, py), 4 if i == selected else 3)
        pygame.draw.rect(screen, (80, 88, 98), rect, 1)

    def _inventory_grid(self, screen: pygame.Surface, agent: object, x: int, y: int, mouse_pos: tuple[int, int]) -> tuple[int, list[str] | None]:
        tooltip: list[str] | None = None
        used = getattr(agent, "used_inventory_slots", sum(1 for count in agent.inventory.values() if count > 0))
        limit = getattr(agent, "inventory_slot_limit", 15)
        header = f"Inventory {used}/{limit}"
        y = self._text(screen, header, x, y, self.font, (242, 244, 247), 21)
        inv = sorted(agent.inventory.items(), key=lambda pair: (item_name(pair[0]), pair[0]))
        slot = 38
        gap = 6
        cols = 5
        for index in range(limit):
            row = index // cols
            col = index % cols
            rect = pygame.Rect(x + col * (slot + gap), y + row * (slot + gap), slot, slot)
            pygame.draw.rect(screen, (28, 33, 39), rect, border_radius=5)
            pygame.draw.rect(screen, (75, 85, 96), rect, 1, border_radius=5)
            if index >= len(inv):
                continue
            item_id, count = inv[index]
            item = ITEMS[item_id]
            icon = self.assets.get(item.sprite)
            icon_rect = icon.get_rect(center=(rect.centerx, rect.centery - 2))
            screen.blit(icon, icon_rect)
            if count > 1:
                badge = self.small.render(str(count), True, (245, 247, 250))
                bg = badge.get_rect(bottomright=(rect.right - 3, rect.bottom - 2)).inflate(4, 2)
                pygame.draw.rect(screen, (8, 10, 12), bg, border_radius=3)
                screen.blit(badge, badge.get_rect(center=bg.center))
            if item.max_stack > 1:
                fill = max(0.0, min(1.0, count / item.max_stack))
                bar = pygame.Rect(rect.left + 4, rect.bottom - 5, int((slot - 8) * fill), 2)
                pygame.draw.rect(screen, (110, 181, 126), bar)
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 236, 120), rect, 2, border_radius=5)
                tooltip = self._item_tooltip(item_id, count, agent)
        rows = math.ceil(limit / cols)
        y += rows * (slot + gap) + 4
        if len(inv) > limit:
            y = self._text(screen, f"+{len(inv) - limit} hidden", x, y, self.small, (230, 151, 126), 15)
        return y, tooltip

    def _tile_tooltip(self, tile: object, x: int, y: int) -> list[str]:
        terrain = TERRAINS[tile.terrain]
        lines = [f"{terrain.name} ({x}, {y})", self._terrain_description(terrain), self._tags_line(terrain.tags), "Passable terrain" if terrain.passable else "Blocked terrain"]
        if tile.floor:
            lines.extend(["", *self._item_tooltip(tile.floor, 1, None, prefix="Floor")])
        if tile.feature:
            feature = FEATURES[tile.feature]
            lines.extend(["", feature.name, self._feature_description(feature), self._tags_line(feature.tags)])
            lines.append("Passable object" if feature.passable else "Blocks movement")
            if feature.max_hp < 999:
                lines.append(f"HP: {tile.hp}/{feature.max_hp}")
            if feature.required_tool:
                lines.append(f"Requires: {feature.required_tool} power {feature.min_power}")
            if "hostile" in feature.tags:
                lines.append("Danger: can hurt nearby agents")
            if feature.loot:
                loot = ", ".join(f"{loot.low}-{loot.high} {item_name(loot.item)}" for loot in feature.loot[:4])
                lines.append(f"Loot: {loot}")
            if "station" in feature.tags:
                lines.append("Station: enables nearby recipes")
            if "building" in feature.tags or "wall" in feature.tags:
                lines.append("Building piece: can count toward houses")
        return lines

    def _agent_tooltip(self, agent: object) -> list[str]:
        equipment = getattr(agent, "equipment", {})
        rings = getattr(agent, "rings", [])
        lines = [
            f"{agent.name} | {agent.persona.archetype}",
            f"HP {agent.health:.1f}  Food {agent.hunger:.1f}  Stamina {agent.energy:.1f}",
            f"Armor: {getattr(agent, 'armor_rating', 0)}",
            f"Intent: {getattr(agent, 'last_intent', '')}",
        ]
        if equipment:
            lines.append("Gear: " + ", ".join(item_name(item_id) for item_id in equipment.values()))
        if rings:
            lines.append(f"Rings: {len(rings)}/10")
        return lines

    def _item_tooltip(self, item_id: str, count: int, agent: object | None, *, prefix: str = "Item") -> list[str]:
        item = ITEMS[item_id]
        lines = [f"{prefix}: {item.name}", self._item_description(item), self._tags_line(item.tags), f"Stack: {count}/{item.max_stack}"]
        if item.food:
            quality = getattr(agent, "food_quality", {}).get(item_id, 0) if agent is not None else 0
            bonus = f" (+{quality} quality)" if quality else ""
            lines.append(f"Food/effect: +{item.food + quality}{bonus}")
        if item.durability:
            current = getattr(agent, "tool_durability", {}).get(item_id, item.durability) if agent is not None else item.durability
            lines.append(f"Durability: {current}/{item.durability}")
        if item.tool_tags:
            lines.append(f"Tool: power {item.tool_power} | {', '.join(item.tool_tags)}")
        if item.armor:
            lines.append(f"Armor: {item.armor}")
        if item.equip_slot:
            slot = "ring finger" if item.equip_slot == "ring" else item.equip_slot
            lines.append(f"Equip slot: {slot}")
        if "station" in item.tags:
            lines.append("Placeable station")
        elif item_id in {"wooden_floor", "stone_floor", "wooden_wall", "stone_wall", "wooden_door"}:
            lines.append("Placeable building piece")
        elif item_id in PLACEABLE_ITEMS:
            lines.append("Placeable object")
        return lines

    @staticmethod
    def _tags_line(tags: tuple[str, ...]) -> str:
        return "Tags: " + (", ".join(tags) if tags else "none")

    @staticmethod
    def _terrain_description(terrain: object) -> str:
        tags = set(terrain.tags)
        if "water" in tags:
            return "Water tile: fishable with a rod or net."
        if "sand" in tags or "coast" in tags:
            return "Shore terrain: sand, shells, crabs, and coastal resources."
        if "forest" in tags:
            return "Forest ground: trees, plants, wildlife, and early materials."
        if "rock" in tags or "mountain" in tags:
            return "Rocky terrain: stone, caves, and ore veins can appear here."
        if "clay" in tags:
            return "Clay hills: useful for kiln and building progression."
        return "Walkable world tile with biome-specific resources."

    @staticmethod
    def _feature_description(feature: object) -> str:
        tags = set(feature.tags)
        if "hostile" in tags:
            return "Hostile wildlife: dangerous if an agent gets too close."
        if "animal" in tags or "fish" in tags:
            return "Wildlife: can move around and may provide food or materials."
        if "station" in tags:
            return "Crafting station: unlocks nearby station recipes."
        if "wall" in tags or "building" in tags:
            return "Building object: can help form enclosed houses."
        if "tree" in tags:
            return "Tree: chop with an axe for logs and wood materials."
        if "ore" in tags:
            return "Ore feature: mine with the right pickaxe power."
        if "plant" in tags:
            return "Gatherable plant feature."
        return "World feature that can be inspected or interacted with."

    @staticmethod
    def _item_description(item: object) -> str:
        tags = set(item.tags)
        if "potion" in tags:
            return "Potion: drink/use it from inventory for a survival effect."
        if item.food > 0:
            return "Food item: restores hunger when eaten."
        if item.armor:
            return "Equipment: armor that reduces incoming damage."
        if item.tool_tags:
            return "Tool or weapon: has durability and action power."
        if item.equip_slot:
            return "Equippable accessory."
        if "station" in tags:
            return "Placeable station used for crafting progression."
        if "building" in tags:
            return "Placeable construction item."
        if "material" in tags:
            return "Crafting material for recipes and experiments."
        return "Inventory item."

    def _tooltip(self, screen: pygame.Surface, lines: list[str], mouse_pos: tuple[int, int]) -> None:
        wrapped: list[str] = []
        max_width = 300
        for line in lines:
            if not line:
                wrapped.append("")
                continue
            current = ""
            for word in line.split():
                test = word if not current else f"{current} {word}"
                if self.font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        wrapped.append(current)
                    current = word
            if current:
                wrapped.append(current)
        line_h = 17
        width = min(max_width + 18, max((self.font.size(line)[0] for line in wrapped if line), default=80) + 18)
        height = max(28, len(wrapped) * line_h + 14)
        x = mouse_pos[0] + 18
        y = mouse_pos[1] + 18
        if x + width > screen.get_width() - 8:
            x = mouse_pos[0] - width - 18
        if y + height > screen.get_height() - 8:
            y = mouse_pos[1] - height - 18
        rect = pygame.Rect(max(8, x), max(8, y), width, height)
        pygame.draw.rect(screen, (12, 15, 18), rect, border_radius=6)
        pygame.draw.rect(screen, (96, 111, 126), rect, 1, border_radius=6)
        ty = rect.y + 7
        for index, line in enumerate(wrapped):
            color = (246, 244, 224) if index == 0 else (207, 216, 224)
            if not line:
                ty += 6
                continue
            img = self.font.render(line, True, color)
            screen.blit(img, (rect.x + 9, ty))
            ty += line_h

    def _grid(self, screen: pygame.Surface, camera: Camera, rect: pygame.Rect, sx: int, sy: int, ex: int, ey: int) -> None:
        for x in range(sx, ex + 1):
            px = int(x * TILE_SIZE - camera.x)
            pygame.draw.line(screen, (0, 0, 0, 24), (px, rect.top), (px, rect.bottom))
        for y in range(sy, ey + 1):
            py = int(y * TILE_SIZE - camera.y)
            pygame.draw.line(screen, (0, 0, 0, 24), (rect.left, py), (rect.right, py))

    def _text(self, screen: pygame.Surface, text: str, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int], line: int) -> int:
        img = font.render(text, True, color)
        screen.blit(img, (x, y))
        return y + line

    def _wrap(self, screen: pygame.Surface, text: str, x: int, y: int, width: int, font: pygame.font.Font, color: tuple[int, int, int] = (210, 214, 218)) -> int:
        current = ""
        for word in text.split():
            test = word if not current else f"{current} {word}"
            if font.size(test)[0] <= width:
                current = test
            else:
                if current:
                    y = self._text(screen, current, x, y, font, color, 15)
                current = word
        if current:
            y = self._text(screen, current, x, y, font, color, 15)
        return y + 3

    def _stat_row(self, screen: pygame.Surface, icon_id: str, label: str, value: float, x: int, y: int, color: tuple[int, int, int]) -> int:
        icon = self.assets.get(icon_id)
        screen.blit(icon, (x, y - 1))
        bar_x = x + 30
        bar_y = y + 4
        bar_w = 178
        bar_h = 10
        value = max(0.0, min(100.0, value))
        pygame.draw.rect(screen, (46, 52, 59), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_w * value / 100), bar_h), border_radius=4)
        pygame.draw.rect(screen, (92, 101, 112), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        text = self.small.render(f"{label} {value:04.1f}", True, (228, 231, 235))
        screen.blit(text, (bar_x + bar_w + 10, y + 1))
        return y + 20

    @staticmethod
    def _agent_pose(agent: object, progress: float) -> tuple[float, float, float, float]:
        t = max(0.0, min(1.0, progress))
        t = t * t * (3 - 2 * t)
        rx = agent.start_x + (agent.x - agent.start_x) * t
        ry = agent.start_y + (agent.y - agent.start_y) * t
        dx = agent.start_facing[0] + (agent.facing[0] - agent.start_facing[0]) * t
        dy = agent.start_facing[1] + (agent.facing[1] - agent.start_facing[1]) * t
        length = math.hypot(dx, dy) or 1.0
        return rx, ry, dx / length, dy / length
