from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pygame

from agents_survival_reborn.assets import AssetManager
from agents_survival_reborn.constants import FPS, HUD_WIDTH, LOG_DIR, SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from agents_survival_reborn.data import FEATURES, TERRAINS
from agents_survival_reborn.renderer import Camera, Renderer
from agents_survival_reborn.world import Tile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play an Agents Survival Reborn replay without LLM delays.")
    parser.add_argument("session", nargs="?", help="logs/session_YYYYMMDD_HHMMSS directory. Defaults to newest replay.")
    parser.add_argument("--speed", type=float, default=1.0, help="Replay speed multiplier.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    session = Path(args.session) if args.session else newest_session()
    if not session.is_absolute():
        session = ROOT_DIR / session
    world_path = session / "world.json"
    replay_path = session / "replay.jsonl"
    if not world_path.exists() or not replay_path.exists():
        raise SystemExit(f"Replay files not found in {session}")
    world_data = json.loads(world_path.read_text(encoding="utf-8"))
    frames = read_jsonl(replay_path)
    if not frames:
        raise SystemExit(f"No replay frames in {replay_path}")

    pygame.init()
    pygame.display.set_caption(f"Agents Survival Reborn Replay - {session.name}")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    assets = AssetManager()
    renderer = Renderer(assets)
    camera = Camera()
    selected = 0
    paused = False
    frame_pos = 0.0
    speed = max(0.1, args.speed)

    running = True
    try:
        while running:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_TAB:
                        selected += 1
                        camera.follow = True
                    elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        speed = min(12.0, speed * 1.4)
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        speed = max(0.1, speed / 1.4)
                    elif event.key == pygame.K_LEFTBRACKET:
                        frame_pos = max(0.0, frame_pos - 1)
                    elif event.key == pygame.K_RIGHTBRACKET:
                        frame_pos = min(float(len(frames) - 1), frame_pos + 1)
                    elif event.key == pygame.K_f:
                        camera.follow = not camera.follow
            if not paused:
                frame_pos = min(float(len(frames) - 1), frame_pos + dt * speed * 2.0)
            frame_index = int(frame_pos)
            progress = frame_pos - frame_index
            sim = make_replay_sim(world_data, frames[frame_index], session, speed)
            if sim.agents:
                selected %= len(sim.agents)
            move_camera(camera, sim, selected, dt)
            renderer.draw(screen, sim, camera, selected, progress, f"{session.name} x{speed:.1f}", paused)
            pygame.display.flip()
    finally:
        pygame.quit()
    return 0


def newest_session() -> Path:
    sessions = sorted((path for path in LOG_DIR.glob("session_*") if (path / "replay.jsonl").exists()), key=lambda path: path.stat().st_mtime, reverse=True)
    if not sessions:
        raise SystemExit(f"No replay sessions found in {LOG_DIR}")
    return sessions[0]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_replay_sim(world_data: dict[str, Any], frame: dict[str, Any], session: Path, speed: float) -> SimpleNamespace:
    world = SimpleNamespace(width=world_data["width"], height=world_data["height"])
    terrain_rows = [row.split(",") for row in world_data["terrain_rows"]]
    shade_rows = world_data.get("shade_rows") or [[0 for _ in range(world.width)] for _ in range(world.height)]
    feature_map = {(entry["x"], entry["y"]): entry for entry in frame.get("features", [])}
    floor_map = {(entry["x"], entry["y"]): entry["floor"] for entry in frame.get("floors", [])}

    def tile(x: int, y: int) -> Tile:
        feature_entry = feature_map.get((x, y))
        feature_id = feature_entry["feature"] if feature_entry else None
        hp = int(feature_entry.get("hp", FEATURES[feature_id].max_hp)) if feature_entry else 0
        return Tile(terrain_rows[y][x], feature_id, floor_map.get((x, y)), hp, shade_rows[y][x])

    world.tile = tile
    world.can_enter = lambda agent, x, y: 0 <= x < world.width and 0 <= y < world.height and TERRAINS[tile(x, y).terrain].passable

    personas = {entry["agent_id"]: entry for entry in world_data.get("agents", [])}
    agents = []
    for entry in frame.get("agents", []):
        persona_data = personas.get(entry["agent_id"], {})
        persona = SimpleNamespace(
            archetype=persona_data.get("archetype", ""),
            origin=persona_data.get("origin", ""),
            long_goal=persona_data.get("long_goal", ""),
        )
        inventory = {item: count for item, count in entry.get("inventory", {}).items() if count > 0}
        agents.append(
            SimpleNamespace(
                agent_id=entry["agent_id"],
                name=entry["name"],
                persona=persona,
                sprite=persona_data.get("sprite", "agent_methodical_builder"),
                color=tuple(persona_data.get("color", [220, 220, 220])),
                x=entry["x"],
                y=entry["y"],
                start_x=entry.get("start_x", entry["x"]),
                start_y=entry.get("start_y", entry["y"]),
                facing=tuple(entry.get("facing", [0, 1])),
                start_facing=tuple(entry.get("start_facing", entry.get("facing", [0, 1]))),
                health=entry.get("health", 100.0),
                hunger=entry.get("hunger", 100.0),
                energy=entry.get("energy", 100.0),
                armor_rating=entry.get("armor", 0),
                equipment=dict(entry.get("equipment", {})),
                rings=list(entry.get("rings", [])),
                tool_durability={},
                food_quality={},
                inventory=inventory,
                used_inventory_slots=entry.get("used_inventory_slots", len(inventory)),
                inventory_slot_limit=entry.get("inventory_slot_limit", 15),
                last_action=entry.get("last_action", ""),
                last_intent=entry.get("last_intent", ""),
                last_thought=entry.get("last_thought", ""),
            )
        )
    chat = [SimpleNamespace(**msg) for msg in frame.get("chat", [])]
    llm_config = SimpleNamespace(provider="replay", enabled=False, model="recorded", timeout=0)
    llm = SimpleNamespace(config=llm_config, last_successes=0, last_requested=0, last_fallbacks=0, last_duration=0.0, last_error="")
    return SimpleNamespace(
        world=world,
        agents=agents,
        chat=chat,
        round_index=frame.get("round", 0),
        round_thinking=False,
        llm=llm,
        replay_session=session.name,
        replay_speed=speed,
    )


def move_camera(camera: Camera, sim: SimpleNamespace, selected: int, dt: float) -> None:
    keys = pygame.key.get_pressed()
    vx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    vy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
    viewport = (SCREEN_WIDTH - HUD_WIDTH, SCREEN_HEIGHT)
    if vx or vy:
        camera.follow = False
        camera.x += vx * 720 * dt
        camera.y += vy * 720 * dt
    elif camera.follow and sim.agents:
        agent = sim.agents[selected % len(sim.agents)]
        tx = agent.x * TILE_SIZE - viewport[0] / 2
        ty = agent.y * TILE_SIZE - viewport[1] / 2
        camera.x += (tx - camera.x) * min(1.0, dt * 7)
        camera.y += (ty - camera.y) * min(1.0, dt * 7)
    camera.clamp(sim, viewport)


if __name__ == "__main__":
    raise SystemExit(main())
