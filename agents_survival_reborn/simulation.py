from __future__ import annotations

import random
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from .agent import Agent, ChatMessage, PERSONAS, clean_chat, clean_inner_text
from .constants import AGENT_COUNT, CENTER_AND_NEIGHBORS, CHAT_HISTORY_LIMIT, CHAT_RADIUS, DEFAULT_SEED, DIRECTIONS, SIGHT_RADIUS, WORLD_HEIGHT, WORLD_WIDTH
from .data import FEATURES, ITEMS, PLACEABLE_ITEMS, RECIPES_BY_ID, TERRAINS, RecipeDef, item_name
from .inventory import craft, craftable_known, discoverable, has_ingredients, has_output_space
from .journal import RunLogger
from .llm import Decision, LLMConfig, LLMDirector
from .world import World


STATUS_UPDATE_PATTERNS = (
    r"\b(i'?ll|i will|i'?m|i am|im)\s+(move|moving|go|going|gather|gathering|craft|crafting|make|making|build|building|place|placing|set up|setup|collect|collecting|chop|chopping|cut|cutting|plant|planting)\b",
    r"\b(setting up|let'?s set up|lets set up|let'?s move|lets move)\b",
    r"\bi think i can find some useful items nearby\b",
    r"\b(i need|i have|i want)\s+to\s+(move|go|gather|craft|make|build|place|set up|setup|collect|get|chop|cut)\b",
    r"\bi'?ll need\b.*\b(wood|stick|log|stone|flint|campfire|workbench|kiln|tent|bedroll|crate|tool|weapon|food)\b",
    r"\bi need\b.*\b(before i can|to make|to craft|to build|to place)\b",
    r"\b(moving|gathering|crafting|building|placing|collecting|chopping|cutting)\b",
    r"\bmove\s+(one step|a bit|to the|right|left|up|down)\b",
    r"\b(head|heading|headed)\s+(toward|towards|to|for)\b",
    r"\b(head|heading|headed)\s+(north|south|east|west|left|right|up|down)\b",
    r"\b(i'?ll|i will|i'?m|i am|im)\s+(look|looking|search|searching|explore|exploring|scout|scouting)\b",
    r"\b(i'?ll|i will|i'?m|i am|im)?\s*(check|checking)\s+(the\s+)?(area|surroundings)\b",
    r"\b(i'?ll|i will)\s+check\b.*\b(nearby|useful|items?|resources?)\b",
    r"\b(i'?ll|i will)\s+check\s+if\b",
    r"\bnearby player\b",
    r"\b(i'?ll|i will)\s+keep\s+(moving|exploring|looking|searching|scouting)\b",
    r"\b(i'?ll|i will)\s+(head|stay|follow)\b",
    r"\blet'?s\s+(move|explore|check|search|look|find|gather|start)\b",
    r"\b(i'?ll|i will|i'?m|i am|im)\s+keep\s+an\s+eye\s+out\b",
    r"\b(keep|keeping)\s+(my\s+)?(eyes?|eye)\s+(out|peeled)\b",
    r"\b(i should|i need to)\s+(explore|scout|look|search|find|keep)\b",
    r"\b(maybe\s+)?i should\s+check\b",
    r"\bi think i'?ll\s+check\b",
    r"\bmaybe there'?s something useful\b",
    r"\bbefore i can\s+(craft|start|make|build)\b",
    r"\bbefore i can\s+place\b",
    r"\bset up my\s+(campfire|workbench|kiln|base)\b",
    r"\bwhat would you like to do\b",
    r"\bcenter of the map\b",
    r"\bcenter of (this|the) area\b",
    r"\bi'?m currently at\b.*\bcenter\b",
    r"\bi'?m standing in the middle\b",
    r"\bthe air is fresh\b",
    r"\bsun shines\b",
    r"\bvast grassland\b",
)

DIALOGUE_MARKERS = {
    "anyone",
    "someone",
    "somebody",
    "you",
    "your",
    "we",
    "us",
    "trade",
    "swap",
    "spare",
    "help",
    "know",
    "where",
    "what",
    "how",
    "got",
    "have",
    "need?",
    "can",
    "could",
    "want",
    "take",
    "thanks",
    "thank",
    "sure",
    "tested",
    "recipe",
    "worked",
    "watch",
    "careful",
    "danger",
    "warning",
    "found",
    "saw",
    "there's",
    "there is",
    "north",
    "south",
    "east",
    "west",
}

UNSUPPORTED_SPEECH_TERMS = {
    "rope",
    "cloth",
    "wool",
    "cabin",
    "campsite",
    "villager",
    "blacksmith",
    "woodcutter",
}


@dataclass
class RoundEvent:
    agent: str
    text: str
    kind: str


