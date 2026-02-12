"""GIF output provider."""

from .base import PillowSequenceOutputProvider


class GifOutputProvider(PillowSequenceOutputProvider):
    """Output provider for GIF format."""

    @property
    def output_format(self) -> str:
        return "gif"

    @property
    def save_options(self) -> dict[str, object]:
        return {"optimize": False}
