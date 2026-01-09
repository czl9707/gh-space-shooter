"""Base Drawable interface for game objects."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PIL import ImageDraw

if TYPE_CHECKING:
    from .render_context import RenderContext


class Drawable(ABC):
    """Interface for objects that can be animated and drawn."""

    @abstractmethod
    def animate(self, delta_time: float) -> None:
        """Update the object's state for the next animation frame.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        pass

    @abstractmethod
    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """
        Draw the object on the image.

        Args:
            draw: PIL ImageDraw object
            context: Rendering context with helper functions and constants
        """
        pass
