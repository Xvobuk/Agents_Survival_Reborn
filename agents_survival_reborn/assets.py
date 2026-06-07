from __future__ import annotations

import shutil
from pathlib import Path

import pygame

from .constants import DOCS_DIR, SPRITE_DIR
from .data import SpriteSpec, sprite_specs


class AssetManager:
    def __init__(self, *, interactive_wizard: bool = False) -> None:
        self.sprites: dict[str, pygame.Surface] = {}
        self.missing: list[SpriteSpec] = []
        SPRITE_DIR.mkdir(parents=True, exist_ok=True)
        if interactive_wizard:
            self.run_wizard()
        self._load_all()
        self.write_missing_report()

    def get(self, sprite_id: str) -> pygame.Surface:
        return self.sprites.get(sprite_id) or self._placeholder(sprite_id, (32, 32), (130, 130, 130))

    def run_wizard(self) -> None:
        print("Sprite asset wizard. Leave input blank to use a generated placeholder.")
        for spec in sprite_specs():
            target = SPRITE_DIR / spec.path
            if target.exists():
                continue
            answer = input(f"{spec.sprite_id} {spec.size} ({spec.notes}) path> ").strip().strip('"')
            if not answer:
                continue
            source = Path(answer)
            if source.exists() and source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            else:
                print(f"  not found: {source}")

    def _load_all(self) -> None:
        for spec in sprite_specs():
            path = SPRITE_DIR / spec.path
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert_alpha()
                    self.sprites[spec.sprite_id] = pygame.transform.scale(image, spec.size)
                    continue
                except pygame.error:
                    pass
            self.missing.append(spec)
            self.sprites[spec.sprite_id] = self._placeholder(spec.sprite_id, spec.size, self._color_for_kind(spec.kind))

    def write_missing_report(self) -> None:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        report = DOCS_DIR / "missing_sprites.md"
        lines = [
            "# Missing Sprites",
            "",
            "Put PNG files into `assets/sprites` using the exact filenames below.",
            "The game will use placeholders until these files exist.",
            "",
            "| Sprite ID | File | Size | Kind | Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
        for spec in self.missing:
            lines.append(f"| `{spec.sprite_id}` | `{spec.path}` | {spec.size[0]}x{spec.size[1]} | {spec.kind} | {spec.notes} |")
        report.write_text("\n".join(lines), encoding="utf-8")

    def _placeholder(self, label: str, size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        rect = surface.get_rect()
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, (15, 18, 22), rect, 2, border_radius=4)
        inner = rect.inflate(-8, -8)
        pygame.draw.rect(surface, self._lighten(color), inner, border_radius=3)
        font = pygame.font.Font(None, max(12, min(size) // 2))
        letters = "".join(part[0] for part in label.split("_") if part)[:3].upper()
        text = font.render(letters, True, (10, 12, 16))
        surface.blit(text, text.get_rect(center=rect.center))
        return surface

    @staticmethod
    def _color_for_kind(kind: str) -> tuple[int, int, int]:
        return {
            "terrain": (95, 130, 105),
            "feature": (145, 120, 78),
            "agent": (92, 138, 205),
            "item": (156, 141, 86),
            "ui": (88, 96, 112),
        }.get(kind, (130, 130, 130))

    @staticmethod
    def _lighten(color: tuple[int, int, int]) -> tuple[int, int, int]:
        return tuple(min(255, channel + 45) for channel in color)
