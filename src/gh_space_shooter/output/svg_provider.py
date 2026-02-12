"""SVG output provider."""

from typing import Iterator

from ..game.svg_timeline import SvgTimelineFrame
from ._svg_timeline_encoder import encode_svg_timeline_sequence
from .base import OutputProvider


class SvgOutputProvider(OutputProvider[SvgTimelineFrame]):
    """Output provider for animated timeline SVG format."""

    def encode(self, frames: Iterator[SvgTimelineFrame], frame_duration: int) -> bytes:
        frame_list = list(frames)
        if not frame_list:
            return b""

        for index, frame in enumerate(frame_list):
            if isinstance(frame, SvgTimelineFrame):
                continue
            raise TypeError(
                "SVG output only supports timeline frames "
                f"(got {type(frame).__name__} at index {index})"
            )

        return encode_svg_timeline_sequence(frame_list, max(1, frame_duration))
