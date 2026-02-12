"""Base class for output format providers."""

from io import BytesIO
from abc import ABC, abstractmethod
from typing import Generic, Iterator, TypeVar

from PIL import Image

FrameT = TypeVar("FrameT")


class OutputProvider(ABC, Generic[FrameT]):
    """Abstract base class for output format providers."""

    def __init__(self, path: str = ""):
        """
        Initialize the provider with an output file path.

        Args:
            path: Path to the output file
        """
        self.path = path

    @abstractmethod
    def encode(self, frames: Iterator[FrameT], frame_duration: int) -> bytes:
        """
        Encode frames into the output format.

        Args:
            frames: Iterator of frame payloads consumed by this provider
            frame_duration: Frame duration in milliseconds

        Returns:
            Encoded output as bytes
        """
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        """
        Write encoded data to a file.

        Args:
            data: Encoded data to write
        """
        if not self.path:
             raise ValueError("Output path not set")
        with open(self.path, "wb") as f:
            f.write(data)


class PillowSequenceOutputProvider(OutputProvider[Image.Image], ABC):
    """Template output provider for Pillow-supported animated image formats."""

    @property
    @abstractmethod
    def output_format(self) -> str:
        """Pillow format identifier (for example, ``gif`` or ``webp``)."""
        raise NotImplementedError

    def encode(self, frames: Iterator[Image.Image], frame_duration: int) -> bytes:
        frame_list = list(frames)
        if not frame_list:
            return b""

        buffer = BytesIO()
        frame_list[0].save(
            buffer,
            format=self.output_format,
            save_all=True,
            append_images=frame_list[1:],
            duration=frame_duration,
            loop=0,
            **self.save_options,
        )
        return buffer.getvalue()

    @property
    def save_options(self) -> dict[str, object]:
        """Additional Pillow ``save`` kwargs for this format."""
        return {}
