from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agents_survival_reborn.constants import CHAT_RADIUS, DEFAULT_SEED
from agents_survival_reborn.data import FEATURES, TERRAINS
from agents_survival_reborn.llm import LLMConfig
from agents_survival_reborn.simulation import Simulation
from agents_survival_reborn.start_items import parse_start_items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run headless social QA rounds for LLM agents.")
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--agents", type=int, default=3)
    parser.add_argument("--width", type=int, default=48)
    parser.add_argument("--height", type=int, default=36)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--llm-retries", type=int, default=2)
    parser.add_argument("--gemini-agents", type=int, default=0)
    parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    parser.add_argument("--start-items", default="", help="Comma-separated item=count kit granted to every agent at spawn.")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--cluster", action="store_true", help="Move agents into one small starting group.")
    parser.add_argument("--mixed-biome", action="store_true", help="Cluster agents near varied progression terrain for tech-path QA.")
    parser.add_argument("--summary-json", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    gemini_api_key = os.getenv("AGENTS_SURVIVAL_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    api_key = os.getenv("AGENTS_SURVIVAL_API_KEY") or (gemini_api_key if args.provider.lower() in {"gemini", "google"} else "")
    llm_config = LLMConfig(
        enabled=not args.offline,
        model=args.model,
        api_key=api_key,
        provider=args.provider,
        base_url=args.base_url.rstrip("/"),
        timeout=args.timeout,
        workers=max(1, args.workers),
        max_output_tokens=args.max_output_tokens,
        gemini_agent_count=max(0, args.gemini_agents),
        gemini_model=args.gemini_model,
        gemini_api_key=gemini_api_key,
        retry_count=max(0, args.llm_retries),
    )
    sim = Simulation(width=args.width, height=args.height, agent_count=args.agents, seed=args.seed, llm_config=llm_config)
    try:
        start_items = parse_start_items(args.start_items)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if start_items:
        sim.grant_starting_items(start_items)
    if args.mixed_biome:
        cluster_agents(sim, center=find_mixed_biome_center(sim))
    elif args.cluster:
        cluster_agents(sim)
    print(f"session={sim.logger.session_dir}", flush=True)
    print(f"agents={', '.join(f'{agent.name}@{agent.x},{agent.y}' for agent in sim.agents)}", flush=True)
    for _ in range(args.rounds):
        sim.advance_round()
        round_chats = [msg for msg in sim.chat if msg.round_index == sim.round_index - 1]
        actions = Counter(event.kind for event in sim.round_events)
        print(
            f"round={sim.round_index:03d} ok={sim.llm.last_successes}/{sim.llm.last_requested} "
            f"fallback={sim.llm.last_fallbacks} actions={dict(actions)} chat={len(round_chats)}"
            ,
            flush=True,
        )
        for msg in round_chats:
            print(f"  chat {msg.speaker}: {msg.text}", flush=True)
        if sim.llm.last_error:
            print(f"  llm_error={sim.llm.last_error}", flush=True)
    summary = summarize_session(sim.logger.session_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if args.summary_json:
        Path(args.summary_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def cluster_agents(sim: Simulation, center: tuple[int, int] | None = None) -> None:
    center = center or find_passable_center(sim)
    offsets = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (2, 0), (0, 2), (-2, 0)]
    used: set[tuple[int, int]] = set()
    for agent, offset in zip(sim.agents, offsets):
        for x, y in nearby_positions(center[0] + offset[0], center[1] + offset[1], radius=CHAT_RADIUS // 2):
            if (x, y) in used or not sim.world.in_bounds(x, y):
                continue
            if sim.world.can_enter(agent, x, y):
                agent.x = agent.start_x = x
                agent.y = agent.start_y = y
                used.add((x, y))
                break
        agent.chat_cooldown = 0


def find_passable_center(sim: Simulation) -> tuple[int, int]:
    preferred = (sim.world.width // 2, sim.world.height // 2)
    probe = sim.agents[0]
    for x, y in nearby_positions(*preferred, radius=max(sim.world.width, sim.world.height)):
        if sim.world.in_bounds(x, y) and sim.world.can_enter(probe, x, y):
            return x, y
    return probe.x, probe.y


def find_mixed_biome_center(sim: Simulation) -> tuple[int, int]:
    probe = sim.agents[0]
    best: tuple[int, int, int, int] | None = None
    for y in range(2, sim.world.height - 2):
        for x in range(2, sim.world.width - 2):
            if not sim.world.can_enter(probe, x, y):
                continue
            score = mixed_biome_score(sim, x, y)
            if score <= 0:
                continue
            distance = abs(x - sim.world.width // 2) + abs(y - sim.world.height // 2)
            candidate = (score, -distance, x, y)
            if best is None or candidate > best:
                best = candidate
    if best:
        return best[2], best[3]
    return find_passable_center(sim)


def mixed_biome_score(sim: Simulation, cx: int, cy: int) -> int:
    terrain_tags: set[str] = set()
    feature_tags: set[str] = set()
    terrain_names: set[str] = set()
    features = 0
    for x, y in nearby_positions(cx, cy, radius=8):
        if not sim.world.in_bounds(x, y):
            continue
        tile = sim.world.tile(x, y)
        terrain = TERRAINS[tile.terrain]
        terrain_tags.update(terrain.tags)
        terrain_names.add(tile.terrain)
        if tile.feature:
            features += 1
            feature_tags.update(FEATURES[tile.feature].tags)
    score = 0
    for tag in ("grass", "forest", "rock", "sand", "hill", "clay", "coast", "water"):
        if tag in terrain_tags:
            score += 4
    for tag in ("tree", "stone", "rock", "ore", "food", "animal", "fish"):
        if tag in feature_tags:
            score += 5
    score += min(12, features)
    score += min(10, len(terrain_names))
    return score


def nearby_positions(cx: int, cy: int, radius: int) -> list[tuple[int, int]]:
    positions: list[tuple[int, int]] = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            positions.append((cx + dx, cy + dy))
    return sorted(positions, key=lambda pos: (abs(pos[0] - cx) + abs(pos[1] - cy), abs(pos[1] - cy), abs(pos[0] - cx)))


def summarize_session(session_dir: Path) -> dict[str, Any]:
    chat = read_jsonl(session_dir / "chat.jsonl")
    thoughts = read_jsonl(session_dir / "thoughts.jsonl")
    turns = read_jsonl(session_dir / "turns.jsonl")
    blocked = Counter(row.get("speech_blocked_reason") or "" for row in thoughts if row.get("speech") and not row.get("speech_allowed"))
    actions = Counter(row.get("kind", "") for row in turns)
    speakers = Counter(row.get("speaker", "") for row in chat)
    return {
        "session_dir": str(session_dir),
        "chat_lines": len(chat),
        "speakers": dict(speakers),
        "blocked_speech": {key: value for key, value in blocked.items() if key},
        "actions": dict(actions),
        "last_chat": chat[-12:],
        "last_thoughts": thoughts[-12:],
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