class Simulation:
    def __init__(
        self,
        *,
        seed: int = DEFAULT_SEED,
        width: int = WORLD_WIDTH,
        height: int = WORLD_HEIGHT,
        agent_count: int = AGENT_COUNT,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self.seed = seed
        self.rng = random.Random(seed + 440)
        self.world = World(width, height, seed)
        self.llm = LLMDirector(llm_config or LLMConfig.from_env())
        self.round_index = 0
        self.round_thinking = False
        self.agents: list[Agent] = []
        self.chat: list[ChatMessage] = []
        self.round_events: list[RoundEvent] = []
        self.logger = RunLogger(seed=seed, width=width, height=height, agent_count=agent_count)
        self._spawn(agent_count)
        self.logger.write_world(self._world_replay_payload())

    def advance_round(self) -> None:
        contexts = self.prepare_round_contexts()
        decisions = self.llm.decide_all(contexts)
        self.apply_round_decisions(decisions)

    def prepare_round_contexts(self) -> dict[int, dict[str, Any]]:
        for agent in self.agents:
            agent.mark_animation_start()
            agent.tick_needs()
        return {agent.agent_id: self._context(agent) for agent in self.agents if agent.health > 0}

    def apply_round_decisions(self, decisions: dict[int, Decision]) -> None:
        self.round_events = []
        fallback_count = 0
        occupied_snapshot = {(agent.x, agent.y): agent.agent_id for agent in self.agents if agent.health > 0}
        for agent in self.agents:
            if agent.health <= 0:
                continue
            from_llm = agent.agent_id in decisions
            decision = decisions.get(agent.agent_id) or self._fallback_decision(agent)
            if not from_llm:
                fallback_count += 1
            requested_action = decision.action
            speech = clean_chat(decision.speech)
            has_listener = self._has_chat_listener(agent)
            fresh_heard_chat = self._has_fresh_heard_chat(agent)
            fresh_question = self._fresh_question_entry(agent, list(agent.heard_messages))
            repeated_speech = agent.recently_said_similar(speech) if speech else False
            answers_fresh_question = bool(speech and fresh_question and self._speech_addresses_question(speech, fresh_question["text"]))
            repeated_global_speech = bool(speech and (not answers_fresh_question or self._is_generic_help_offer(speech)) and self._recent_global_chat_similar(speech))
            speech_quality_block = self._speech_quality_block_reason(agent, speech, fresh_question, fresh_heard_chat)
            speech_allowed = bool(speech and has_listener and not repeated_speech and not repeated_global_speech and not speech_quality_block and (agent.chat_cooldown <= 0 or fresh_heard_chat))
            speech_blocked_reason = ""
            if speech and not speech_allowed:
                if not has_listener:
                    speech_blocked_reason = "no nearby listener"
                elif repeated_speech:
                    speech_blocked_reason = "repeated recent speech"
                elif repeated_global_speech:
                    speech_blocked_reason = "repeated recent chat idea"
                elif speech_quality_block:
                    speech_blocked_reason = speech_quality_block
                elif agent.chat_cooldown > 0 and not fresh_heard_chat:
                    speech_blocked_reason = f"chat cooldown {agent.chat_cooldown}"
                else:
                    speech_blocked_reason = "not useful now"
            if decision.intent:
                agent.last_intent = decision.intent if from_llm else f"fallback: {decision.intent}"
            decision, adjustment_reason = self._adjust_low_value_decision(agent, decision)
            if decision.action == "talk" and not speech_allowed:
                decision = Decision("wait", private_memory=decision.private_memory, intent="skip blocked or nonessential chat", thought=decision.thought)
            thought = self._polish_thought(agent, clean_inner_text(decision.thought) or self._fallback_thought(agent, decision), decision)
            agent.record_thought(self.round_index, thought)
            event = self._apply(agent, decision, occupied_snapshot)
            private_memory_delta = self._validated_private_memory(agent, decision, event, decision.private_memory)
            if private_memory_delta:
                agent.remember(private_memory_delta)
            post_event_speech_block = self._speech_result_block_reason(speech, event)
            if speech_allowed and post_event_speech_block:
                speech_allowed = False
                speech_blocked_reason = post_event_speech_block
            self.round_events.append(event)
            agent.record_action(self.round_index, event.text, agent.last_intent)
            self.logger.log_thought(
                {
                    "round": self.round_index,
                    "agent": agent.name,
                    "persona": agent.persona.archetype,
                    "position": [agent.x, agent.y],
                    "from_llm": from_llm,
                    "thought": thought,
                    "intent": agent.last_intent,
                    "requested_action": requested_action,
                    "applied_action": decision.action,
                    "decision_adjustment": adjustment_reason,
                    "result": event.text,
                    "speech": speech,
                    "speech_allowed": speech_allowed,
                    "speech_blocked_reason": speech_blocked_reason,
                    "fresh_question": fresh_question,
                    "private_memory_delta": private_memory_delta,
                    "recent_heard_chat": [self._chat_context_entry(agent, msg) for msg in list(agent.heard_messages)[-4:]],
                }
            )
            self.logger.log_turn(
                {
                    "round": self.round_index,
                    "agent": agent.name,
                    "kind": event.kind,
                    "result": event.text,
                    "intent": agent.last_intent,
                    "thought": thought,
                    "position": [agent.x, agent.y],
                    "inventory": {item: count for item, count in sorted(agent.inventory.items()) if count > 0},
                }
            )
            if speech_allowed:
                self._broadcast(agent, speech)
                agent.chat_cooldown = self.rng.randint(5, 14)
        self.world.advance_wildlife({(agent.x, agent.y) for agent in self.agents if agent.health > 0})
        self.logger.log_replay(self._replay_payload())
        self.round_index += 1
        self.chat = self.chat[-CHAT_HISTORY_LIMIT:]
        self.llm.last_fallbacks = fallback_count

    def _adjust_low_value_decision(self, agent: Agent, decision: Decision) -> tuple[Decision, str]:
        if decision.action == "craft":
            recipe = RECIPES_BY_ID.get(decision.recipe_id)
            if not recipe or recipe.recipe_id not in agent.known_recipes or not has_ingredients(agent.inventory, recipe):
                return self._productive_replacement(agent, decision, "invalid craft replaced")
            return decision, ""
        if decision.action == "place":
            if decision.place_item not in PLACEABLE_ITEMS or agent.inventory.get(decision.place_item, 0) <= 0:
                return self._productive_replacement(agent, decision, "invalid place replaced")
            return decision, ""
        if decision.action in {"move", "interact", "talk", "experiment", "wait"} and self._looks_like_unsupported_world_plan(decision):
            return self._productive_replacement(agent, decision, "unsupported world plan replaced")
        if decision.action in {"move", "interact", "talk", "wait"}:
            urgent = self._urgent_progression_decision(agent, decision)
            if urgent:
                agent.last_intent = urgent.intent
                return urgent, "urgent progression opportunity used"
        if decision.action in {"move", "interact", "talk"} and self._looks_like_invalid_place_plan(agent, decision):
            return self._productive_replacement(agent, decision, "imagined place plan replaced")
        if decision.action in {"move", "interact", "talk"} and self._should_break_gather_loop(agent):
            return self._productive_replacement(agent, decision, "repeated gathering converted to progression")
        if decision.action == "talk":
            option = self._best_immediate_interaction(agent)
            if not option:
                return decision, ""
            target = str(option["target"]).lower()
            adjusted = Decision(
                action="interact",
                target_dx=int(option["target_dx"]),
                target_dy=int(option["target_dy"]),
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"keep talking while checking immediate {target}",
                thought=f"I can keep the conversation going without wasting the chance to check {option['target']}.",
            )
            agent.last_intent = adjusted.intent
            return adjusted, "talk converted to interact while speaking"
        if decision.action != "move" or not self._looks_like_vague_exploration(decision):
            return decision, ""
        progress_move = self._progress_exploration_move(agent, decision)
        if progress_move:
            agent.last_intent = progress_move.intent
            return progress_move, "vague move redirected toward progression target"
        option = self._best_immediate_interaction(agent)
        if not option:
            return decision, ""
        target = str(option["target"]).lower()
        adjusted = Decision(
            action="interact",
            target_dx=int(option["target_dx"]),
            target_dy=int(option["target_dy"]),
            speech=decision.speech,
            private_memory=decision.private_memory,
            intent=f"check immediate {target} instead of wandering",
            thought=f"{option['target']} is close enough to check now; walking past it would be sloppy.",
        )
        agent.last_intent = adjusted.intent
        return adjusted, "vague move converted to immediate interact"

    def _progress_exploration_move(self, agent: Agent, decision: Decision) -> Decision | None:
        if not self._needs_progress_exploration(agent):
            return None
        target = self._best_visible_progress_target(agent)
        if not target:
            return None
        dx = _sign(target[0] - agent.x)
        dy = _sign(target[1] - agent.y)
        if dx == 0 and dy == 0:
            return None
        if max(abs(target[0] - agent.x), abs(target[1] - agent.y)) <= 1:
            label = target[2]
            return Decision(
                action="interact",
                target_dx=target[0] - agent.x,
                target_dy=target[1] - agent.y,
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"work the nearby {label}",
                thought=f"{label} is right here; I should work it instead of walking past it.",
            )
        nx, ny = agent.x + dx, agent.y + dy
        if not self.world.can_enter(agent, nx, ny):
            for alt_dx, alt_dy in ((dx, 0), (0, dy)):
                if alt_dx == 0 and alt_dy == 0:
                    continue
                ax, ay = agent.x + alt_dx, agent.y + alt_dy
                if self.world.can_enter(agent, ax, ay):
                    dx, dy = alt_dx, alt_dy
                    break
            else:
                return None
        label = target[2]
        return Decision(
            action="move",
            dx=dx,
            dy=dy,
            speech=decision.speech,
            private_memory=decision.private_memory,
            intent=f"move toward {label}",
            thought=f"I have enough basics for now; {label} is the next useful lead.",
        )

    @staticmethod
    def _needs_progress_exploration(agent: Agent) -> bool:
        has_basics = agent.inventory.get("cordage", 0) >= 1 or agent.inventory.get("grass_fiber", 0) >= 6
        has_sticks = agent.inventory.get("stick", 0) >= 3
        stone_like = agent.inventory.get("stone", 0) + agent.inventory.get("pebble", 0) // 3
        log_count = sum(agent.inventory.get(item_id, 0) for item_id in ("birch_log", "oak_log", "pine_log", "fruit_log"))
        has_axe = bool(agent.best_tool("axe", 1))
        has_pickaxe = bool(agent.best_tool("pickaxe", 1))
        has_tool_head = agent.inventory.get("pebble", 0) >= 2 or agent.inventory.get("stone", 0) >= 2 or agent.inventory.get("flint", 0) >= 1
        needs_stick_for_tool = has_tool_head and agent.inventory.get("cordage", 0) >= 1 and agent.inventory.get("stick", 0) <= 0
        needs_axe_material = not has_axe and (stone_like < 2 and agent.inventory.get("pebble", 0) < 2)
        needs_pickaxe_material = not has_pickaxe and not agent.inventory.get("flint", 0) and stone_like < 3
        needs_campfire_stone = agent.inventory.get("campfire", 0) <= 0 and stone_like < 5
        needs_workbench_wood = not has_axe and log_count <= 0 and agent.inventory.get("plank", 0) < 4
        needs_logs_with_axe = has_axe and log_count <= 0 and agent.inventory.get("plank", 0) < 4
        recent = " ".join(list(agent.recent_actions)[-5:]).lower()
        repeated_ground = recent.count("foraged ground cover") >= 2
        needs_progress_material = needs_stick_for_tool or needs_axe_material or needs_pickaxe_material or needs_campfire_stone or needs_workbench_wood or needs_logs_with_axe
        if needs_logs_with_axe:
            return True
        return has_basics and (needs_stick_for_tool or has_sticks or repeated_ground) and needs_progress_material

    def _best_visible_progress_target(self, agent: Agent) -> tuple[int, int, str] | None:
        candidates: list[tuple[int, int, int, str]] = []
        stone_like = agent.inventory.get("stone", 0) + agent.inventory.get("pebble", 0) // 3
        log_count = sum(agent.inventory.get(item_id, 0) for item_id in ("birch_log", "oak_log", "pine_log", "fruit_log"))
        has_axe = bool(agent.best_tool("axe", 1))
        has_tool_head = agent.inventory.get("pebble", 0) >= 2 or agent.inventory.get("stone", 0) >= 2 or agent.inventory.get("flint", 0) >= 1
        needs_stick = has_tool_head and agent.inventory.get("cordage", 0) >= 1 and agent.inventory.get("stick", 0) <= 0
        needs_logs_with_axe = has_axe and log_count <= 0 and agent.inventory.get("plank", 0) < 4
        needs_rock = not needs_logs_with_axe and (stone_like < 5 or (not agent.best_tool("pickaxe", 1) and not agent.inventory.get("flint", 0)))
        needs_wood = (has_axe and log_count <= 0 and agent.inventory.get("plank", 0) < 4) or (not has_axe and log_count <= 0)
        for dy in range(-SIGHT_RADIUS, SIGHT_RADIUS + 1):
            for dx in range(-SIGHT_RADIUS, SIGHT_RADIUS + 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = agent.x + dx, agent.y + dy
                if not self.world.in_bounds(x, y):
                    continue
                tile = self.world.tile(x, y)
                terrain = TERRAINS[tile.terrain]
                feature = FEATURES[tile.feature] if tile.feature else None
                label = ""
                priority = 99
                if feature and ("stone" in feature.tags or "rock" in feature.tags or "ore" in feature.tags):
                    priority = 8 if needs_logs_with_axe else 6 if needs_stick else 0
                    label = feature.name
                elif feature and "tree" in feature.tags:
                    priority = 0 if needs_logs_with_axe else 1 if needs_stick else 1 if needs_wood and not needs_rock else 5
                    label = feature.name
                elif "rock" in terrain.tags or "hill" in terrain.tags:
                    priority = 7 if needs_stick else 2 if needs_rock else 6
                    label = terrain.name
                elif "sand" in terrain.tags or "dry" in terrain.tags:
                    priority = 8 if needs_stick else 3 if needs_rock else 7
                    label = terrain.name
                elif "forest" in terrain.tags:
                    priority = 1 if needs_stick else 4 if needs_wood else 8
                    label = terrain.name
                elif "grass" in terrain.tags:
                    priority = 2 if needs_stick else 9
                    label = terrain.name
                if label:
                    candidates.append((priority, abs(dx) + abs(dy), x * 10000 + y, label))
        if not candidates:
            return None
        priority, _distance, packed, label = sorted(candidates)[0]
        x, y = divmod(packed, 10000)
        return x, y, label

    def _looks_like_invalid_place_plan(self, agent: Agent, decision: Decision) -> bool:
        text = f"{decision.intent} {decision.thought} {decision.speech} {decision.private_memory}".lower()
        if not any(marker in text for marker in ("place", "set up", "setup")):
            return False
        mentioned = [item_id for item_id in PLACEABLE_ITEMS if item_id.replace("_", " ") in text or item_name(item_id).lower() in text]
        if not mentioned:
            return False
        return all(agent.inventory.get(item_id, 0) <= 0 for item_id in mentioned)

    @staticmethod
    def _looks_like_unsupported_world_plan(decision: Decision) -> bool:
        text = f"{decision.intent} {decision.thought} {decision.speech} {decision.private_memory}".lower()
        unsupported_patterns = (
            r"\bplant(?:ing)?\s+(?:a|an|the|some)?\s*(?:birch|oak|pine|fruit\s*tree|tree)\b",
            r"\bgrow(?:ing)?\s+(?:a|an|the|some)?\s*(?:birch|oak|pine|fruit\s*tree|tree)\b",
        )
        return any(re.search(pattern, text) for pattern in unsupported_patterns)

    def _should_break_gather_loop(self, agent: Agent) -> bool:
        if craftable_known(agent, self.world) or discoverable(agent, self.world):
            recent = " ".join(list(agent.recent_actions)[-6:]).lower()
            repetitive_hits = sum(
                recent.count(marker)
                for marker in (
                    "foraged ground cover",
                    "gathered soil",
                    "scooped dry ground",
                    "searched the coast",
                    "gathered rock",
                )
            )
            if repetitive_hits >= 3:
                return True
            if agent.inventory.get("grass_fiber", 0) >= 6 and "cordage_from_fiber" not in agent.known_recipes:
                return True
            if agent.inventory.get("stick", 0) >= 4 and any(count >= 1 for item, count in agent.inventory.items() if "log" in ITEMS[item].tags):
                return True
        return False

    def _productive_replacement(self, agent: Agent, decision: Decision, reason: str) -> tuple[Decision, str]:
        urgent = self._urgent_progression_decision(agent, decision)
        if urgent:
            agent.last_intent = urgent.intent
            return urgent, reason
        recipe = self._best_known_craft(agent)
        discoverable_recipe = self._best_discoverable(agent)
        recipe_priority = self._craft_priority(agent, recipe) if recipe else 999
        if recipe and (not discoverable_recipe or self._craft_priority(agent, recipe) <= self._craft_priority(agent, discoverable_recipe)):
            if recipe_priority > 5:
                progress_move = self._progress_exploration_move(agent, decision)
                if progress_move:
                    agent.last_intent = progress_move.intent
                    return progress_move, reason
            adjusted = Decision(
                action="craft",
                recipe_id=recipe.recipe_id,
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"craft available {recipe.name}",
                thought=f"{recipe.name} is actually available, so I should make that instead of guessing.",
            )
            agent.last_intent = adjusted.intent
            return adjusted, reason
        if discoverable_recipe:
            adjusted = Decision(
                action="experiment",
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"test materials for {discoverable_recipe.name}",
                thought=f"{discoverable_recipe.name} looks like the more important next recipe to test.",
            )
            agent.last_intent = adjusted.intent
            return adjusted, reason
        progress_move = self._progress_exploration_move(agent, decision)
        if progress_move:
            agent.last_intent = progress_move.intent
            return progress_move, reason
        option = self._best_immediate_interaction(agent)
        if option:
            target = str(option["target"]).lower()
            adjusted = Decision(
                action="interact",
                target_dx=int(option["target_dx"]),
                target_dy=int(option["target_dy"]),
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"check immediate {target} instead of invalid action",
                thought=f"{option['target']} is real and close; that is better than an invalid action.",
            )
            agent.last_intent = adjusted.intent
            return adjusted, reason
        return Decision("wait", speech=decision.speech, private_memory=decision.private_memory, intent="avoid invalid action", thought="I caught myself trying something invalid, so I need to reassess."), reason

    def _urgent_progression_decision(self, agent: Agent, decision: Decision) -> Decision | None:
        place_item = self._best_urgent_placeable(agent)
        if place_item:
            return Decision(
                action="place",
                place_item=place_item,
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"place ready {item_name(place_item)}",
                thought=f"{item_name(place_item)} is already in my pack; setting it down unlocks more than wandering does.",
            )
        recipe = self._best_known_craft(agent)
        if recipe and self._craft_priority(agent, recipe) <= 3:
            return Decision(
                action="craft",
                recipe_id=recipe.recipe_id,
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"craft key recipe {recipe.name}",
                thought=f"{recipe.name} is a real step forward now, so I should make it before drifting off.",
            )
        discoverable_recipe = self._best_discoverable(agent)
        if discoverable_recipe and self._craft_priority(agent, discoverable_recipe) <= 3:
            return Decision(
                action="experiment",
                speech=decision.speech,
                private_memory=decision.private_memory,
                intent=f"test key materials for {discoverable_recipe.name}",
                thought=f"The materials line up for {discoverable_recipe.name}; this is the moment to test that idea.",
            )
        return None

    def _best_urgent_placeable(self, agent: Agent) -> str:
        current_tile = self.world.tile(agent.x, agent.y)
        if current_tile.feature or "water" in TERRAINS[current_tile.terrain].tags:
            return ""
        ranked: list[tuple[int, str]] = []
        priorities = {"campfire": 1, "workbench": 2, "kiln": 3, "tent": 4, "bedroll": 5, "wooden_crate": 6}
        for item_id in self._placeable_inventory(agent):
            if self.world.has_station_near(agent.x, agent.y, item_id):
                continue
            ranked.append((priorities.get(item_id, 9), item_id))
        return sorted(ranked)[0][1] if ranked else ""

    def _best_known_craft(self, agent: Agent) -> RecipeDef | None:
        candidates = craftable_known(agent, self.world)
        if not candidates:
            return None
        scored = [(self._craft_priority(agent, recipe), recipe) for recipe in candidates]
        scored = [(score, recipe) for score, recipe in scored if score < 999]
        if not scored:
            return None
        return sorted(scored, key=lambda pair: (pair[0], pair[1].recipe_id))[0][1]

    def _craft_priority(self, agent: Agent, recipe: RecipeDef) -> int:
        outputs = dict(recipe.outputs)
        output_ids = set(outputs)
        if any(ITEMS[item_id].food > 0 and ("cooked" in ITEMS[item_id].tags or agent.hunger < 65) for item_id in output_ids):
            return 0
        if "campfire" in output_ids and not self._has_item_or_station(agent, "campfire"):
            return 1
        if "workbench" in output_ids and not self._has_item_or_station(agent, "workbench"):
            return 2
        if "kiln" in output_ids and not self._has_item_or_station(agent, "kiln"):
            return 3
        if any(self._is_needed_tool(agent, item_id) for item_id in output_ids):
            return 4 + min(self._tool_need_rank(ITEMS[item_id]) for item_id in output_ids if self._is_needed_tool(agent, item_id))
        if any(item_id in PLACEABLE_ITEMS and not self._has_item_or_station(agent, item_id) for item_id in output_ids):
            return 5
        if recipe.recipe_id == "planks_from_log":
            if not self._has_item_or_station(agent, "workbench") and agent.inventory.get("plank", 0) < 4:
                return 3
            return 8 if agent.inventory.get("plank", 0) < 12 else 999
        if recipe.recipe_id == "sticks_from_log":
            if not self._has_item_or_station(agent, "workbench") and agent.inventory.get("stick", 0) < 2:
                return 4
            return 7 if agent.inventory.get("stick", 0) < 10 else 999
        if recipe.recipe_id == "cordage_from_fiber":
            if not self._has_item_or_station(agent, "workbench") and agent.inventory.get("plank", 0) >= 4 and agent.inventory.get("stick", 0) >= 2 and agent.inventory.get("cordage", 0) < 1:
                return 2
            return 6 if agent.inventory.get("cordage", 0) < 4 else 999
        if recipe.recipe_id == "stone_from_pebbles":
            return 6 if agent.inventory.get("stone", 0) < 5 else 999
        if recipe.recipe_id == "arrows":
            return 9 if agent.inventory.get("arrow", 0) < 16 else 999
        if any(ITEMS[item_id].durability and agent.inventory.get(item_id, 0) <= 0 for item_id in output_ids):
            return 10
        return 20

    def _best_discoverable(self, agent: Agent) -> RecipeDef | None:
        candidates = discoverable(agent, self.world)
        if not candidates:
            return None
        return sorted(candidates, key=lambda recipe: (self._craft_priority(agent, recipe), recipe.recipe_id))[0]

    def _has_item_or_station(self, agent: Agent, item_id: str) -> bool:
        return agent.inventory.get(item_id, 0) > 0 or self.world.has_station_near(agent.x, agent.y, item_id)

    @staticmethod
    def _is_needed_tool(agent: Agent, item_id: str) -> bool:
        item = ITEMS[item_id]
        if not item.tool_tags:
            return False
        return any(agent.best_tool(tag, item.tool_power) is None for tag in item.tool_tags)

    @staticmethod
    def _tool_need_rank(item: object) -> int:
        tags = set(getattr(item, "tool_tags", ()))
        if "pickaxe" in tags:
            return 0
        if "axe" in tags:
            return 1
        if "shovel" in tags:
            return 2
        if "blade" in tags:
            return 3
        if "fishing" in tags or "net" in tags:
            return 4
        if "spear" in tags or "bow" in tags:
            return 5
        return 6

    def _validated_private_memory(self, agent: Agent, decision: Decision, event: RoundEvent, note: str) -> str:
        note = clean_inner_text(note, 220)
        if not note:
            return ""
        if any(ord(char) > 127 for char in note):
            return ""
        lowered = note.lower()
        if re.search(r"\b(user|player\s*\d+|nearby player|players?\s+nearby)\b", lowered):
            return ""
        if re.search(r"\([A-Z][A-Za-z]{2,}\)", note) or re.search(r"\b(woodcutter|stranger|miner)\s*\(", lowered):
            return ""
        if re.search(r"\b(player|person|companion)\b", lowered) and not any(message.speaker.lower() in lowered for message in agent.heard_messages):
            return ""
        if re.search(r"\b(rabbit|villager|blacksmith|cabin|wildlife)\b", lowered):
            return ""
        if re.search(r"\b(willing|friendly|seems|might be)\b", lowered) and "said" not in lowered and "heard" not in lowered:
            return ""
        if re.search(r"\b(i will|i'?ll|i am|i'?m|i am going to|i'?m going to|i should|i need to|i want to|plan to|want to|need to|might want to)\b", lowered):
            return ""
        if re.search(r"\bmoved\s+(to|from)\s*\(\s*-?\d+\s*,\s*-?\d+\s*\)", lowered):
            return ""
        if re.search(r"\bmoved\s+(north|south|east|west|left|right|up|down)\b", lowered):
            return ""
        if "no action needed" in lowered:
            return ""
        if re.search(r"\blocation\s*:\s*\(\s*-?\d+\s*,\s*-?\d+\s*\)", lowered):
            return ""
        if self._has_unsupported_speech_term(note):
            return ""
        result = event.text.lower()
        if self._memory_imagines_unowned_placeable(agent, note, result):
            return ""
        unsupported_action_claims = {
            "placed": "placed" not in result,
            "crafted": "crafted" not in result,
            "made": "crafted" not in result and "made" not in result,
            "moved": "moved" not in result,
            "discovered": "discovered" not in result,
            "collected": "collected" not in result,
            "harvested": "harvested" not in result,
            "foraged": "foraged" not in result,
            "gathered": "gathered" not in result,
            "found": not any(word in result for word in ("got", "harvested", "foraged", "gathered", "dug", "searched")),
        }
        if any(word in lowered and blocked for word, blocked in unsupported_action_claims.items()):
            return ""
        if "tree" in lowered and "tree" not in result:
            return ""
        if "crate" in lowered and "crate" not in result:
            return ""
        if re.search(r"\bat coordinates?\b|\(\s*-?\d+\s*,\s*-?\d+\s*\)", lowered):
            current = f"{agent.x},{agent.y}"
            compact = re.sub(r"\s+", "", lowered)
            if current not in compact and event.kind not in {"move", "place"}:
                return ""
        return note

    def _memory_imagines_unowned_placeable(self, agent: Agent, note: str, result: str) -> bool:
        lowered = note.lower()
        if "placed" in result:
            return False
        if not re.search(r"\b(placing|place|set up|setup|build|building|built)\b", lowered):
            return False
        for item_id in PLACEABLE_ITEMS:
            item_label = item_name(item_id).lower()
            if item_id.replace("_", " ") not in lowered and item_label not in lowered:
                continue
            if agent.inventory.get(item_id, 0) <= 0 and not self.world.has_station_near(agent.x, agent.y, item_id):
                return True
        return False

    @staticmethod
    def _looks_like_vague_exploration(decision: Decision) -> bool:
        text = f"{decision.intent} {decision.thought} {decision.private_memory}".lower()
        vague_markers = (
            "explore",
            "surround",
            "resource",
            "look",
            "search",
            "scout",
            "keep moving",
            "eye out",
            "checking",
            "check ",
            "nearby",
            "later",
        )
        return not text.strip() or any(marker in text for marker in vague_markers)

    def _best_immediate_interaction(self, agent: Agent) -> dict[str, Any] | None:
        options = [option for option in self._immediate_actions(agent) if option.get("available")]
        if not options:
            return None
        persona_priorities: dict[str, tuple[str, ...]] = {
            "builder": ("wood", "tree", "fiber", "earth", "clay", "stone", "food"),
            "miner": ("rock", "stone", "ore", "metal", "clay", "wood", "food"),
            "provider": ("food", "fish", "coast", "plant", "fiber", "wood"),
            "explorer": ("food", "plant", "wood", "rock", "clay"),
            "forager": ("plant", "food", "medicine", "fiber", "wood"),
            "trader": ("food", "fiber", "wood", "stone", "clay"),
            "minmaxer": ("wood", "fiber", "stone", "food", "clay"),
            "solo": ("food", "wood", "stone", "fiber", "clay"),
            "cook": ("food", "wood", "fiber", "clay", "stone"),
            "tinkerer": ("fiber", "wood", "stone", "clay", "rock"),
        }
        priorities = persona_priorities.get(agent.persona.archetype, ("food", "wood", "fiber", "stone", "clay"))

        def score(option: dict[str, Any]) -> tuple[int, int, int, int]:
            tags = set(option.get("tags", []))
            expected_text = " ".join(option.get("expected_loot", [])).lower()
            log_count = sum(agent.inventory.get(item_id, 0) for item_id in ("birch_log", "oak_log", "pine_log", "fruit_log"))
            needs_logs = agent.best_tool("axe", 1) and log_count <= 0 and agent.inventory.get("plank", 0) < 4
            if needs_logs and option.get("target_type") == "feature" and "tree" in tags:
                strategic_score = 0
            elif needs_logs and ("forest" in tags or "wood" in tags):
                strategic_score = 1
            else:
                strategic_score = 2
            priority_hits = [index for index, tag in enumerate(priorities) if tag in tags or tag in expected_text]
            priority_score = min(priority_hits) if priority_hits else len(priorities)
            feature_bonus = 0 if option.get("target_type") == "feature" else 1
            distance = abs(int(option["target_dx"])) + abs(int(option["target_dy"]))
            return (strategic_score, priority_score, feature_bonus, distance)

        return sorted(options, key=score)[0]

    def _apply(self, agent: Agent, decision: Decision, occupied_snapshot: dict[tuple[int, int], int]) -> RoundEvent:
        action = decision.action
        if self._should_auto_eat(agent, action):
            eaten = agent.eat_best_food(target_hunger=86.0)
            if eaten:
                agent.last_action = f"ate {eaten}"
                return RoundEvent(agent.name, agent.last_action, "eat")
        if action == "move":
            return self._move(agent, decision.dx, decision.dy, occupied_snapshot)
        if action == "interact":
            return self._interact(agent, decision.target_dx, decision.target_dy)
        if action == "craft":
            return self._craft(agent, decision.recipe_id)
        if action == "experiment":
            return self._experiment(agent)
        if action == "place":
            return self._place(agent, decision.place_item)
        if action == "eat":
            eaten = agent.eat_best_food()
            text = f"ate {eaten}" if eaten else "looked for food but had none"
            agent.last_action = text
            return RoundEvent(agent.name, text, "eat")
        if action == "talk":
            agent.last_action = "talked while watching the area"
            return RoundEvent(agent.name, agent.last_action, "talk")
        agent.last_action = "waited and watched"
        return RoundEvent(agent.name, agent.last_action, "wait")

    @staticmethod
    def _should_auto_eat(agent: Agent, action: str) -> bool:
        if action in {"eat", "wait"}:
            return False
        if not any(ITEMS[item_id].food > 0 for item_id, count in agent.inventory.items() if count > 0):
            return False
        if agent.hunger < 42:
            return True
        if agent.hunger < 58 and action in {"move", "interact", "talk"}:
            return True
        return False

    def _move(self, agent: Agent, dx: int, dy: int, occupied_snapshot: dict[tuple[int, int], int]) -> RoundEvent:
        if dx == 0 and dy == 0:
            return self._fallback_move(agent, occupied_snapshot)
        nx, ny = agent.x + dx, agent.y + dy
        if not self.world.can_enter(agent, nx, ny):
            agent.last_action = "planned a blocked move"
            return self._fallback_move(agent, occupied_snapshot)
        if (nx, ny) in occupied_snapshot and occupied_snapshot[(nx, ny)] != agent.agent_id:
            agent.last_action = "nearly bumped into another player"
            return self._fallback_move(agent, occupied_snapshot)
        occupied_snapshot.pop((agent.x, agent.y), None)
        agent.x, agent.y = nx, ny
        occupied_snapshot[(nx, ny)] = agent.agent_id
        agent.facing = (dx, dy)
        agent.energy = max(0.0, agent.energy - 0.5)
        agent.last_action = f"moved to {nx},{ny}"
        return RoundEvent(agent.name, agent.last_action, "move")

    def _fallback_move(self, agent: Agent, occupied_snapshot: dict[tuple[int, int], int]) -> RoundEvent:
        options = list(DIRECTIONS)
        self.rng.shuffle(options)
        for dx, dy in options:
            nx, ny = agent.x + dx, agent.y + dy
            if self.world.can_enter(agent, nx, ny) and (nx, ny) not in occupied_snapshot:
                occupied_snapshot.pop((agent.x, agent.y), None)
                agent.x, agent.y = nx, ny
                occupied_snapshot[(nx, ny)] = agent.agent_id
                agent.facing = (dx, dy)
                agent.last_action = f"moved to {nx},{ny}"
                return RoundEvent(agent.name, agent.last_action, "move")
        agent.last_action = "could not find a move"
        return RoundEvent(agent.name, agent.last_action, "wait")

    def _interact(self, agent: Agent, dx: int, dy: int) -> RoundEvent:
        tx, ty = agent.x + dx, agent.y + dy
        if abs(dx) <= 1 and abs(dy) <= 1 and self.world.in_bounds(tx, ty):
            if dx or dy:
                agent.facing = (dx, dy)
            result = self.world.interact(agent, tx, ty)
            loot = ", ".join(f"{count} {item_name(item)}" for item, count in result.loot.items()) or "nothing"
            agent.last_action = f"{result.text}; got {loot}" if result.ok else result.text
            return RoundEvent(agent.name, agent.last_action, "interact")
        agent.last_action = "reached for something too far away"
        return RoundEvent(agent.name, agent.last_action, "interact")

    def _craft(self, agent: Agent, recipe_id: str) -> RoundEvent:
        recipe = RECIPES_BY_ID.get(recipe_id)
        if not recipe or recipe.recipe_id not in agent.known_recipes:
            agent.last_action = "could not craft that yet"
            return RoundEvent(agent.name, agent.last_action, "craft")
        if not has_ingredients(agent.inventory, recipe):
            agent.last_action = f"lacked materials for {recipe.name}"
            return RoundEvent(agent.name, agent.last_action, "craft")
        if not has_output_space(agent, recipe):
            agent.last_action = f"had no inventory space for {recipe.name}"
            return RoundEvent(agent.name, agent.last_action, "craft")
        outputs = craft(agent, recipe)
        text = ", ".join(f"{count} {item_name(item)}" for item, count in outputs.items())
        agent.last_action = f"crafted {text}"
        return RoundEvent(agent.name, agent.last_action, "craft")

    def _experiment(self, agent: Agent) -> RoundEvent:
        recipe = self._best_discoverable(agent)
        if not recipe:
            agent.last_action = "tested items but learned nothing"
            return RoundEvent(agent.name, agent.last_action, "experiment")
        agent.known_recipes.add(recipe.recipe_id)
        outputs = craft(agent, recipe)
        text = ", ".join(f"{count} {item_name(item)}" for item, count in outputs.items())
        agent.last_action = f"discovered {recipe.name} and made {text}"
        agent.remember(f"Discovered recipe: {recipe.name}. Hint: {recipe.hint}.")
        return RoundEvent(agent.name, agent.last_action, "experiment")

    def _place(self, agent: Agent, item_id: str) -> RoundEvent:
        if item_id not in PLACEABLE_ITEMS or agent.inventory.get(item_id, 0) <= 0:
            agent.last_action = "had no placeable item"
            return RoundEvent(agent.name, agent.last_action, "place")
        if self.world.place_station(agent.x, agent.y, item_id):
            agent.inventory[item_id] -= 1
            if agent.inventory[item_id] <= 0:
                del agent.inventory[item_id]
            agent.last_action = f"placed {item_name(item_id)}"
            return RoundEvent(agent.name, agent.last_action, "place")
        agent.last_action = "could not place that here"
        return RoundEvent(agent.name, agent.last_action, "place")

    def _broadcast(self, agent: Agent, speech: str) -> None:
        agent.record_speech(self.round_index, speech)
        message = ChatMessage(self.round_index, agent.name, speech, agent.x, agent.y)
        self.chat.append(message)
        heard_by: list[str] = []
        for other in self.agents:
            if other.agent_id == agent.agent_id:
                continue
            if ((other.x - agent.x) ** 2 + (other.y - agent.y) ** 2) ** 0.5 <= CHAT_RADIUS:
                other.hear(message)
                heard_by.append(other.name)
        self.logger.log_chat(
            {
                "round": self.round_index,
                "speaker": agent.name,
                "text": speech,
                "position": [agent.x, agent.y],
                "heard_by": heard_by,
            }
        )

    def _chat_context_entry(self, agent: Agent, message: ChatMessage) -> dict[str, Any]:
        return {
            "speaker": message.speaker,
            "text": message.text,
            "round": message.round_index,
            "age": max(0, self.round_index - message.round_index),
            "speaker_dx": message.x - agent.x,
            "speaker_dy": message.y - agent.y,
        }

    def _fresh_question_entry(self, agent: Agent, messages: list[ChatMessage]) -> dict[str, Any] | None:
        for message in reversed(messages):
            if message.round_index < self.round_index - 2:
                continue
            text = message.text.strip()
            lowered = text.lower()
            looks_like_question = "?" in text or lowered.startswith(("anyone ", "does ", "do ", "can ", "where ", "what ", "how ", "who ", "need ", "got "))
            if looks_like_question:
                return self._chat_context_entry(agent, message)
        return None

    @staticmethod
    def _speech_addresses_question(speech: str, question: str) -> bool:
        speech_words = {_word_stem(word) for word in re.findall(r"[a-z]{3,}", speech.lower())}
        question_words = {_word_stem(word) for word in re.findall(r"[a-z]{3,}", question.lower())}
        question_lower = question.lower()
        speech_lower = speech.lower()
        asks_back_instead = "?" in speech and any(marker in speech_lower for marker in ("do you have", "do you know", "can you spare", "happen to have"))
        direct_request_question = any(marker in question_lower for marker in ("do you have", "do you know", "can you spare", "any to spare", "need any help"))
        if direct_request_question and asks_back_instead:
            return False
        question_words -= {
            "anyone",
            "somebody",
            "someone",
            "know",
            "knows",
            "does",
            "what",
            "where",
            "when",
            "which",
            "need",
            "with",
            "have",
            "that",
            "this",
            "they",
            "them",
            "you",
            "your",
            "are",
            "for",
            "the",
        }
        asks_where = any(marker in question_lower for marker in ("where", "find", "around here"))
        gives_location = any(marker in speech_lower for marker in ("north", "south", "east", "west", "nearby", "around", "bush", "patch", "over there", "close", "next to"))
        self_plan = any(marker in speech_lower for marker in ("i should", "i'll check", "i will check", "i think i'll", "maybe i should"))
        if self_plan:
            return False
        if asks_where and gives_location and bool(speech_words & question_words):
            return True
        honest_unknown = (
            "not sure",
            "no idea",
            "don't know",
            "dont know",
            "haven't tried",
            "havent tried",
            "haven't tested",
            "havent tested",
            "maybe",
            "try",
            "test",
        )
        if any(marker in speech.lower() for marker in honest_unknown):
            return True
        return bool(speech_words & question_words)

    def _speech_quality_block_reason(self, agent: Agent, speech: str, fresh_question: dict[str, Any] | None, fresh_heard_chat: bool) -> str:
        if not speech:
            return ""
        if self._has_unsupported_speech_term(speech):
            return "unsupported item or recipe claim"
        if self._claims_unknown_recipe(agent, speech):
            return "unknown recipe claim"
        if self._is_generic_help_offer(speech) and not fresh_question and not self._surplus_inventory_topics(agent):
            return "generic help offer without concrete help"
        if self._is_status_update_speech(agent, speech):
            return "status update instead of dialogue"
        if self._is_low_value_smalltalk(speech):
            return "low-value smalltalk"
        if fresh_question and not self._speech_addresses_question(speech, fresh_question["text"]):
            return "did not answer fresh question"
        if not fresh_heard_chat and not self._is_dialogue_speech(agent, speech):
            return "not dialogue"
        return ""

    @staticmethod
    def _speech_result_block_reason(speech: str, event: RoundEvent) -> str:
        if not speech:
            return ""
        lowered = speech.lower()
        result = event.text.lower()
        completed_claims = {
            "placed": ("placed", "place"),
            "set up": ("placed", "place", "set up"),
            "built": ("built", "placed", "crafted"),
            "crafted": ("crafted",),
            "made": ("crafted", "made"),
            "found": ("got", "found", "caught", "mined", "chopped", "harvested", "foraged"),
            "got": ("got", "caught", "mined", "chopped", "harvested", "foraged"),
            "caught": ("caught",),
        }
        for claim, result_markers in completed_claims.items():
            if re.search(rf"\b(i'?ve|i have|i just|just|now i)\s+{re.escape(claim)}\b", lowered):
                if not any(marker in result for marker in result_markers):
                    return "claimed action not completed"
        if re.search(r"\bnow i can rest here\b", lowered) and "placed" not in result:
            return "claimed action not completed"
        return ""

    @staticmethod
    def _has_unsupported_speech_term(speech: str) -> bool:
        lowered = speech.lower()
        return any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in UNSUPPORTED_SPEECH_TERMS)

    @staticmethod
    def _claims_unknown_recipe(agent: Agent, speech: str) -> bool:
        lowered = speech.lower()
        if "how to craft" not in lowered and "recipe" not in lowered:
            return False
        known_names = {RECIPES_BY_ID[recipe_id].name.lower() for recipe_id in agent.known_recipes if recipe_id in RECIPES_BY_ID}
        for recipe in RECIPES_BY_ID.values():
            recipe_name = recipe.name.lower()
            output_names = {item_name(item_id).lower() for item_id, _count in recipe.outputs}
            mentioned = recipe_name in lowered or any(name in lowered for name in output_names)
            if mentioned and recipe_name not in known_names:
                return True
        return False

    def _recent_global_chat_similar(self, speech: str) -> bool:
        normalized = self._normalize_speech(speech)
        if not normalized:
            return True
        for message in self.chat[-8:]:
            if self.round_index - message.round_index > 5:
                continue
            recent = self._normalize_speech(message.text)
            if self._word_similarity(normalized, recent) >= 0.68 or self._shared_word_count(normalized, recent) >= 4:
                return True
        return False

    def _is_status_update_speech(self, agent: Agent, speech: str) -> bool:
        lowered = speech.lower().strip()
        if re.search(r"\b(what would you like to do|center of the map)\b", lowered):
            return True
        if "?" in lowered:
            return False
        if re.search(r"\bi need to be able to\b", lowered):
            return True
        if any(re.search(pattern, lowered) for pattern in STATUS_UPDATE_PATTERNS):
            return True
        if self._has_direct_social_marker(agent, lowered):
            return False
        return False

    def _is_dialogue_speech(self, agent: Agent, speech: str) -> bool:
        lowered = speech.lower()
        if "?" in lowered or self._has_direct_social_marker(agent, lowered):
            return True
        return any(self._contains_marker(lowered, marker) for marker in DIALOGUE_MARKERS)

    @staticmethod
    def _is_generic_help_offer(speech: str) -> bool:
        lowered = speech.lower()
        return "need any help" in lowered and any(topic in lowered for topic in ("gather", "resource", "craft"))

    @staticmethod
    def _is_low_value_smalltalk(speech: str) -> bool:
        lowered = speech.lower()
        if "weather" in lowered:
            return True
        if "admiring the view" in lowered or "enjoy the view" in lowered:
            return True
        greeting_only = re.sub(r"\b(hey|hi|hello|there|folks|everyone)\b", " ", lowered)
        greeting_only = re.sub(r"[^a-z0-9]+", " ", greeting_only).strip()
        return not greeting_only

    def _has_direct_social_marker(self, agent: Agent, lowered: str) -> bool:
        direct_markers = {
            "anyone",
            "someone",
            "somebody",
            "you",
            "your",
            "we",
            "us",
            "trade",
            "swap",
            "spare",
            "help",
            "thanks",
            "thank",
            "careful",
            "watch",
            "danger",
            "warning",
        }
        if any(self._contains_marker(lowered, marker) for marker in direct_markers):
            return True
        return any(self._contains_marker(lowered, other.name.lower()) for other in self.agents if other.agent_id != agent.agent_id)

    @staticmethod
    def _contains_marker(lowered: str, marker: str) -> bool:
        if " " in marker or "'" in marker:
            return marker in lowered
        return bool(re.search(rf"\b{re.escape(marker)}\b", lowered))

    @staticmethod
    def _normalize_speech(text: str) -> str:
        text = re.sub(r"^(hey|hi|hello)( there| everyone| folks)?\s+", "", text.lower().strip())
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _word_similarity(left: str, right: str) -> float:
        left_words = set(left.split())
        right_words = set(right.split())
        if not left_words or not right_words:
            return 0.0
        return len(left_words & right_words) / len(left_words | right_words)

    @staticmethod
    def _shared_word_count(left: str, right: str) -> int:
        ignored = {"there", "with", "some", "just", "here", "that", "this", "they", "them", "could", "think", "maybe"}
        left_words = set(left.split()) - ignored
        right_words = set(right.split()) - ignored
        return len(left_words & right_words)

    def _immediate_actions(self, agent: Agent) -> list[dict[str, Any]]:
        options: list[dict[str, Any]] = []
        food_options = self._food_inventory(agent)
        if food_options and agent.hunger < 88:
            options.append(
                {
                    "action": "eat",
                    "target_dx": 0,
                    "target_dy": 0,
                    "target": food_options[0]["name"],
                    "target_type": "food",
                    "tags": food_options[0]["tags"],
                    "available": True,
                    "blocked_by": "",
                    "expected_loot": [f"+{food_options[0]['food']} hunger"],
                }
            )
        current_tile = self.world.tile(agent.x, agent.y)
        if not current_tile.feature and "water" not in TERRAINS[current_tile.terrain].tags:
            for item_id in self._placeable_inventory(agent):
                options.append(
                    {
                        "action": "place",
                        "place_item": item_id,
                        "target_dx": 0,
                        "target_dy": 0,
                        "target": item_name(item_id),
                        "target_type": "placeable",
                        "tags": list(ITEMS[item_id].tags),
                        "available": True,
                        "blocked_by": "",
                        "expected_loot": [],
                    }
                )
        for dx, dy in CENTER_AND_NEIGHBORS:
            x, y = agent.x + dx, agent.y + dy
            if not self.world.in_bounds(x, y):
                continue
            tile = self.world.tile(x, y)
            if tile.feature:
                feature = FEATURES[tile.feature]
                blocked_by = ""
                if feature.required_tool and not agent.best_tool(feature.required_tool, feature.min_power):
                    blocked_by = f"needs {feature.required_tool}"
                options.append(
                    {
                        "action": "interact",
                        "target_dx": dx,
                        "target_dy": dy,
                        "target": feature.name,
                        "target_type": "feature",
                        "tags": list(feature.tags),
                        "available": not blocked_by,
                        "blocked_by": blocked_by,
                        "expected_loot": self._loot_summary(feature.loot),
                    }
                )
            else:
                terrain = TERRAINS[tile.terrain]
                available, blocked_by, expected = self._terrain_interaction_summary(agent, terrain.tags)
                options.append(
                    {
                        "action": "interact",
                        "target_dx": dx,
                        "target_dy": dy,
                        "target": terrain.name,
                        "target_type": "ground",
                        "tags": list(terrain.tags),
                        "available": available,
                        "blocked_by": blocked_by,
                        "expected_loot": expected,
                    }
                )
        type_rank = {"food": 0, "feature": 1, "placeable": 2, "ground": 3}
        return sorted(options, key=lambda option: (not option["available"], type_rank.get(option["target_type"], 3), abs(option["target_dx"]) + abs(option["target_dy"])))[:10]

    @staticmethod
    def _placeable_inventory(agent: Agent) -> list[str]:
        return sorted(item_id for item_id in PLACEABLE_ITEMS if agent.inventory.get(item_id, 0) > 0)

    @staticmethod
    def _food_inventory(agent: Agent) -> list[dict[str, Any]]:
        foods: list[dict[str, Any]] = []
        for item_id, count in agent.inventory.items():
            if count <= 0:
                continue
            item = ITEMS[item_id]
            if item.food <= 0:
                continue
            foods.append(
                {
                    "item_id": item_id,
                    "name": item_name(item_id),
                    "count": count,
                    "food": item.food,
                    "tags": list(item.tags),
                    "raw": "raw" in item.tags,
                    "cooked": "cooked" in item.tags,
                }
            )
        return sorted(foods, key=lambda food: (food["raw"], -int(food["food"]), str(food["name"])))

    @staticmethod
    def _hunger_state(agent: Agent) -> str:
        if agent.hunger <= 0:
            return "starving"
        if agent.hunger < 35:
            return "critical"
        if agent.hunger < 60:
            return "hungry"
        if agent.hunger < 82:
            return "peckish"
        return "fed"

    def _terrain_interaction_summary(self, agent: Agent, tags: tuple[str, ...]) -> tuple[bool, str, list[str]]:
        if "water" in tags:
            if agent.best_tool("net", 1) or agent.best_tool("fishing", 1):
                return True, "", ["Raw fish", "Seaweed"]
            return False, "needs fishing rod or net", []
        if "coast" in tags:
            return True, "", ["Clean sand", "Shell"]
        if "grass" in tags or "forest" in tags:
            return True, "", ["Grass fiber", "Stick", "Berries"]
        if "wet" in tags:
            return True, "", ["Reeds", "Bitter herb"]
        if "clay" in tags:
            return True, "", ["Clay lump"]
        if "rock" in tags or "hill" in tags:
            if agent.best_tool("pickaxe", 1):
                return True, "", ["Stone", "Coal"]
            return True, "", ["Pebble", "Flint"]
        if "sand" in tags or "dry" in tags:
            return True, "", ["Clean sand", "Flint"]
        return True, "", ["Handful of soil"]

    @staticmethod
    def _loot_summary(loot: tuple[object, ...]) -> list[str]:
        names: list[str] = []
        for entry in loot:
            item = getattr(entry, "item", "")
            if item:
                names.append(item_name(item))
        return names

    def _polish_thought(self, agent: Agent, thought: str, decision: Decision) -> str:
        if any(ord(char) > 127 for char in thought):
            return self._fallback_thought(agent, decision)
        normalized = re.sub(r"[^a-z0-9]+", " ", thought.lower()).strip()
        goal = re.sub(r"[^a-z0-9]+", " ", agent.persona.long_goal.lower()).strip()
        bad_goal_copy = goal and goal in normalized
        generic_move = (
            "keep moving toward" in normalized
            or "need to keep moving" in normalized
            or normalized.startswith("moving to ")
            or normalized.startswith("moving one step")
            or normalized.startswith("i am moving ")
            or normalized.startswith("i m moving ")
            or normalized in {"move", "moving", "stay", "stay put", "idle"}
        )
        meta_player = (
            normalized.startswith("the player ")
            or "the player wants" in normalized
            or "player is already" in normalized
            or "desired location" in normalized
            or "move the character" in normalized
        )
        fake_social = "get to know" in normalized or "better conversation" in normalized
        if not bad_goal_copy and not generic_move and not meta_player and not fake_social:
            return thought
        if decision.action == "interact":
            return "There is something close enough to check, and guessing from a distance is wasting time."
        if decision.action == "craft":
            return "I have enough pieces for a concrete craft, so this is the right moment to try it."
        if decision.action == "experiment":
            return "These materials might reveal a recipe if I stop overthinking and test them."
        if decision.action == "move":
            return "I need a better nearby resource lead, so I am repositioning instead of standing around."
        if decision.action == "talk":
            return "This is worth saying out loud because someone nearby may actually use it."
        return "I need a concrete next step, not a vague plan."

    def _context(self, agent: Agent) -> dict[str, Any]:
        nearby_cells: list[dict[str, Any]] = []
        nearby_players: list[dict[str, Any]] = []
        for dy in range(-SIGHT_RADIUS, SIGHT_RADIUS + 1):
            for dx in range(-SIGHT_RADIUS, SIGHT_RADIUS + 1):
                x, y = agent.x + dx, agent.y + dy
                if not self.world.in_bounds(x, y):
                    continue
                tile = self.world.tile(x, y)
                close = max(abs(dx), abs(dy)) <= 2
                if not close and not tile.feature:
                    continue
                terrain = TERRAINS[tile.terrain]
                entry: dict[str, Any] = {
                    "dx": dx,
                    "dy": dy,
                    "ground": terrain.name,
                    "ground_tags": list(terrain.tags),
                    "passable": self.world.can_enter(agent, x, y),
                }
                if tile.feature:
                    feature = FEATURES[tile.feature]
                    entry.update(
                        {
                            "feature": feature.name,
                            "feature_tags": list(feature.tags),
                            "requires_tool": feature.required_tool or "",
                            "min_power": feature.min_power,
                        }
                    )
                nearby_cells.append(entry)
        for other in self.agents:
            if other.agent_id == agent.agent_id:
                continue
            dx, dy = other.x - agent.x, other.y - agent.y
            if max(abs(dx), abs(dy)) <= SIGHT_RADIUS:
                nearby_players.append({"name": other.name, "dx": dx, "dy": dy, "last_action": other.last_action})
        known_recipes = craftable_known(agent, self.world)
        heard_messages = list(agent.heard_messages)
        new_heard_messages = [msg for msg in heard_messages if msg.round_index > agent.last_seen_chat_round]
        fresh_question = self._fresh_question_entry(agent, new_heard_messages)
        placeable_inventory = self._placeable_inventory(agent)
        available_actions = ["move", "interact", "craft", "experiment", "eat", "talk", "wait"]
        if placeable_inventory:
            available_actions.append("place")
        forbidden_actions = sorted({"place"} - set(available_actions))
        context = {
            "round": self.round_index,
            "available_actions": available_actions,
            "forbidden_actions": forbidden_actions,
            "turn_guidance": [
                "Choose only an action listed in available_actions; actions listed in forbidden_actions are invalid this turn.",
                "If an immediate_actions entry is available and useful, usually interact instead of wandering.",
                "If hunger is below 60 and food_inventory is not empty, eat before routine movement or chatter.",
                "Cooked food is safer and stronger than raw food; if hunger is not urgent and a campfire recipe is available, cook raw food first.",
                "If you have gathered similar ground resources for several turns and recipes are available or discoverable, craft or experiment instead of foraging again.",
                "Use action='place' only when available_actions includes place and placeable_inventory lists the exact item.",
                "If placeable_inventory is empty, do not plan or chat about placing campfires, crates, bedrolls, tents, doors, or workbenches yet.",
                "Move when you are blocked, repositioning toward a visible better target, or avoiding danger.",
                "Speech is optional and should not describe the action you are taking.",
            ],
            "self": {
                "name": agent.name,
                "origin": agent.persona.origin,
                "archetype": agent.persona.archetype,
                "long_goal": agent.persona.long_goal,
                "temperament": agent.persona.temperament,
                "social_style": agent.persona.social_style,
                "position": [agent.x, agent.y],
                "health": round(agent.health, 1),
                "hunger": round(agent.hunger, 1),
                "hunger_state": self._hunger_state(agent),
                "energy": round(agent.energy, 1),
                "last_action": agent.last_action,
                "last_thought": agent.last_thought,
                "private_memory": list(agent.private_memory),
                "recent_actions": list(agent.recent_actions),
                "recent_speech": list(agent.recent_speech),
                "recent_thoughts": list(agent.recent_thoughts),
            },
            "inventory": [
                {"item_id": item_id, "name": item_name(item_id), "count": count, "tags": list(ITEMS[item_id].tags)}
                for item_id, count in sorted(agent.inventory.items())
                if count > 0
            ],
            "inventory_rules": {
                "used_slots": agent.used_inventory_slots,
                "free_slots": agent.free_inventory_slots,
                "slot_limit": agent.inventory_slot_limit,
                "max_stack_by_item": {item_id: ITEMS[item_id].max_stack for item_id, count in agent.inventory.items() if count > 0},
            },
            "food_inventory": self._food_inventory(agent),
            "tools": [
                {
                    "item_id": item_id,
                    "name": item_name(item_id),
                    "tags": list(ITEMS[item_id].tool_tags),
                    "power": ITEMS[item_id].tool_power,
                    "durability": agent.tool_durability.get(item_id, ITEMS[item_id].durability),
                }
                for item_id in agent.inventory
                if ITEMS[item_id].tool_tags
            ],
            "placeable_inventory": [
                {"item_id": item_id, "name": item_name(item_id)}
                for item_id in placeable_inventory
            ],
            "known_craftable_recipes": [
                {
                    "recipe_id": recipe.recipe_id,
                    "name": recipe.name,
                    "station": recipe.station or "",
                    "outputs": [{"item": item, "name": item_name(item), "count": count} for item, count in recipe.outputs],
                }
                for recipe in known_recipes
            ],
            "immediate_actions": self._immediate_actions(agent),
            "heard_chat": [self._chat_context_entry(agent, msg) for msg in heard_messages[-10:]],
            "new_heard_chat": [self._chat_context_entry(agent, msg) for msg in new_heard_messages[-6:]],
            "communication": {
                "chat_radius": CHAT_RADIUS,
                "chat_cooldown": agent.chat_cooldown,
                "can_be_heard_by": self._nearby_chat_listener_names(agent),
                "chat_silence_rounds": self._chat_silence_rounds(),
                "social_openings": self._social_openings(agent, nearby_players, known_recipes),
                "fresh_question_to_answer": fresh_question,
                "speech_can_accompany_action": True,
                "use_talk_action_only_if_conversation_is_worth_the_turn": True,
                "avoid_narrating_current_action": True,
                "speech_rules": [
                    "Use speech for replies, questions, offers, requests, warnings, trades, or occasional social remarks.",
                    "Do not say what you are about to move/gather/craft/place; put that in thought instead.",
                    "If you have nothing to say to another player, keep speech empty.",
                ],
                "blocked_speech_examples": [
                    "I'll move a bit to the right.",
                    "I need to gather more resources.",
                    "I'll need some wood to make a campfire.",
                    "I've placed a bedroll here.",
                    "Moving one step to the left.",
                    "I need to set up a workbench before I can craft.",
                ],
            },
            "nearby_players": nearby_players,
            "has_chat_listener": self._has_chat_listener(agent),
            "nearby_cells": sorted(nearby_cells, key=lambda cell: (0 if "feature" in cell else 1, abs(cell["dx"]) + abs(cell["dy"])))[:64],
        }
        if heard_messages:
            agent.last_seen_chat_round = max(agent.last_seen_chat_round, max(msg.round_index for msg in heard_messages))
        return context

    def _has_chat_listener(self, agent: Agent) -> bool:
        for other in self.agents:
            if other.agent_id == agent.agent_id or other.health <= 0:
                continue
            if ((other.x - agent.x) ** 2 + (other.y - agent.y) ** 2) ** 0.5 <= CHAT_RADIUS:
                return True
        return False

    def _has_fresh_heard_chat(self, agent: Agent) -> bool:
        return any(msg.round_index >= self.round_index - 2 for msg in agent.heard_messages)

    def _nearby_chat_listener_names(self, agent: Agent) -> list[str]:
        names: list[str] = []
        for other in self.agents:
            if other.agent_id == agent.agent_id or other.health <= 0:
                continue
            if ((other.x - agent.x) ** 2 + (other.y - agent.y) ** 2) ** 0.5 <= CHAT_RADIUS:
                names.append(other.name)
        return names

    def _chat_silence_rounds(self) -> int:
        if not self.chat:
            return self.round_index
        return max(0, self.round_index - self.chat[-1].round_index)

    def _social_openings(self, agent: Agent, nearby_players: list[dict[str, Any]], known_recipes: list[object]) -> list[str]:
        if not nearby_players:
            return []
        openings: list[str] = []
        silence = self._chat_silence_rounds()
        if silence >= 4 and agent.chat_cooldown <= 0:
            openings.append("chat has been quiet; one short useful question, offer, warning, or casual line is acceptable")
        surplus = self._surplus_inventory_topics(agent)
        if surplus:
            openings.append("you have possible trade/help material: " + ", ".join(surplus))
        if not known_recipes and len(agent.inventory) >= 3:
            openings.append("you are blocked on recipes; asking nearby players one specific crafting question could help")
        if agent.health < 45 or agent.hunger < 35:
            openings.append("you are in trouble; asking nearby players for food or help is reasonable")
        visible_names = ", ".join(player["name"] for player in nearby_players[:3])
        openings.append(f"nearby players visible: {visible_names}; speak to them only if the line benefits interaction")
        return openings[:5]

    @staticmethod
    def _surplus_inventory_topics(agent: Agent) -> list[str]:
        topics: list[str] = []
        for item_id, count in sorted(agent.inventory.items()):
            if count < 4:
                continue
            item = ITEMS[item_id]
            if item.food > 0:
                topics.append(f"{count} {item_name(item_id)} food")
            elif {"fiber", "wood", "rock", "clay", "medicine"} & set(item.tags):
                topics.append(f"{count} {item_name(item_id)}")
        return topics[:4]

    def _world_replay_payload(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "width": self.world.width,
            "height": self.world.height,
            "terrain_rows": ["".join(f"{self.world.tile(x, y).terrain}," for x in range(self.world.width)).rstrip(",") for y in range(self.world.height)],
            "shade_rows": [[self.world.tile(x, y).shade for x in range(self.world.width)] for y in range(self.world.height)],
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "archetype": agent.persona.archetype,
                    "origin": agent.persona.origin,
                    "long_goal": agent.persona.long_goal,
                    "color": list(agent.color),
                    "sprite": agent.sprite,
                }
                for agent in self.agents
            ],
        }

    def _replay_payload(self) -> dict[str, Any]:
        features: list[dict[str, Any]] = []
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.tile(x, y)
                if tile.feature:
                    features.append({"x": x, "y": y, "feature": tile.feature, "hp": tile.hp})
        return {
            "round": self.round_index,
            "features": features,
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "x": agent.x,
                    "y": agent.y,
                    "start_x": agent.start_x,
                    "start_y": agent.start_y,
                    "facing": list(agent.facing),
                    "start_facing": list(agent.start_facing),
                    "health": round(agent.health, 2),
                    "hunger": round(agent.hunger, 2),
                    "energy": round(agent.energy, 2),
                    "inventory": {item: count for item, count in sorted(agent.inventory.items()) if count > 0},
                    "used_inventory_slots": agent.used_inventory_slots,
                    "inventory_slot_limit": agent.inventory_slot_limit,
                    "last_action": agent.last_action,
                    "last_intent": agent.last_intent,
                    "last_thought": agent.last_thought,
                    "known_recipes": sorted(agent.known_recipes),
                }
                for agent in self.agents
            ],
            "events": [{"agent": event.agent, "kind": event.kind, "text": event.text} for event in self.round_events],
            "chat": [
                {"round": msg.round_index, "speaker": msg.speaker, "text": msg.text, "x": msg.x, "y": msg.y}
                for msg in self.chat[-20:]
            ],
        }

    def _fallback_decision(self, agent: Agent) -> Decision:
        if agent.hunger < 65 and any(ITEMS[item].food > 0 for item in agent.inventory):
            return Decision("eat", intent="eat from inventory", thought="I am hungry enough that food matters more than progress.")
        recipe = self._best_known_craft(agent)
        if recipe:
            return Decision("craft", recipe_id=recipe.recipe_id, intent="craft known recipe", thought=f"I can make {recipe.name}, so I should use the chance.")
        if self._best_discoverable(agent):
            return Decision("experiment", intent="try hidden recipe", thought="These materials might fit together; testing them could unlock something.")
        if self.rng.random() < 0.6:
            dx, dy = self.rng.choice(DIRECTIONS)
            return Decision("move", dx=dx, dy=dy, intent="offline movement", thought="Standing still will not teach me anything, so I should scout a little.")
        for dx, dy in [(0, 0), *DIRECTIONS]:
            tx, ty = agent.x + dx, agent.y + dy
            if self.world.in_bounds(tx, ty):
                tile = self.world.tile(tx, ty)
                if tile.feature:
                    feature = FEATURES[tile.feature]
                    if feature.required_tool and not agent.best_tool(feature.required_tool, feature.min_power):
                        continue
                    return Decision("interact", target_dx=dx, target_dy=dy, intent="interact nearby", thought=f"That {feature.name} nearby looks useful enough to check first.")
        for dx, dy in [(0, 0), *DIRECTIONS]:
            tx, ty = agent.x + dx, agent.y + dy
            if self.world.in_bounds(tx, ty) and not self.world.tile(tx, ty).feature:
                return Decision("interact", target_dx=dx, target_dy=dy, intent="gather terrain resource", thought="Even the ground might give me something basic to work with.")
        dx, dy = self.rng.choice(DIRECTIONS)
        return Decision("move", dx=dx, dy=dy, intent="offline movement", thought="I need a better spot before I can make a real plan.")

    @staticmethod
    def _fallback_thought(agent: Agent, decision: Decision) -> str:
        if decision.action == "move":
            return "I need a better nearby resource lead, so I am repositioning instead of standing around."
        if decision.action == "interact":
            return "There is something close enough to check, and guessing from a distance is wasting time."
        if decision.action == "craft":
            return "I have enough pieces for a concrete craft, so this is the right moment to try it."
        if decision.action == "experiment":
            return "These materials might reveal a recipe if I stop overthinking and test them."
        if decision.action == "eat":
            return "My hunger is getting in the way, so eating is the sensible move."
        if decision.action == "talk":
            return "This is worth saying out loud because someone nearby may actually use it."
        return "I need a concrete next step, not a vague plan."

    def _spawn(self, agent_count: int) -> None:
        colors = [
            (232, 97, 92),
            (92, 177, 232),
            (238, 190, 81),
            (157, 111, 232),
            (96, 214, 132),
            (232, 128, 203),
            (245, 139, 74),
            (117, 210, 201),
            (208, 219, 91),
            (176, 143, 104),
        ]
        attempts = 0
        while len(self.agents) < agent_count and attempts < agent_count * 800:
            attempts += 1
            if self.agents and self.rng.random() < 0.72:
                anchor = self.rng.choice(self.agents)
                spread = max(3, CHAT_RADIUS // 2)
                x = anchor.x + self.rng.randint(-spread, spread)
                y = anchor.y + self.rng.randint(-spread, spread)
            else:
                x = self.rng.randrange(2, self.world.width - 2)
                y = self.rng.randrange(2, self.world.height - 2)
            if not (2 <= x < self.world.width - 2 and 2 <= y < self.world.height - 2):
                continue
            dummy = type("SpawnProbe", (), {"inventory": Counter()})()
            if not self.world.can_enter(dummy, x, y):
                continue
            if any(agent.x == x and agent.y == y for agent in self.agents):
                continue
            persona = PERSONAS[len(self.agents) % len(PERSONAS)]
            agent = Agent(len(self.agents), persona, x, y, colors[len(self.agents) % len(colors)])
            if persona.archetype == "builder":
                agent.inventory["stick"] = 2
            elif persona.archetype == "miner":
                agent.inventory["pebble"] = 2
            elif persona.archetype == "provider":
                agent.inventory["stick"] = 1
            elif persona.archetype == "forager":
                agent.inventory["grass_fiber"] = 1
            agent.chat_cooldown = self.rng.randint(2, 9)
            self.agents.append(agent)
        if not self.agents:
            raise RuntimeError("Could not spawn any agents")


def _word_stem(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and len(word) > 4:
        return word[:-1]
    return word


def _sign(value: int) -> int:
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0
