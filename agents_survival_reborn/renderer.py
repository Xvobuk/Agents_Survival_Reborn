from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from .assets import AssetManager
from .constants import HUD_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from .data import FEATURES, ITEMS, TERRAINS, item_name


@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    follow: bool = False

    def clamp(self, sim: object, viewport: tuple[int, int]) -> None:
        self.x = max(0, min(self.x, sim.world.width * TILE_SIZE - viewport[0]))
        self.y = max(0, min(self.y, sim.world.height * TILE_SIZE - viewport[1]))


class Renderer:
    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        pygame.font.init()
        self.font = pygame.font.SysFont("segoeui", 15) or pygame.font.Font(None, 15)
        self.small = pygame.font.SysFont("consolas", 12) or pygame.font.Font(None, 12)
        self.title = pygame.font.SysFont("segoeui", 22, bold=True) or pygame.font.Font(None, 22)

    def draw(self, screen: pygame.Surface, sim: object, camera: Camera, selected: int, progress: float, recorder_status: str, paused: bool) -> None:
        screen.fill((10, 12, 15))
        world_view = pygame.Rect(0, 0, screen.get_width() - HUD_WIDTH, screen.get_height())
        self._world(screen, sim, camera, world_view, selected, progress)
        self._hud(screen, sim, selected, recorder_status, paused)

    def _world(self, screen: pygame.Surface, sim: object, camera: Camera, rect: pygame.Rect, selected: int, progress: float) -> None:
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

    def _hud(self, screen: pygame.Surface, sim: object, selected: int, recorder_status: str, paused: bool) -> None:
        panel = pygame.Rect(screen.get_width() - HUD_WIDTH, 0, HUD_WIDTH, screen.get_height())
        pygame.draw.rect(screen, (18, 22, 27), panel)
        pygame.draw.line(screen, (70, 78, 88), (panel.left, 0), (panel.left, panel.bottom), 2)
        x, y = panel.left + 16, 16
        y = self._text(screen, "Agents Survival Reborn", x, y, self.title, (242, 244, 247), 28)
        state = "THINKING" if getattr(sim, "round_thinking", False) else "PAUSED" if paused else "RUNNING"
        y = self._text(screen, f"Round {sim.round_index} | {state}", x, y, self.font, (184, 202, 213), 22)
        if sim.llm.config.provider in {"compatible", "llama", "ollama"}:
            llm_state = "local" if sim.llm.config.enabled else "offline"
        else:
            llm_state = "on" if sim.llm.config.enabled and sim.llm.config.api_key else "no key" if sim.llm.config.enabled else "offline"
        y = self._wrap(
            screen,
            f"LLM: {llm_state} | {sim.llm.config.provider} | {sim.llm.config.model} | ok {sim.llm.last_successes}/{sim.llm.last_requested} | fallback {sim.llm.last_fallbacks} | {sim.llm.last_duration:.1f}s/{sim.llm.config.timeout:.0f}s",
            x,
            y,
            360,
            self.small,
            (171, 190, 203),
        )
        if sim.llm.last_error:
            y = self._wrap(screen, f"LLM error: {sim.llm.last_error[:120]}", x, y, 360, self.small, (230, 151, 126))
        y = self._wrap(screen, f"Recorder: {recorder_status}", x, y, 360, self.small, (142, 162, 174))
        agent = sim.agents[selected % len(sim.agents)]
        y += 8
        y = self._text(screen, f"{agent.name} | {agent.persona.archetype}", x, y, self.title, agent.color, 26)
        y = self._wrap(screen, agent.persona.origin, x, y, 360, self.small, (202, 210, 217))
        y = self._wrap(screen, f"Goal: {agent.persona.long_goal}", x, y, 360, self.small, (202, 210, 217))
        y = self._stat_row(screen, "ui_health", "HP", agent.health, x, y, (216, 72, 82))
        y = self._stat_row(screen, "ui_hunger", "Food", agent.hunger, x, y, (226, 165, 72))
        y = self._stat_row(screen, "ui_energy", "Stamina", agent.energy, x, y, (78, 181, 226))
        y = self._wrap(screen, f"Intent: {agent.last_intent}", x, y, 360, self.small, (215, 218, 222))
        y = self._wrap(screen, f"Thought: {agent.last_thought}", x, y, 360, self.small, (184, 214, 190))
        y = self._wrap(screen, f"Last: {agent.last_action}", x, y, 360, self.small, (215, 218, 222))
        y += 8
        y = self._inventory_grid(screen, agent, x, y)
        y += 8
        self._minimap(screen, sim, pygame.Rect(x, y, 360, 140), selected)
        y += 154
        y = self._text(screen, "Chat", x, y, self.font, (242, 244, 247), 21)
        for msg in sim.chat[-12:]:
            y = self._wrap(screen, f"{msg.speaker}: {msg.text}", x, y, 360, self.small, (182, 215, 222))
            if y > screen.get_height() - 18:
                break

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

    def _inventory_grid(self, screen: pygame.Surface, agent: object, x: int, y: int) -> int:
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
        rows = math.ceil(limit / cols)
        y += rows * (slot + gap) + 4
        if len(inv) > limit:
            y = self._text(screen, f"+{len(inv) - limit} hidden", x, y, self.small, (230, 151, 126), 15)
        return y

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
