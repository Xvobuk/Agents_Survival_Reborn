from __future__ import annotations

import re
from collections import Counter, deque
from dataclasses import dataclass, field

from .constants import HEARD_MEMORY_LIMIT, INVENTORY_SLOT_LIMIT, PRIVATE_MEMORY_LIMIT
from .data import AGENT_SPRITES, ITEMS, item_name


FORBIDDEN_CHAT_WORDS = {
    "ai",
    "bot",
    "llm",
    "model",
    "prompt",
    "schema",
    "npc",
    "simulation",
}

REPEATED_CHAT_THRESHOLD = 0.72
REPEATED_MEMORY_THRESHOLD = 0.82
RECENT_ACTION_LIMIT = 14
RECENT_SPEECH_LIMIT = 8
RECENT_THOUGHT_LIMIT = 10


@dataclass(frozen=True)
class Persona:
    name: str
    origin: str
    archetype: str
    long_goal: str
    temperament: str
    social_style: str
    sprite: str


PERSONAS: tuple[Persona, ...] = (
    Persona("Aiden", "ex-carpenter from a rainy northern port", "builder", "build the strongest base and unlock every station", "patient, practical, dry humor", "brief, helpful only when it matters", AGENT_SPRITES[0]),
    Persona("Mira", "prospector raised around abandoned mines", "miner", "reach metal tools before everyone else", "focused, stubborn, quiet", "rare direct questions about mining and tool recipes", AGENT_SPRITES[1]),
    Persona("Noah", "coastal fisher who trusts food security first", "provider", "control fishing and keep a food surplus", "calm, generous, observant", "warm but not noisy; trades food for materials", AGENT_SPRITES[2]),
    Persona("Ivy", "restless mapmaker from a caravan family", "explorer", "find rare biomes, caves, and routes", "curious, impatient, wry", "asks about landmarks and shares discoveries sparingly", AGENT_SPRITES[3]),
    Persona("Leo", "herbalist used to surviving alone", "forager", "discover plant uses and bootstrap early crafting", "careful, kind, risk-aware", "asks crafting questions only when blocked", AGENT_SPRITES[4]),
    Persona("Zara", "competitive speedrunner type", "solo", "out-progress everyone without giving too much away", "guarded, efficient, slightly smug", "vague unless cooperation gives an advantage", AGENT_SPRITES[5]),
    Persona("Owen", "market-town trader dropped into the wild", "trader", "become useful through trade and recipe knowledge", "social, opportunistic, upbeat", "natural conversation, trades, occasional jokes", AGENT_SPRITES[6]),
    Persona("Nia", "systems-minded survival optimizer", "minmaxer", "climb the tech tree with minimal wasted turns", "analytical, blunt, low patience", "mostly silent; direct blocked-craft questions", AGENT_SPRITES[7]),
    Persona("Caleb", "former camp cook who thinks in supplies and morale", "cook", "secure cooked food and keep a shared camp alive", "steady, warm, pragmatic", "offers food help, asks practical questions, light humor when safe", AGENT_SPRITES[2]),
    Persona("Sera", "wandering tinkerer who learns by taking things apart", "tinkerer", "discover utility recipes and build clever tool chains", "inventive, restless, a little cryptic", "asks specific recipe questions and trades odd materials", AGENT_SPRITES[6]),
)


@dataclass
class ChatMessage:
    round_index: int
    speaker: str
    text: str
    x: int
    y: int


