from __future__ import annotations

import base64
import json
import pickle
from collections import Counter, deque
from pathlib import Path
from typing import Any

from .agent import Agent, ChatMessage, PERSONAS, RECENT_ACTION_LIMIT, RECENT_SPEECH_LIMIT, RECENT_THOUGHT_LIMIT
from .constants import HEARD_MEMORY_LIMIT, PRIVATE_MEMORY_LIMIT, SAVE_DIR
from .world import Tile


SAVE_VERSION = 1


def save_simulation(sim: object, path: Path | str | None = None) -> Path:
    target = Path(path) if path else SAVE_DIR / "autosave.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = simulation_to_dict(sim)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_simulation(sim: object, path: Path | str) -> None:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    apply_simulation_state(sim, payload)


def simulation_to_dict(sim: object) -> dict[str, Any]:
    return {
        "version": SAVE_VERSION,
        "seed": sim.seed,
        "round_index": sim.round_index,
        "sim_rng": _pack_state(sim.rng.getstate()),
        "world": {
            "width": sim.world.width,
            "height": sim.world.height,
            "seed": sim.world.seed,
            "rng": _pack_state(sim.world.rng.getstate()),
            "tiles": [
                [
                    {
                        "terrain": tile.terrain,
                        "feature": tile.feature,
                        "floor": tile.floor,
                        "hp": tile.hp,
                        "shade": tile.shade,
                    }
                    for tile in row
                ]
                for row in sim.world.tiles
            ],
        },
        "agents": [_agent_to_dict(agent) for agent in sim.agents],
        "chat": [_chat_to_dict(message) for message in sim.chat],
    }


def apply_simulation_state(sim: object, payload: dict[str, Any]) -> None:
    if int(payload.get("version", 0)) != SAVE_VERSION:
        raise ValueError(f"Unsupported save version: {payload.get('version')}")
    world_payload = payload["world"]
    sim.seed = int(payload["seed"])
    sim.round_index = int(payload["round_index"])
    sim.rng.setstate(_unpack_state(payload["sim_rng"]))
    sim.world.width = int(world_payload["width"])
    sim.world.height = int(world_payload["height"])
    sim.world.seed = int(world_payload["seed"])
    sim.world.rng.setstate(_unpack_state(world_payload["rng"]))
    sim.world.tiles = [
        [
            Tile(
                terrain=str(tile["terrain"]),
                feature=tile.get("feature"),
                floor=tile.get("floor"),
                hp=int(tile.get("hp", 0)),
                shade=int(tile.get("shade", 0)),
            )
            for tile in row
        ]
        for row in world_payload["tiles"]
    ]
    sim.agents = [_agent_from_dict(data) for data in payload["agents"]]
    sim.chat = [_chat_from_dict(data) for data in payload.get("chat", [])]
    sim.round_events = []
    sim.round_thinking = False
    sim.logger.write_world(sim._world_replay_payload())
    sim.logger.log_replay(sim._replay_payload())


def _agent_to_dict(agent: Agent) -> dict[str, Any]:
    return {
        "agent_id": agent.agent_id,
        "persona_index": PERSONAS.index(agent.persona),
        "x": agent.x,
        "y": agent.y,
        "color": list(agent.color),
        "facing": list(agent.facing),
        "start_x": agent.start_x,
        "start_y": agent.start_y,
        "start_facing": list(agent.start_facing),
        "inventory": dict(agent.inventory),
        "tool_durability": dict(agent.tool_durability),
        "food_quality": dict(agent.food_quality),
        "equipment": dict(agent.equipment),
        "rings": list(agent.rings),
        "known_recipes": sorted(agent.known_recipes),
        "private_memory": list(agent.private_memory),
        "heard_messages": [_chat_to_dict(message) for message in agent.heard_messages],
        "recent_actions": list(agent.recent_actions),
        "recent_speech": list(agent.recent_speech),
        "recent_thoughts": list(agent.recent_thoughts),
        "health": agent.health,
        "hunger": agent.hunger,
        "energy": agent.energy,
        "chat_cooldown": agent.chat_cooldown,
        "last_action": agent.last_action,
        "last_intent": agent.last_intent,
        "last_thought": agent.last_thought,
        "last_private_note": agent.last_private_note,
        "last_seen_chat_round": agent.last_seen_chat_round,
        "inventory_slot_limit": agent.inventory_slot_limit,
    }


def _agent_from_dict(data: dict[str, Any]) -> Agent:
    agent = Agent(
        agent_id=int(data["agent_id"]),
        persona=PERSONAS[int(data["persona_index"])],
        x=int(data["x"]),
        y=int(data["y"]),
        color=tuple(data["color"]),
    )
    agent.facing = tuple(data.get("facing", [0, 1]))
    agent.start_x = int(data.get("start_x", agent.x))
    agent.start_y = int(data.get("start_y", agent.y))
    agent.start_facing = tuple(data.get("start_facing", agent.facing))
    agent.inventory = Counter({item: int(count) for item, count in data.get("inventory", {}).items() if int(count) > 0})
    agent.tool_durability = {item: int(value) for item, value in data.get("tool_durability", {}).items()}
    agent.food_quality = {item: int(value) for item, value in data.get("food_quality", {}).items()}
    agent.equipment = {slot: item for slot, item in data.get("equipment", {}).items()}
    agent.rings = list(data.get("rings", []))
    agent.known_recipes = set(data.get("known_recipes", []))
    agent.private_memory = deque(data.get("private_memory", []), maxlen=PRIVATE_MEMORY_LIMIT)
    agent.heard_messages = deque((_chat_from_dict(message) for message in data.get("heard_messages", [])), maxlen=HEARD_MEMORY_LIMIT)
    agent.recent_actions = deque(data.get("recent_actions", []), maxlen=RECENT_ACTION_LIMIT)
    agent.recent_speech = deque(data.get("recent_speech", []), maxlen=RECENT_SPEECH_LIMIT)
    agent.recent_thoughts = deque(data.get("recent_thoughts", []), maxlen=RECENT_THOUGHT_LIMIT)
    agent.health = float(data.get("health", 100.0))
    agent.hunger = float(data.get("hunger", 90.0))
    agent.energy = float(data.get("energy", 100.0))
    agent.chat_cooldown = int(data.get("chat_cooldown", 0))
    agent.last_action = str(data.get("last_action", "looking around"))
    agent.last_intent = str(data.get("last_intent", "survive"))
    agent.last_thought = str(data.get("last_thought", "I need to get oriented and find something useful."))
    agent.last_private_note = str(data.get("last_private_note", ""))
    agent.last_seen_chat_round = int(data.get("last_seen_chat_round", -1))
    agent.inventory_slot_limit = int(data.get("inventory_slot_limit", agent.inventory_slot_limit))
    return agent


def _chat_to_dict(message: ChatMessage) -> dict[str, Any]:
    return {
        "round_index": message.round_index,
        "speaker": message.speaker,
        "text": message.text,
        "x": message.x,
        "y": message.y,
    }


def _chat_from_dict(data: dict[str, Any]) -> ChatMessage:
    return ChatMessage(
        round_index=int(data["round_index"]),
        speaker=str(data["speaker"]),
        text=str(data["text"]),
        x=int(data["x"]),
        y=int(data["y"]),
    )


def _pack_state(state: object) -> str:
    return base64.b64encode(pickle.dumps(state, protocol=4)).decode("ascii")


def _unpack_state(text: str) -> object:
    return pickle.loads(base64.b64decode(text.encode("ascii")))
