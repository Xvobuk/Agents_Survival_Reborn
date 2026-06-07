from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
import pygame


@dataclass(frozen=True)
class ChromaStats:
    removed_pixels: int
    replaced_pixels: int
    remaining_magenta_pixels: int


def remove_magenta_background(surface: pygame.Surface) -> tuple[pygame.Surface, ChromaStats]:
    rgb = pygame.surfarray.array3d(surface)
    alpha = _surface_alpha(surface, rgb.shape[:2])
    candidates = _magenta_candidates(rgb, alpha)
    connected = _border_connected(alpha <= 8, candidates)
    remove = (connected & candidates) | _hot_magenta_pixels(rgb, alpha)
    alpha[remove] = 0
    _paint_transparent_pixels(rgb, alpha)
    result = _surface_from_arrays(rgb, alpha)
    remaining = int((_magenta_candidates(rgb, alpha) & (alpha > 0)).sum())
    return result, ChromaStats(int(remove.sum()), 0, remaining)


def clean_sprite_surface(surface: pygame.Surface, *, preserve_opaque: bool = False) -> tuple[pygame.Surface, ChromaStats]:
    rgb = pygame.surfarray.array3d(surface)
    alpha = _surface_alpha(surface, rgb.shape[:2])
    candidates = _magenta_candidates(rgb, alpha)
    if preserve_opaque:
        replace = candidates & (alpha > 0)
        if replace.any():
            fill = _average_visible_color(rgb, alpha, ~replace)
            rgb[replace] = fill
        alpha[:, :] = 255
        remaining = int((_magenta_candidates(rgb, alpha) & (alpha > 0)).sum())
        return _surface_from_arrays(rgb, alpha), ChromaStats(0, int(replace.sum()), remaining)

    connected = _border_connected(alpha <= 8, candidates)
    remove = (connected & candidates) | _hot_magenta_pixels(rgb, alpha)
    alpha[remove] = 0
    _paint_transparent_pixels(rgb, alpha)
    remaining = int((_magenta_candidates(rgb, alpha) & (alpha > 0)).sum())
    return _surface_from_arrays(rgb, alpha), ChromaStats(int(remove.sum()), 0, remaining)


def _surface_alpha(surface: pygame.Surface, shape: tuple[int, int]) -> np.ndarray:
    try:
        return pygame.surfarray.array_alpha(surface).copy()
    except ValueError:
        return np.full(shape, 255, dtype=np.uint8)


def _magenta_candidates(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    visible = alpha > 0
    hot_key = (r > 210) & (b > 190) & (g < 125) & (r - g > 75) & (b - g > 75)
    spill = (r > 145) & (b > 135) & (g < 100) & (r - g > 68) & (b - g > 62) & (np.abs(r - b) < 105)
    return visible & (hot_key | spill)


def _hot_magenta_pixels(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    return (alpha > 0) & (r > 135) & (b > 135) & (g < 45) & (r - g > 90) & (b - g > 90) & (np.abs(r - b) < 120)


def _border_connected(transparent: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    passable = transparent | candidates
    width, height = passable.shape
    connected = np.zeros_like(passable, dtype=bool)
    queue: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        if passable[x, y] and not connected[x, y]:
            connected[x, y] = True
            queue.append((x, y))

    for x in range(width):
        push(x, 0)
        push(x, height - 1)
    for y in range(height):
        push(0, y)
        push(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx in (x - 1, x, x + 1):
            for ny in (y - 1, y, y + 1):
                if (nx != x or ny != y) and 0 <= nx < width and 0 <= ny < height:
                    push(nx, ny)
    return connected


def _paint_transparent_pixels(rgb: np.ndarray, alpha: np.ndarray) -> None:
    transparent = alpha <= 8
    if transparent.any():
        rgb[transparent] = _average_visible_color(rgb, alpha, np.ones(alpha.shape, dtype=bool))


def _average_visible_color(rgb: np.ndarray, alpha: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    visible = (alpha > 8) & allowed
    if visible.any():
        return rgb[visible].mean(axis=0).astype(np.uint8)
    return np.array([32, 34, 38], dtype=np.uint8)


def _surface_from_arrays(rgb: np.ndarray, alpha: np.ndarray) -> pygame.Surface:
    result = pygame.Surface(rgb.shape[:2], pygame.SRCALPHA)
    pygame.surfarray.blit_array(result, rgb)
    pygame.surfarray.pixels_alpha(result)[:, :] = alpha
    return result
