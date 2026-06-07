from __future__ import annotations

from collections import Counter

from .data import ITEMS


def parse_start_items(raw: str) -> Counter[str]:
    items: Counter[str] = Counter()
    if not raw.strip():
        return items
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(f"Invalid start item entry '{chunk}'. Use item_id=count.")
        item_id, count_text = (part.strip() for part in chunk.split("=", 1))
        if item_id not in ITEMS:
            raise ValueError(f"Unknown start item '{item_id}'.")
        try:
            count = int(count_text)
        except ValueError as exc:
            raise ValueError(f"Invalid count for start item '{item_id}': {count_text}") from exc
        if count < 0:
            raise ValueError(f"Invalid count for start item '{item_id}': {count}")
        if count:
            items[item_id] += count
    return items
