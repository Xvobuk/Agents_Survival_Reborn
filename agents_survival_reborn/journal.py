from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import LOG_DIR


class RunLogger:
    def __init__(self, *, seed: int, width: int, height: int, agent_count: int, root: Path = LOG_DIR) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = root / f"session_{stamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.chat_path = self.session_dir / "chat.jsonl"
        self.thoughts_path = self.session_dir / "thoughts.jsonl"
        self.turns_path = self.session_dir / "turns.jsonl"
        self.replay_path = self.session_dir / "replay.jsonl"
        self.world_path = self.session_dir / "world.json"
        self.meta_path = self.session_dir / "meta.json"
        self._write_json(
            self.meta_path,
            {
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "seed": seed,
                "world": {"width": width, "height": height},
                "agent_count": agent_count,
                "files": {
                    "chat": self.chat_path.name,
                    "thoughts": self.thoughts_path.name,
                    "turns": self.turns_path.name,
                    "world": self.world_path.name,
                    "replay": self.replay_path.name,
                },
            },
        )

    def write_world(self, payload: dict[str, Any]) -> None:
        self._write_json(self.world_path, payload)

    def log_chat(self, payload: dict[str, Any]) -> None:
        self._append_jsonl(self.chat_path, payload)

    def log_thought(self, payload: dict[str, Any]) -> None:
        self._append_jsonl(self.thoughts_path, payload)

    def log_turn(self, payload: dict[str, Any]) -> None:
        self._append_jsonl(self.turns_path, payload)

    def log_replay(self, payload: dict[str, Any]) -> None:
        self._append_jsonl(self.replay_path, payload)

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
