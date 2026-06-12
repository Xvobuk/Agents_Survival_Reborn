from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent import Agent
from .constants import CODEX_CONTROL_DIR
from .llm import ACTION_VALUES, DECISION_KEYS, Decision


class CodexControl:
    def __init__(self, root: Path | str = CODEX_CONTROL_DIR, *, poll_seconds: float = 0.5) -> None:
        self.root = Path(root)
        self.poll_seconds = poll_seconds
        self.root.mkdir(parents=True, exist_ok=True)
        self.status = "idle"

    def decide_all(self, sim: object, contexts: dict[int, dict[str, Any]]) -> dict[int, Decision]:
        self._write_round(sim, contexts)
        expected = set(contexts)
        decisions: dict[int, Decision] = {}
        self.status = f"waiting for Codex decisions 0/{len(expected)}"
        while set(decisions) != expected:
            for agent in sim.agents:
                if agent.agent_id not in expected or agent.agent_id in decisions:
                    continue
                decision = self._read_decision(agent, sim.round_index)
                if decision:
                    decisions[agent.agent_id] = decision
                    self._write_agent_status(agent, f"accepted round {sim.round_index} decision")
            self.status = f"waiting for Codex decisions {len(decisions)}/{len(expected)}"
            if set(decisions) != expected:
                time.sleep(self.poll_seconds)
        self.status = f"received Codex decisions {len(decisions)}/{len(expected)}"
        return decisions

    def _write_round(self, sim: object, contexts: dict[int, dict[str, Any]]) -> None:
        manifest = {
            "round": sim.round_index,
            "mode": "codex-control",
            "expected_agents": [],
            "instructions": "Each Codex player reads only their agent folder and writes decision_round_XXXXXX.json for the current round.",
            "decision_schema": _decision_schema_doc(),
        }
        for agent in sim.agents:
            if agent.agent_id not in contexts:
                continue
            folder = self._agent_dir(agent)
            folder.mkdir(parents=True, exist_ok=True)
            observation = {
                "round": sim.round_index,
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "status": "waiting_for_decision",
                "observation": contexts[agent.agent_id],
                "decision_file": f"decision_round_{sim.round_index:06d}.json",
                "decision_schema": _decision_schema_doc(),
            }
            self._write_json(folder / f"observation_round_{sim.round_index:06d}.json", observation)
            self._write_json(folder / "latest_observation.json", observation)
            self._write_agent_prompt(folder, agent)
            self._write_agent_status(agent, f"waiting for round {sim.round_index} decision")
            manifest["expected_agents"].append(
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "folder": str(folder),
                    "observation": f"observation_round_{sim.round_index:06d}.json",
                    "decision": f"decision_round_{sim.round_index:06d}.json",
                }
            )
        self._write_json(self.root / "current_round.json", manifest)

    def _read_decision(self, agent: Agent, round_index: int) -> Decision | None:
        path = self._agent_dir(agent) / f"decision_round_{round_index:06d}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if int(data.get("round", round_index)) != round_index:
                raise ValueError(f"decision round mismatch; expected {round_index}")
            decision = _decision_from_payload(data)
        except Exception as exc:
            self._write_agent_status(agent, f"invalid decision for round {round_index}: {exc}")
            bad = path.with_suffix(f".invalid_{int(time.time())}.json")
            try:
                path.rename(bad)
            except OSError:
                pass
            return None
        self._write_json(self._agent_dir(agent) / "last_accepted_decision.json", {"round": round_index, **asdict(decision)})
        return decision

    def _agent_dir(self, agent: Agent) -> Path:
        safe_name = "".join(char for char in agent.name if char.isalnum() or char in {"_", "-"})
        return self.root / f"agent_{agent.agent_id}_{safe_name}"

    def _write_agent_prompt(self, folder: Path, agent: Agent) -> None:
        path = folder / "CODEX_PLAYER_PROMPT.md"
        if path.exists():
            return
        path.write_text(
            "\n".join(
                [
                    f"# Codex Player: {agent.name}",
                    "",
                    "You control exactly one survivor in Agents Survival Reborn.",
                    "Do not control other agents. Do not edit their folders.",
                    "Read `latest_observation.json`, choose one legal action, and write the required `decision_round_XXXXXX.json`.",
                    "",
                    "Your decision must be one JSON object:",
                    "",
                    "```json",
                    json.dumps(_empty_decision_example(), indent=2),
                    "```",
                    "",
                    "Use `speech` only for real in-game communication. Use `thought` as your private immediate intent.",
                    "When the game cannot continue, stop after saving has written the latest autosave.",
                ]
            ),
            encoding="utf-8",
        )

    def _write_agent_status(self, agent: Agent, status: str) -> None:
        self._write_json(self._agent_dir(agent) / "status.json", {"agent_id": agent.agent_id, "name": agent.name, "status": status})

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)


def _decision_from_payload(data: dict[str, Any]) -> Decision:
    action = str(data.get("action", "wait")).strip().lower()
    if action not in ACTION_VALUES:
        raise ValueError(f"invalid action {action!r}")
    return Decision(
        action=action,
        dx=_step(data.get("dx", 0)),
        dy=_step(data.get("dy", 0)),
        target_dx=_step(data.get("target_dx", 0)),
        target_dy=_step(data.get("target_dy", 0)),
        recipe_id=str(data.get("recipe_id", ""))[:80],
        place_item=str(data.get("place_item", ""))[:40],
        speech=str(data.get("speech", ""))[:180],
        private_memory=str(data.get("private_memory", ""))[:220],
        intent=str(data.get("intent", ""))[:160],
        thought=str(data.get("thought", ""))[:260],
    )


def _step(value: object) -> int:
    try:
        return max(-1, min(1, int(value)))
    except (TypeError, ValueError):
        return 0


def _decision_schema_doc() -> dict[str, Any]:
    return {
        "required_keys": sorted(DECISION_KEYS),
        "actions": sorted(ACTION_VALUES),
        "notes": [
            "Use dx/dy for move.",
            "Use target_dx/target_dy for interact.",
            "Use recipe_id for craft.",
            "Use place_item for place.",
            "Speech can accompany any action.",
        ],
    }


def _empty_decision_example() -> dict[str, Any]:
    return {
        "round": 0,
        "action": "move",
        "dx": 1,
        "dy": 0,
        "target_dx": 0,
        "target_dy": 0,
        "recipe_id": "",
        "place_item": "",
        "speech": "",
        "private_memory": "Short useful memory if something was learned.",
        "intent": "move toward useful visible resource",
        "thought": "I want a better resource lead before spending materials.",
    }
