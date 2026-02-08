"""Output providers for different animation formats."""

from .base import OutputProvider
from .gif_provider import GifOutputProvider

__all__ = ["OutputProvider", "GifOutputProvider"]
