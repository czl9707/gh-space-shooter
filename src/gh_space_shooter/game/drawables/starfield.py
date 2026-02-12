"""Animated starfield background."""

import random
from typing import TYPE_CHECKING, TypedDict

from PIL import ImageDraw

from ...constants import NUM_WEEKS, SHIP_POSITION_Y, STAR_SPEED_MIN, STAR_SPEED_MAX
from .drawable import Drawable

if TYPE_CHECKING:
    from ..render_context import RenderContext

class Star(TypedDict):
    id: int
    x: float
    y: float
    brightness: float
    size: int
    speed: float


class Starfield(Drawable):
    """Animated starfield background with slowly moving stars."""

    def __init__(self, rng: random.Random | None = None) -> None:
        """Initialize the starfield with random stars."""
        self.rng = rng or random.Random()
        self.spawn_top = -3
        self.stars: list[Star] = []
        # Generate about 100 stars across the play area
        for star_id in range(100):
            # Random position across the entire grid area
            x = self.rng.uniform(-2, NUM_WEEKS + 2)
            y = self.rng.uniform(self.spawn_top, SHIP_POSITION_Y + 4)
            # Brightness: 0.2 to 1.0 (dimmer stars for depth)
            brightness = self.rng.uniform(0.2, 1.0)
            # Size: 1-2 pixels
            size = self.rng.choice([1, 1, 1, 2])  # More 1-pixel stars
            # Speed: slower for dimmer (farther) stars (in cells per second)
            speed = STAR_SPEED_MIN + (brightness * (STAR_SPEED_MAX - STAR_SPEED_MIN))
            self.stars.append(
                {
                    "id": star_id,
                    "x": x,
                    "y": y,
                    "brightness": brightness,
                    "size": size,
                    "speed": speed,
                }
            )

    def animate(self, delta_time: float) -> None:
        """Move stars downward, wrapping around when they go off screen.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        for star in self.stars:
            star["y"] += star["speed"] * delta_time

            # Wrap around: if star goes below the screen, move it back to the top
            if star["y"] > SHIP_POSITION_Y + 4:
                # Start slightly above viewport so stars enter from the top edge.
                star["y"] = self.spawn_top
                # Randomize x position when wrapping for variety
                star["x"] = self.rng.uniform(-2, NUM_WEEKS + 2)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw all stars at their current positions."""
        for star in self.stars:
            star_x = star["x"]
            star_y = star["y"]
            brightness = star["brightness"]
            size = star["size"]
            # Convert grid position to pixel position
            x, y = context.get_cell_position(star_x, star_y)

            # Calculate star color (white with varying brightness)
            star_brightness = int(255 * brightness)
            star_color = (star_brightness, star_brightness, star_brightness, 255)

            # Draw star as a small rectangle or point
            if size == 1:
                # Single pixel star
                draw.point([(x, y)], fill=star_color)
            else:
                # Slightly larger star (2x2)
                draw.rectangle(
                    [x, y, x + size - 1, y + size - 1],
                    fill=star_color
                )
