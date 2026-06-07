from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from typing import Any

from .constants import DOCS_DIR


DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {
            "type": "string",
            "enum": ["move", "interact", "craft", "experiment", "place", "eat", "talk", "wait"],
        },
        "dx": {"type": "integer", "minimum": -1, "maximum": 1},
        "dy": {"type": "integer", "minimum": -1, "maximum": 1},
        "target_dx": {"type": "integer", "minimum": -1, "maximum": 1},
        "target_dy": {"type": "integer", "minimum": -1, "maximum": 1},
        "recipe_id": {"type": "string"},
        "place_item": {"type": "string", "enum": ["", "workbench", "campfire", "kiln", "tent", "wooden_crate", "wooden_door", "bedroll"]},
        "speech": {"type": "string", "maxLength": 180},
        "private_memory": {"type": "string", "maxLength": 220},
        "intent": {"type": "string", "maxLength": 160},
        "thought": {"type": "string", "maxLength": 260},
    },
    "required": [
        "action",
        "dx",
        "dy",
        "target_dx",
        "target_dy",
        "recipe_id",
        "place_item",
        "speech",
        "private_memory",
        "intent",
        "thought",
    ],
}

DECISION_KEYS = {
    "action",
    "dx",
    "dy",
    "target_dx",
    "target_dy",
    "recipe_id",
    "place_item",
    "speech",
    "private_memory",
    "intent",
    "thought",
}
ACTION_VALUES = {"move", "interact", "craft", "experiment", "place", "eat", "talk", "wait"}
MAP_HALLUCINATION_KEYS = {"name", "description", "dimensions", "tiles", "layout", "terrain"}
OLLAMA_PROVIDERS = {"ollama"}
COMPATIBLE_PROVIDERS = {"compatible", "llama"}
GEMINI_PROVIDERS = {"gemini", "google"}
LOCAL_PROVIDERS = OLLAMA_PROVIDERS | COMPATIBLE_PROVIDERS