@dataclass
class Agent:
    agent_id: int
    persona: Persona
    x: int
    y: int
    color: tuple[int, int, int]
    facing: tuple[int, int] = (0, 1)
    start_x: int = 0
    start_y: int = 0
    start_facing: tuple[int, int] = (0, 1)
    inventory: Counter[str] = field(default_factory=Counter)
    tool_durability: dict[str, int] = field(default_factory=dict)
    known_recipes: set[str] = field(default_factory=set)
    private_memory: deque[str] = field(default_factory=lambda: deque(maxlen=PRIVATE_MEMORY_LIMIT))
    heard_messages: deque[ChatMessage] = field(default_factory=lambda: deque(maxlen=HEARD_MEMORY_LIMIT))
    recent_actions: deque[str] = field(default_factory=lambda: deque(maxlen=RECENT_ACTION_LIMIT))
    recent_speech: deque[str] = field(default_factory=lambda: deque(maxlen=RECENT_SPEECH_LIMIT))
    recent_thoughts: deque[str] = field(default_factory=lambda: deque(maxlen=RECENT_THOUGHT_LIMIT))
    health: float = 100.0
    hunger: float = 90.0
    energy: float = 100.0
    chat_cooldown: int = 0
    last_action: str = "looking around"
    last_intent: str = "survive"
    last_thought: str = "I need to get oriented and find something useful."
    last_private_note: str = ""
    last_seen_chat_round: int = -1
    inventory_slot_limit: int = INVENTORY_SLOT_LIMIT

    @property
    def name(self) -> str:
        return self.persona.name

    @property
    def sprite(self) -> str:
        return self.persona.sprite

    def mark_animation_start(self) -> None:
        self.start_x = self.x
        self.start_y = self.y
        self.start_facing = self.facing

    def add_items(self, items: Counter[str] | dict[str, int]) -> Counter[str]:
        accepted: Counter[str] = Counter()
        for item_id, count in items.items():
            if count <= 0:
                continue
            if item_id not in self.inventory and self.used_inventory_slots >= self.inventory_slot_limit:
                continue
            item = ITEMS[item_id]
            current = self.inventory.get(item_id, 0)
            room = max(0, item.max_stack - current)
            take = min(count, room)
            if take <= 0:
                continue
            self.inventory[item_id] += take
            accepted[item_id] += take
        return accepted

    @property
    def used_inventory_slots(self) -> int:
        return sum(1 for count in self.inventory.values() if count > 0)

    @property
    def free_inventory_slots(self) -> int:
        return max(0, self.inventory_slot_limit - self.used_inventory_slots)

    def can_accept_item(self, item_id: str, count: int = 1) -> bool:
        if count <= 0:
            return True
        if item_id in self.inventory:
            return self.inventory[item_id] + count <= ITEMS[item_id].max_stack
        return self.used_inventory_slots < self.inventory_slot_limit and count <= ITEMS[item_id].max_stack

    def best_tool(self, tag: str, power: int = 1) -> str | None:
        best: tuple[int, int, str] | None = None
        for item_id, count in self.inventory.items():
            if count <= 0:
                continue
            item = ITEMS[item_id]
            if tag not in item.tool_tags or item.tool_power < power:
                continue
            durability = self.tool_durability.get(item_id, item.durability)
            if durability <= 0:
                continue
            candidate = (item.tool_power, durability, item_id)
            if best is None or candidate > best:
                best = candidate
        return best[2] if best else None

    def remember(self, note: str) -> None:
        note = clean_inner_text(note, 180)
        if note:
            normalized = _normalize_chat(note)
            for existing in self.private_memory:
                if _similarity(normalized, _normalize_chat(existing)) >= REPEATED_MEMORY_THRESHOLD:
                    return
            self.private_memory.append(note[:180])
            self.last_private_note = note[:180]

    def record_action(self, round_index: int, action: str, intent: str) -> None:
        action = action.strip()
        intent = intent.strip()
        if action:
            detail = f"r{round_index}: {action}"
            if intent:
                detail += f" | intent: {intent}"
            self.recent_actions.append(detail[:220])

    def record_speech(self, round_index: int, speech: str) -> None:
        speech = clean_chat(speech)
        if speech:
            self.recent_speech.append(f"r{round_index}: {speech}"[:220])

    def record_thought(self, round_index: int, thought: str) -> None:
        thought = clean_inner_text(thought, 260)
        if not thought:
            return
        self.last_thought = thought
        self.recent_thoughts.append(f"r{round_index}: {thought}"[:300])

    def recently_said_similar(self, speech: str) -> bool:
        normalized = _normalize_chat(speech)
        if not normalized:
            return True
        for recent in self.recent_speech:
            if _similarity(normalized, _normalize_chat(recent)) >= REPEATED_CHAT_THRESHOLD:
                return True
        return False

    def hear(self, message: ChatMessage) -> None:
        if message.speaker != self.name:
            self.heard_messages.append(message)

    def tick_needs(self) -> None:
        self.hunger = max(0.0, self.hunger - 0.16)
        self.energy = min(100.0, self.energy + 0.25)
        if self.chat_cooldown:
            self.chat_cooldown -= 1
        if self.hunger <= 0:
            self.health = max(0.0, self.health - 0.7)
        elif self.hunger > 70:
            self.health = min(100.0, self.health + 0.03)

    def eat_best_food(self, *, target_hunger: float = 88.0) -> str | None:
        best: tuple[float, int, str] | None = None
        for item_id, count in self.inventory.items():
            if count <= 0:
                continue
            item = ITEMS[item_id]
            food = item.food
            if food <= 0:
                continue
            waste = max(0.0, self.hunger + food - target_hunger)
            raw_penalty = 5.0 if "raw" in item.tags else 0.0
            medicine_bonus = 2.0 if "medicine" in item.tags and self.health < 75 else 0.0
            cooked_bonus = 3.0 if "cooked" in item.tags else 0.0
            score = food - waste * 0.7 - raw_penalty + medicine_bonus + cooked_bonus
            if best is None or (score, food, item_id) > best:
                best = (score, food, item_id)
        if not best:
            return None
        _score, food, item_id = best
        item = ITEMS[item_id]
        self.inventory[item_id] -= 1
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        self.hunger = min(100.0, self.hunger + food)
        if "raw" in item.tags:
            self.health = max(0.0, self.health - 2.0)
            self.energy = max(0.0, self.energy - 1.0)
            return f"{item_name(item_id)} (+{food} food, raw)"
        if "cooked" in item.tags:
            self.health = min(100.0, self.health + 1.0)
            self.energy = min(100.0, self.energy + 1.5)
        return f"{item_name(item_id)} (+{food} food)"


def clean_chat(text: str) -> str:
    text = text.translate(str.maketrans({"’": "'", "“": '"', "”": '"', "—": "-", "–": "-"}))
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"^(hey|hi|hello)( there| everyone| folks)?[!,.]\s*", "", text, flags=re.IGNORECASE)
    if text:
        text = text[0].upper() + text[1:]
    if not text:
        return ""
    if any(ord(char) > 127 for char in text):
        return ""
    words = set(re.findall(r"[a-z0-9_]+", text.lower()))
    if words & FORBIDDEN_CHAT_WORDS:
        return ""
    return text[:180]


def clean_inner_text(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    return text[:limit]


def _normalize_chat(text: str) -> str:
    text = re.sub(r"^r\d+:\s*", "", text.lower().strip())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _similarity(left: str, right: str) -> float:
    left_words = set(left.split())
    right_words = set(right.split())
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / len(left_words | right_words)
