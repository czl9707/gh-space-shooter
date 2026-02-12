"""Raster (Pillow) animation frame generators built on top of Animator timelines."""

from typing import Iterator

from PIL import Image

from .animator import Animator
from .render_context import RenderContext
from .renderer import Renderer


def generate_raster_frames(
    animator: Animator, max_frames: int | None = None
) -> Iterator[Image.Image]:
    """Render raster frame payloads from an animator timeline."""
    renderer: Renderer | None = None
    for game_state, _elapsed_ms in animator.iter_state_timeline(max_frames=max_frames):
        if renderer is None:
            renderer = Renderer(
                game_state,
                RenderContext.darkmode(),
                watermark=animator.watermark,
            )
        yield renderer.render_frame()
