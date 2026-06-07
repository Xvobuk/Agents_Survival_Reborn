from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pygame


class VideoRecorder:
    def __init__(self, output_dir: Path, *, fps: int, size: tuple[int, int], enabled: bool) -> None:
        self.output_dir = output_dir
        self.fps = fps
        self.size = size
        self.enabled = enabled
        self.writer = None
        self.path: Path | None = None
        self.frames = 0
        self.status = "off"
        self._np = None
        output_dir.mkdir(parents=True, exist_ok=True)
        if enabled:
            self.start()

    def start(self) -> None:
        if self.writer:
            self.enabled = True
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = self.output_dir / f"reborn_{stamp}.mp4"
        try:
            import imageio.v2 as imageio
            import numpy as np

            self._np = np
            self.writer = imageio.get_writer(self.path, fps=self.fps, codec="libx264", quality=7, macro_block_size=1)
            self.status = f"recording {self.path.name}"
        except Exception as exc:
            self.status = f"recording unavailable: {exc.__class__.__name__}"
        self.enabled = True

    def capture(self, surface: pygame.Surface) -> None:
        if not self.enabled or not self.writer:
            return
        if surface.get_size() != self.size:
            surface = pygame.transform.smoothscale(surface, self.size)
        pixels = pygame.surfarray.array3d(surface)
        frame = self._np.transpose(pixels, (1, 0, 2))
        self.writer.append_data(frame)
        self.frames += 1

    def toggle(self) -> None:
        self.enabled = not self.enabled
        if self.enabled and not self.writer:
            self.start()
        if not self.enabled:
            self.status = "paused"

    def close(self) -> None:
        if self.writer:
            self.writer.close()
            self.writer = None
            self.status = f"saved {self.path.name if self.path else 'video'}"
