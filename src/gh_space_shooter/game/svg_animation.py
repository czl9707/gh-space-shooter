"""SVG-specific animation frame generators built on top of Animator timelines."""

from typing import Iterator

from .animator import Animator
from .game_state import GameState
from .render_context import RenderContext
from .svg_renderer import SvgRenderer
from .svg_timeline import SvgTimelineFrame, snapshot_svg_timeline_frame


def generate_svg_timeline_frames(
    animator: Animator, max_frames: int | None = None
) -> Iterator[SvgTimelineFrame]:
    """Build object-based SVG timeline snapshots from an animator timeline."""
    for renderer, game_state, elapsed_ms in _iter_svg_timeline(animator, max_frames):
        yield snapshot_svg_timeline_frame(
            game_state,
            width=renderer.width,
            height=renderer.height,
            time_ms=elapsed_ms,
            watermark=animator.watermark,
        )


def _iter_svg_timeline(
    animator: Animator,
    max_frames: int | None,
) -> Iterator[tuple[SvgRenderer, GameState, int]]:
    """Yield renderer and timeline pairs while keeping renderer setup single-sourced."""
    renderer: SvgRenderer | None = None
    for game_state, elapsed_ms in animator.iter_state_timeline(max_frames=max_frames):
        if renderer is None:
            renderer = SvgRenderer(
                game_state,
                RenderContext.darkmode(),
                watermark=animator.watermark,
            )
        yield renderer, game_state, elapsed_ms
