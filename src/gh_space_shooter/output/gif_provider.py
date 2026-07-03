"""GIF output provider."""

from io import BytesIO
from typing import Iterator
from PIL import Image
from .base import OutputProvider


class GifOutputProvider(OutputProvider):
    """Output provider for GIF format."""

    def __init__(self, path: str):
        """
        Initialize the provider with an output file path.

        Args:
            path: Path to the output GIF file
        """
        super().__init__(path)

    def encode(self, frames: Iterator[Image.Image], frame_duration: int) -> bytes:
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
                duration=frame_duration,
                loop=0,
                optimize=True,
            )

        return buffer.getvalue()

    def write(self, data: bytes) -> None:
        """
        Write GIF-encoded data to a file.

        Args:
            data: GIF-encoded bytes to write
        """
        with open(self.path, "wb") as f:
            f.write(data)