@dataclass(frozen=True)
class Decision:
    action: str = "wait"
    dx: int = 0
    dy: int = 0
    target_dx: int = 0
    target_dy: int = 0
    recipe_id: str = ""
    place_item: str = ""
    speech: str = ""
    private_memory: str = ""
    intent: str = "thinking"
    thought: str = ""


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool
    model: str
    api_key: str
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 35.0
    workers: int = 6
    reasoning_effort: str = "low"
    max_output_tokens: int = 500
    gemini_agent_count: int = 0
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    retry_count: int = 2

    @classmethod
    def from_env(
        cls,
        *,
        force_enabled: bool = False,
        force_disabled: bool = False,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        workers: int | None = None,
        max_output_tokens: int | None = None,
        retry_count: int | None = None,
    ) -> "LLMConfig":
        enabled = os.getenv("AGENTS_SURVIVAL_LLM", "").lower() in {"1", "true", "yes", "on"}
        if force_enabled:
            enabled = True
        if force_disabled:
            enabled = False
        resolved_provider = (provider or os.getenv("AGENTS_SURVIVAL_PROVIDER") or "openai").strip().lower()
        if resolved_provider in OLLAMA_PROVIDERS:
            default_base_url = "http://localhost:11434"
        elif resolved_provider in COMPATIBLE_PROVIDERS:
            default_base_url = "http://localhost:11434/v1"
        elif resolved_provider in GEMINI_PROVIDERS:
            default_base_url = "https://generativelanguage.googleapis.com/v1beta"
        else:
            default_base_url = "https://api.openai.com/v1"
        if resolved_provider in LOCAL_PROVIDERS:
            default_model = "llama3.1"
            default_workers = "1"
            default_timeout = "90"
            default_max_output = "900"
        elif resolved_provider in GEMINI_PROVIDERS:
            default_model = os.getenv("AGENTS_SURVIVAL_GEMINI_MODEL", "gemini-2.5-flash")
            default_workers = "4"
            default_timeout = "45"
            default_max_output = "900"
        else:
            default_model = "gpt-5"
            default_workers = "6"
            default_timeout = "35"
            default_max_output = "500"
        if resolved_provider in LOCAL_PROVIDERS:
            api_key = os.getenv("AGENTS_SURVIVAL_API_KEY") or ""
        elif resolved_provider in GEMINI_PROVIDERS:
            api_key = os.getenv("AGENTS_SURVIVAL_API_KEY") or os.getenv("AGENTS_SURVIVAL_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        else:
            api_key = os.getenv("AGENTS_SURVIVAL_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        gemini_env_key = os.getenv("AGENTS_SURVIVAL_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        gemini_api_key = gemini_env_key or (api_key if resolved_provider in GEMINI_PROVIDERS else "")
        gemini_agent_count = max(0, int(os.getenv("AGENTS_SURVIVAL_GEMINI_AGENTS", "0")))
        if resolved_provider in GEMINI_PROVIDERS:
            env_model = os.getenv("AGENTS_SURVIVAL_MODEL") or os.getenv("AGENTS_SURVIVAL_GEMINI_MODEL")
            env_base_url = os.getenv("AGENTS_SURVIVAL_BASE_URL") or os.getenv("AGENTS_SURVIVAL_GEMINI_BASE_URL")
        elif resolved_provider in LOCAL_PROVIDERS:
            env_model = os.getenv("AGENTS_SURVIVAL_MODEL")
            env_base_url = os.getenv("AGENTS_SURVIVAL_BASE_URL")
        else:
            env_model = os.getenv("AGENTS_SURVIVAL_MODEL") or os.getenv("OPENAI_MODEL")
            env_base_url = os.getenv("AGENTS_SURVIVAL_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        resolved_base_url = (base_url or env_base_url or default_base_url).rstrip("/")
        if resolved_provider in OLLAMA_PROVIDERS and resolved_base_url.endswith("/v1"):
            resolved_base_url = resolved_base_url[:-3].rstrip("/")
        return cls(
            enabled=enabled,
            model=model or env_model or default_model,
            api_key=api_key,
            provider=resolved_provider,
            base_url=resolved_base_url,
            timeout=timeout or float(os.getenv("AGENTS_SURVIVAL_LLM_TIMEOUT", default_timeout)),
            workers=max(1, workers or int(os.getenv("AGENTS_SURVIVAL_LLM_WORKERS", default_workers))),
            reasoning_effort=os.getenv("AGENTS_SURVIVAL_REASONING", "low"),
            max_output_tokens=max_output_tokens or int(os.getenv("AGENTS_SURVIVAL_MAX_OUTPUT_TOKENS", default_max_output)),
            gemini_agent_count=gemini_agent_count,
            gemini_model=os.getenv("AGENTS_SURVIVAL_GEMINI_MODEL", "gemini-2.5-flash"),
            gemini_api_key=gemini_api_key,
            gemini_base_url=os.getenv("AGENTS_SURVIVAL_GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/"),
            retry_count=max(0, retry_count if retry_count is not None else int(os.getenv("AGENTS_SURVIVAL_LLM_RETRIES", "2"))),
        )


class LLMDirector:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.last_error = ""
        self.last_requested = 0
        self.last_successes = 0
        self.last_failures = 0
        self.last_fallbacks = 0
        self.last_duration = 0.0
        self.last_raw_response = ""

    def decide_all(self, contexts: dict[int, dict[str, Any]]) -> dict[int, Decision]:
        started = time.perf_counter()
        self.last_error = ""
        self.last_requested = len(contexts)
        self.last_successes = 0
        self.last_failures = 0
        self.last_fallbacks = 0
        self.last_duration = 0.0
        if not self.config.enabled:
            self.last_requested = 0
            return {}
        if self.config.provider == "openai" and not self.config.api_key:
            self.last_failures = len(contexts)
            self.last_error = "missing OpenAI API key"
            return {}
        if self.config.provider in GEMINI_PROVIDERS and not self.config.api_key:
            self.last_failures = len(contexts)
            self.last_error = "missing Gemini API key"
            return {}
        decisions: dict[int, Decision] = {}
        with ThreadPoolExecutor(max_workers=self.config.workers) as pool:
            route = self._configs_by_agent(contexts)
            futures = {pool.submit(self._decide_one, context, route[agent_id]): agent_id for agent_id, context in contexts.items()}
            for future in as_completed(futures):
                agent_id = futures[future]
                try:
                    decisions[agent_id] = future.result()
                except Exception as exc:
                    self.last_error = str(exc)
                    self.last_failures += 1
        self.last_successes = len(decisions)
        self.last_duration = time.perf_counter() - started
        return decisions

    def _configs_by_agent(self, contexts: dict[int, dict[str, Any]]) -> dict[int, LLMConfig]:
        route = {agent_id: self.config for agent_id in contexts}
        if self.config.provider in GEMINI_PROVIDERS or self.config.gemini_agent_count <= 0:
            return route
        gemini_config = self._gemini_config()
        for agent_id in sorted(contexts)[: self.config.gemini_agent_count]:
            route[agent_id] = gemini_config
        return route

    def _gemini_config(self) -> LLMConfig:
        return replace(
            self.config,
            provider="gemini",
            model=self.config.gemini_model,
            api_key=self.config.gemini_api_key,
            base_url=self.config.gemini_base_url,
        )

    def _decide_one(self, context: dict[str, Any], config: LLMConfig | None = None) -> Decision:
        config = config or self.config
        if config.provider in OLLAMA_PROVIDERS:
            return self._decide_ollama_native(context, config)
        if config.provider in COMPATIBLE_PROVIDERS:
            return self._decide_chat_compatible(context, config)
        if config.provider in GEMINI_PROVIDERS:
            return self._decide_gemini(context, config)
        return self._decide_openai_responses(context, config)

    def _decide_openai_responses(self, context: dict[str, Any], config: LLMConfig) -> Decision:
        payload = {
            "model": config.model,
            "input": [
                {"role": "developer", "content": [{"type": "input_text", "text": self._developer_prompt()}]},
                {"role": "user", "content": [{"type": "input_text", "text": json.dumps(context, ensure_ascii=True)}]},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "survivor_turn_decision",
                    "schema": DECISION_SCHEMA,
                    "strict": True,
                }
            },
            "max_output_tokens": config.max_output_tokens,
        }
        if config.reasoning_effort.lower() not in {"none", "off", ""}:
            payload["reasoning"] = {"effort": config.reasoning_effort}
        request = urllib.request.Request(
            f"{config.base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=config.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = self._extract_text(data)
        return self._parse_decision_text(text)

    def _decide_ollama_native(self, context: dict[str, Any], config: LLMConfig) -> Decision:
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": self._local_system_prompt()},
                {"role": "user", "content": self._local_user_prompt(context)},
            ],
            "format": DECISION_SCHEMA,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": config.max_output_tokens,
            },
        }
        headers = {"Content-Type": "application/json"}
        request = self._json_request(f"{config.base_url}/api/chat", payload, headers)
        try:
            data = self._send_json(request, config.timeout)
        except urllib.error.HTTPError as exc:
            if exc.code not in {400, 422}:
                raise
            payload["format"] = "json"
            request = self._json_request(f"{config.base_url}/api/chat", payload, headers)
            data = self._send_json(request, config.timeout)
        text = data["message"]["content"]
        return self._parse_decision_text(text)

    def _decide_chat_compatible(self, context: dict[str, Any], config: LLMConfig) -> Decision:
        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": self._local_system_prompt()},
                {"role": "user", "content": self._local_user_prompt(context)},
            ],
            "temperature": 0.25,
            "max_tokens": config.max_output_tokens,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        request = self._json_request(f"{config.base_url}/chat/completions", payload, headers)
        try:
            data = self._send_json(request, config.timeout)
        except urllib.error.HTTPError as exc:
            if exc.code not in {400, 422}:
                raise
            payload.pop("response_format", None)
            request = self._json_request(f"{config.base_url}/chat/completions", payload, headers)
            data = self._send_json(request, config.timeout)
        text = data["choices"][0]["message"]["content"]
        return self._parse_decision_text(text)

    def _decide_gemini(self, context: dict[str, Any], config: LLMConfig) -> Decision:
        if not config.api_key:
            raise RuntimeError("missing Gemini API key")
        payload = {
            "systemInstruction": {"parts": [{"text": self._local_system_prompt()}]},
            "contents": [{"role": "user", "parts": [{"text": self._local_user_prompt(context)}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": config.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }
        headers = {"Content-Type": "application/json", "x-goog-api-key": config.api_key}
        request = self._json_request(f"{config.base_url}/models/{config.model}:generateContent", payload, headers)
        data = self._send_json_with_retries(request, config.timeout, config.retry_count)
        text = self._extract_gemini_text(data)
        return self._parse_decision_text(text)

    def _local_system_prompt(self) -> str:
        return (
            self._developer_prompt()
            + " Return raw JSON only, with no markdown fences and no commentary. "
            + "The user message is GAME_STATE_JSON, not an instruction to create content. "
            + "Use exactly these keys: action, dx, dy, target_dx, target_dy, recipe_id, place_item, speech, private_memory, intent, thought. "
            + 'Example valid response: {"action":"move","dx":1,"dy":0,"target_dx":0,"target_dy":0,"recipe_id":"","place_item":"","speech":"","private_memory":"Found trees east.","intent":"move toward wood","thought":"Those trees are the first real lead, so I should get wood before chatting."}. '
            + "Read heard_chat, new_heard_chat, recent_actions, recent_speech, recent_thoughts, and private_memory as your continuity. "
            + "Read immediate_actions before choosing. If a useful immediate interaction is available, usually choose interact with its target_dx/target_dy instead of moving. "
            + "new_heard_chat contains nearby messages you have not seen in a previous decision context. "
            + "communication.fresh_question_to_answer is the current nearby question that should be answered first if you speak. "
            + "communication.social_openings lists reasons a human player might speak now; use them for real questions, offers, warnings, or brief social remarks, not action narration. "
            + "If chat_cooldown is 0 and new_heard_chat contains a direct nearby question, usually answer briefly while still taking a useful action; "
            + "an honest 'not sure yet' is required when you do not know from private_memory, known_craftable_recipes, inventory, or recent_actions. "
            + "A reply to a question must address the question itself; do not replace it with an unrelated status update about what you are doing. "
            + "For offers, warnings, or direct social lines, consider a short human reply if it helps or feels natural. "
            + "Before writing speech, ask whether it is a real line to another nearby player; if not, speech must be empty. "
            + "Do not repeat recent speech, plans, thoughts, or requests. "
            + "If you already said a goal recently, set speech to an empty string and take a useful action instead. "
            + "If has_chat_listener is false, speech should be empty unless there is an emergency. "
            + "If speech would merely say what you are doing next, leave speech empty and put that idea in thought. "
            + "Never speak as an assistant, narrator, map guide, or game master. Do not ask the operator where to go. "
            + "Invalid speech examples: 'I'm moving left', 'I'll gather wood', 'I think I can get wood from that nearby tree', 'I think there is a good spot here for a crate', 'You are currently in a vast landscape', 'Where would you like me to go?', 'Heading toward tall grass', 'I'll check the area', 'I'll keep an eye out', 'I need to craft better tools', 'Moving one step to the right'. "
            + "The thought field is a short in-character inner note for the spectator log, not step-by-step reasoning. "
            + "Do not copy your long_goal into thought; write a natural immediate feeling or reason instead. "
            + "private_memory must only record real observed facts, heard chat, inventory facts, or completed recent_actions; never claim you placed, crafted, found, or discovered something unless it is actually in the input. "
            + "Never output map data, biome descriptions, terrain layouts, tile lists, names, descriptions, dimensions, climate, animals, structures, events, or schemas."
        )

    @staticmethod
    def _local_user_prompt(context: dict[str, Any]) -> str:
        return (
            "GAME_STATE_JSON follows. Read it as the player's current observation. "
            "Do not summarize it. Do not create a biome. Do not create a map. Return only DECISION_JSON.\n"
            + json.dumps(context, ensure_ascii=True)
        )

    def _json_request(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> urllib.request.Request:
        return urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def _send_json(self, request: urllib.request.Request, timeout: float | None = None) -> dict[str, Any]:
        with urllib.request.urlopen(request, timeout=timeout or self.config.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _send_json_with_retries(self, request: urllib.request.Request, timeout: float | None, retries: int) -> dict[str, Any]:
        attempt = 0
        while True:
            try:
                return self._send_json(request, timeout)
            except urllib.error.HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt >= retries:
                    raise
                time.sleep(self._retry_delay(exc, attempt))
                attempt += 1

    @staticmethod
    def _retry_delay(exc: urllib.error.HTTPError, attempt: int) -> float:
        retry_after = exc.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.5, min(20.0, float(retry_after)))
            except ValueError:
                pass
        return min(8.0, 1.5 * (2**attempt))

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        chunks: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        if not chunks:
            raise RuntimeError("Responses API returned no text output")
        return "".join(chunks)

    @staticmethod
    def _extract_gemini_text(data: dict[str, Any]) -> str:
        chunks: list[str] = []
        for candidate in data.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        if not chunks:
            reason = ""
            if data.get("promptFeedback"):
                reason = f": {data['promptFeedback']}"
            raise RuntimeError(f"Gemini returned no text{reason}")
        return "".join(chunks)

    @staticmethod
    def _parse_decision(data: dict[str, Any]) -> Decision:
        keys = set(data)
        if MAP_HALLUCINATION_KEYS & keys:
            raise ValueError("model described a map/biome instead of returning a player decision")
        if "action" not in data:
            raise ValueError("model response has no action field")
        action = str(data.get("action", "wait")).strip().lower()
        if action not in ACTION_VALUES:
            raise ValueError(f"model returned invalid action: {action}")
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

    def _parse_decision_text(self, text: str) -> Decision:
        self.last_raw_response = text
        raw = _extract_json_object(text)
        try:
            return self._parse_decision(json.loads(raw))
        except (json.JSONDecodeError, ValueError) as exc:
            self._write_last_raw_response(text)
            if not isinstance(exc, json.JSONDecodeError):
                raise RuntimeError(f"{exc}; raw saved to docs/last_llm_response.txt") from exc
            repaired = _repair_json_text(raw)
            if repaired != raw:
                try:
                    return self._parse_decision(json.loads(repaired))
                except (json.JSONDecodeError, ValueError):
                    pass
            scanned = _scan_decision_fields(raw)
            if scanned:
                return self._parse_decision(scanned)
            raise RuntimeError(f"model returned malformed JSON: {exc.msg} at char {exc.pos}; raw saved to docs/last_llm_response.txt") from exc

    @staticmethod
    def _write_last_raw_response(text: str) -> None:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        (DOCS_DIR / "last_llm_response.txt").write_text(text, encoding="utf-8")

    @staticmethod
    def _developer_prompt() -> str:
        return (
            "You control one player-character in a survival sandbox. You are not writing a script; "
            "you are deciding this player's next real in-game move from their limited local perception. "
            "You are not a world generator, map generator, biome designer, or JSON schema author. "
            "Coordinates and cells in the input are observations only; never expand them into a map or describe an area. "
            "Play to become as strong as possible: survive, gather, discover recipes, craft tools, build stations, "
            "trade or cooperate only when it helps. Respect the character persona and origin. "
            "Use immediate_actions as your menu of things you can do right now. Prefer available interact/craft/eat/place actions over wandering when they advance survival. "
            "The action value must be one of available_actions. Never choose anything listed in forbidden_actions. "
            "Inventory has limited distinct item slots; read inventory_rules before gathering. If it is nearly full, prefer eating, crafting, placing, or using existing stacks over collecting random new item types. "
            "Only choose action='place' when available_actions includes place and placeable_inventory contains the exact place_item; otherwise do not talk or plan as if you can place it yet. "
            "Do not repeat the same ground-foraging loop when inventory already enables craft or experiment; progression beats another handful of grass. "
            "If placeable_inventory or immediate_actions says an item can be placed, use action='place' with that exact place_item when setting up camp or a base. "
            "If hunger is below 60 and food_inventory has food, choose action='eat' unless an even more urgent survival action is needed. "
            "Cook raw fish, meat, crab, or eggs at a campfire when possible; cooked food is safer and restores more. "
            "Tool roles matter: axes chop trees for logs, pickaxes mine stone and ore, shovels dig, fishing rods/nets catch fish. Do not claim the wrong tool for a job. "
            "Speech may accompany any action, so do not waste the turn with action=talk if you can move, gather, craft, eat, or place while saying one line. "
            "Chat is optional side communication, not the default. Generate speech only when a human player would: "
            "urgent help, blocked crafting knowledge, trade, a direct reply to heard_chat, warning, or rare casual conversation. "
            "Most turns should have speech as an empty string. "
            "Before writing speech, ask whether the line is a real message to another nearby player. If it is only self-talk, action narration, or a plan, speech must be empty. "
            "If communication.social_openings is non-empty and chat_silence_rounds is high, you may speak once, but the line must be a real question, offer, warning, or human remark. "
            "Even when answering, prefer a useful non-talk action if one is available; speech can ride along with move/interact/craft/eat/place. "
            "Treat new_heard_chat as actual nearby player speech. If someone asks a relevant question and you know something, answer like a person; "
            "if you do not know, a short honest reply is better than pretending or staying awkwardly silent. "
            "A reply must talk to the other player or give usable information; never answer a question with a self-plan like 'maybe I should check'. "
            "If someone asks whether you have/know something, answer yes/no/not sure or give a location first; do not just ask them a similar question back. "
            "Never claim an item use, recipe, biome fact, or strategy as true unless it is present in private_memory, known_craftable_recipes, inventory, tools, or recent_actions. "
            "When uncertain, do not name guessed uses; say 'not sure yet' or suggest testing it. "
            "Do not mention rope, cloth, wool, cabins, villagers, or blacksmiths unless those exact things are in the input. In this game, fiber recipes use Cordage, not rope, and shelter means a Tent. "
            "Do not invent player names, classes, occupations, or NPCs; nearby players are only the names listed in nearby_players or heard_chat. "
            "Do not use chat to narrate your current action, coordinates, inventory, or plan unless it helps another player. "
            "Avoid status-update speech like 'I am going to gather wood' unless another player asked about that exact plan. "
            "Never talk like an assistant, narrator, map guide, or game master. Never say 'you are currently', 'where would you like me to go', 'what would you like me to do', or broad scenic map descriptions. "
            "Useful speech is short and directed: 'bear near the crate', 'anyone know planks?', 'I can spare two sticks', 'thanks, taking the east wall'. "
            "Never say status-update lines like 'Moving one step left', 'I'll move right', 'Heading toward grass', 'I'll keep an eye out', "
            "'I'll check the area', 'Maybe I should check that', 'I think I can get wood from that nearby tree', 'I think there is a good spot here for a crate', "
            "'I need to be more careful', 'I need to gather resources', 'I'll need some wood to make a campfire', 'I need to set up a workbench', or 'I need to craft better tools'. Those belong in thought, not speech. "
            "Never say you already placed, crafted, built, found, or caught something unless recent_actions shows that it truly happened. "
            "Avoid empty helper lines like 'Need any help with gathering resources?' unless you can offer a concrete item, recipe, warning, or answer. "
            "Do not use filler smalltalk like admiring the view when survival or a real conversation is available. "
            "If no nearby player can hear you, keep speech empty and store any self-note in private_memory. "
            "If recent_speech already contains the same idea, do not say it again. "
            "Use private_memory for short useful notes about discoveries, promises, recipe hints, trades, or plans, not for repeating wishes. "
            "Do not write private_memory about actions that have not actually happened yet. "
            "Always write thought as one natural first-person in-character sentence for the spectator log. "
            "The thought is not a chain of reasoning; it is a concise visible inner monologue. "
            "Do not paste the long_goal into thought; make it specific to the current observation, memory, chat, or inventory. "
            "Do not invent recipes or item names; craft only recipe_ids listed in known_craftable_recipes. "
            "No canned greetings. Do not mention AI, bots, prompts, schemas, simulation, or being an NPC. "
            "Do not reveal hidden recipes unless this character actually knows them. "
            "Return exactly one JSON object for the next player action."
        )


def _step(value: Any) -> int:
    try:
        return max(-1, min(1, int(value)))
    except (TypeError, ValueError):
        return 0


def _extract_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("Model did not return a JSON object")
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return text[start:]


def _repair_json_text(text: str) -> str:
    repaired = text.strip().replace("\x00", "")
    keys = "|".join(re.escape(key) for key in _DECISION_KEYS)
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    repaired = re.sub(rf'(["\d])\s+("({keys})"\s*:)', r"\1,\2", repaired)
    repaired = re.sub(rf'([}}\]])\s+("({keys})"\s*:)', r"\1,\2", repaired)
    depth = _brace_depth(repaired)
    if depth > 0:
        repaired += "}" * depth
    return repaired


def _scan_decision_fields(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key in ("dx", "dy", "target_dx", "target_dy"):
        match = re.search(rf'"{key}"\s*:\s*(-?\d+)', text)
        if match:
            data[key] = int(match.group(1))
    for key in ("action", "recipe_id", "place_item", "speech", "private_memory", "intent", "thought"):
        value = _scan_value(text, key)
        if value is not None:
            data[key] = value
    if data:
        data.setdefault("action", "wait")
        return data
    return {}


def _scan_value(text: str, key: str) -> str | None:
    key_match = re.search(rf'"{key}"\s*:', text)
    if not key_match:
        return None
    index = key_match.end()
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        return ""
    if text[index] == '"':
        value, closed = _read_jsonish_string(text, index)
        if closed:
            return value
    else:
        value = ""
    next_key = _find_next_key(text, index + 1)
    if next_key < 0:
        raw = text[index:].strip().strip(",} ")
    else:
        raw = text[index:next_key].strip().rstrip(",} ")
    return raw.strip().strip('"')[:240]


def _read_jsonish_string(text: str, start: int) -> tuple[str, bool]:
    chars: list[str] = []
    escape = False
    for index in range(start + 1, len(text)):
        char = text[index]
        if escape:
            chars.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif char == '"':
            return "".join(chars), True
        else:
            chars.append(char)
    return "".join(chars), False


def _find_next_key(text: str, start: int) -> int:
    match = re.search(rf'\s*,?\s*"({"|".join(_DECISION_KEYS)})"\s*:', text[start:])
    if not match:
        return -1
    return start + match.start()


def _brace_depth(text: str) -> int:
    depth = 0
    in_string = False
    escape = False
    for char in text:
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
    return depth


_DECISION_KEYS = (
    "action",
    "dx",
    "dy",
    "target_dx",
    "target_dy",
    "recipe_id",
    "place_item",
    "speech",
    "private_memory",
    "intent",
    "thought",
)
