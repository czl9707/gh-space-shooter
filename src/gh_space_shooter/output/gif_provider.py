"""GIF output provider."""

from io import BytesIO
from typing import Iterator
from PIL import Image
from .base import OutputProvider


class GifOutputProvider(OutputProvider):
    """Output provider for GIF format."""

    def encode(self, frames: Iterator[Image.Image]) -> bytes:
        """
        Encode frames as animated GIF.

        Args:
            frames: Iterator of PIL Images

        Returns:
            GIF-encoded bytes
        """
        frame_list = list(frames)
        buffer = BytesIO()

        if frame_list:
            frame_list[0].save(
                buffer,
                format="gif",
                save_all=True,
                append_images=frame_list[1:],
                duration=self.frame_duration,
                loop=0,
                optimize=False,
            )

        return buffer.getvalue()
