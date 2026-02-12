"""WebP output provider."""

from .base import PillowSequenceOutputProvider


class WebPOutputProvider(PillowSequenceOutputProvider):
    """Output provider for WebP format."""

    @property
    def output_format(self) -> str:
        return "webp"

    @property
    def save_options(self) -> dict[str, object]:
        return {
            "lossless": True,
            "quality": 100,
            "method": 4,
        }
