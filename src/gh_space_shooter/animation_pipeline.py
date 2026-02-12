"""Shared animation orchestration used by CLI and web app entry points."""

from pathlib import Path
from typing import Any, Iterator

from .game.animator import Animator
from .game.raster_animation import generate_raster_frames
from .game.strategies.base_strategy import BaseStrategy
from .game.svg_animation import generate_svg_timeline_frames
from .github_client import ContributionData
from .output import resolve_output_provider
from .output.base import OutputProvider


def build_frame_stream(
    animator: Animator,
    file_extension: str,
    max_frames: int | None,
) -> Iterator[Any]:
    """Build the frame stream matching the target output extension."""
    if file_extension == ".svg":
        return generate_svg_timeline_frames(animator, max_frames)
    return generate_raster_frames(animator, max_frames)


def encode_animation(
    data: ContributionData,
    strategy: BaseStrategy,
    output_path: str,
    *,
    fps: int,
    watermark: bool,
    max_frames: int | None,
    provider: OutputProvider[Any] | None = None,
) -> bytes:
    """Encode animation bytes for the given strategy and output path."""
    file_extension = Path(output_path).suffix.lower()
    target_provider = provider or resolve_output_provider(output_path)
    animator = Animator(data, strategy, fps=fps, watermark=watermark)
    frame_stream = build_frame_stream(animator, file_extension, max_frames)
    return target_provider.encode(frame_stream, frame_duration=1000 // fps)
