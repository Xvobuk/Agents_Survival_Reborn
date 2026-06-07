from __future__ import annotations

import argparse
from concurrent.futures import Future
from threading import Thread

import pygame

from .assets import AssetManager
from .constants import (
    AGENT_COUNT,
    FPS,
    HUD_WIDTH,
    ROUND_FRAMES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from .llm import Decision, LLMConfig
from .renderer import Camera, Renderer
from .simulation import Simulation
from .start_items import parse_start_items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="Use real generative-model agents.")
    parser.add_argument("--llama", action="store_true", help="Use local Ollama with native structured JSON output.")
    parser.add_argument("--offline", action="store_true", help="Run deterministic fallback decisions without API calls.")
    parser.add_argument("--provider", default=None, help="openai, ollama, compatible, or gemini.")
    parser.add_argument("--base-url", default=None, help="API base URL. Ollama default: http://localhost:11434")
    parser.add_argument("--model", default=None, help="Model name, e.g. gpt-5 or llama3.1.")
    parser.add_argument("--gemini-agents", type=int, default=None, help="Number of agents routed through Gemini while the rest use the primary provider.")
    parser.add_argument("--gemini-model", default=None, help="Gemini model for mixed mode, e.g. gemini-2.5-flash.")
    parser.add_argument("--llm-timeout", type=float, default=None, help="Seconds to wait for one model call.")
    parser.add_argument("--llm-workers", type=int, default=None, help="Concurrent model calls. Local Ollama usually likes 1.")
    parser.add_argument("--llm-max-output-tokens", type=int, default=None, help="Token budget for one model decision JSON.")
    parser.add_argument("--agents", type=int, default=AGENT_COUNT)
    parser.add_argument("--width", type=int, default=WORLD_WIDTH)
    parser.add_argument("--height", type=int, default=WORLD_HEIGHT)
    parser.add_argument("--round-frames", type=int, default=ROUND_FRAMES)
    parser.add_argument("--start-items", default="", help="Comma-separated item=count kit granted to every agent at spawn.")
    parser.add_argument("--asset-wizard", action="store_true", help="Ask for missing sprite files before launch.")
    parser.add_argument("--no-record", action="store_true", help="Deprecated: screen videos are no longer recorded; replay JSONL is always written.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pygame.init()
    pygame.display.set_caption("Agents Survival Reborn")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    assets = AssetManager(interactive_wizard=args.asset_wizard)
    renderer = Renderer(assets)
    provider = args.provider
    base_url = args.base_url
    model = args.model
    force_enabled = args.llm
    if args.llama:
        provider = provider or "ollama"
        base_url = base_url or "http://localhost:11434"
        model = model or "llama3.1"
        force_enabled = True
    if args.gemini_agents and args.gemini_agents > 0:
        force_enabled = True
    llm_config = LLMConfig.from_env(
        force_enabled=force_enabled,
        force_disabled=args.offline,
        provider=provider,
        model=model,
        base_url=base_url,
        timeout=args.llm_timeout,
        workers=args.llm_workers,
        max_output_tokens=args.llm_max_output_tokens,
    )
    if args.gemini_agents is not None or args.gemini_model:
        llm_config = LLMConfig(
            enabled=llm_config.enabled,
            model=llm_config.model,
            api_key=llm_config.api_key,
            provider=llm_config.provider,
            base_url=llm_config.base_url,
            timeout=llm_config.timeout,
            workers=llm_config.workers,
            reasoning_effort=llm_config.reasoning_effort,
            max_output_tokens=llm_config.max_output_tokens,
            gemini_agent_count=max(0, args.gemini_agents if args.gemini_agents is not None else llm_config.gemini_agent_count),
            gemini_model=args.gemini_model or llm_config.gemini_model,
            gemini_api_key=llm_config.gemini_api_key,
            gemini_base_url=llm_config.gemini_base_url,
        )
    sim = Simulation(width=args.width, height=args.height, agent_count=args.agents, llm_config=llm_config)
    try:
        start_items = parse_start_items(args.start_items)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if start_items:
        sim.grant_starting_items(start_items)
    camera = Camera()
    selected = 0
    paused = False
    frames_since_round = args.round_frames
    progress = 1.0
    pending_round: Future[dict[int, Decision]] | None = None
    replay_status = f"replay {sim.logger.replay_path.name}"

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
                        selected = (selected + 1) % len(sim.agents)
                        camera.follow = True
                    elif event.key == pygame.K_f:
                        camera.follow = not camera.follow
                    elif event.key == pygame.K_r:
                        replay_status = f"replay {sim.logger.replay_path.name}"
            _camera(camera, sim, selected, dt)
            if pending_round is not None and pending_round.done():
                try:
                    decisions = pending_round.result()
                except Exception as exc:
                    sim.llm.last_error = str(exc)
                    decisions = {}
                sim.apply_round_decisions(decisions)
                sim.round_thinking = False
                pending_round = None
                frames_since_round = 0
                progress = 0.0
            if not paused and pending_round is None:
                frames_since_round += 1
                if frames_since_round >= max(1, args.round_frames):
                    contexts = sim.prepare_round_contexts()
                    sim.round_thinking = True
                    pending_round = _start_round_worker(sim, contexts)
                    progress = 1.0
                else:
                    progress = min(1.0, frames_since_round / max(1, args.round_frames))
            elif pending_round is not None:
                progress = 1.0
            elif paused:
                progress = min(1.0, frames_since_round / max(1, args.round_frames))
            renderer.draw(screen, sim, camera, selected, progress, replay_status, paused)
            pygame.display.flip()
    finally:
        pygame.quit()
    return 0


def _start_round_worker(sim: Simulation, contexts: dict[int, dict[str, object]]) -> Future[dict[int, Decision]]:
    future: Future[dict[int, Decision]] = Future()

    def run() -> None:
        try:
            future.set_result(sim.llm.decide_all(contexts))
        except BaseException as exc:
            future.set_exception(exc)

    Thread(target=run, name="agents-survival-llm-round", daemon=True).start()
    return future


def _camera(camera: Camera, sim: Simulation, selected: int, dt: float) -> None:
    keys = pygame.key.get_pressed()
    vx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    vy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
    viewport = (SCREEN_WIDTH - HUD_WIDTH, SCREEN_HEIGHT)
    if vx or vy:
        camera.follow = False
        camera.x += vx * 720 * dt
        camera.y += vy * 720 * dt
    elif camera.follow:
        agent = sim.agents[selected % len(sim.agents)]
        tx = agent.x * TILE_SIZE - viewport[0] / 2
        ty = agent.y * TILE_SIZE - viewport[1] / 2
        camera.x += (tx - camera.x) * min(1.0, dt * 7)
        camera.y += (ty - camera.y) * min(1.0, dt * 7)
    camera.clamp(sim, viewport)
