"""Player ship object."""

from typing import TYPE_CHECKING

from PIL import ImageDraw

from ...constants import SHIP_POSITION_Y, SHIP_SPEED
from .drawable import Drawable

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..render_context import RenderContext


class Ship(Drawable):
    """Represents the player's ship."""

    def __init__(self, game_state: "GameState"):
        """Initialize the ship at starting position."""
        self.x: float = 25  # Start middle of screen
        self.target_x = self.x
        self.shoot_cooldown = 0.0  # Seconds until ship can shoot again
        self.game_state = game_state

    def move_to(self, x: int):
        """
        Move ship to a new x position.

        Args:
            x: Target x position
        """
        self.target_x = x

    def is_moving(self) -> bool:
        """Check if ship is moving to a new position."""
        return self.x != self.target_x

    def can_shoot(self) -> bool:
        """Check if ship can shoot (cooldown has finished)."""
        return self.shoot_cooldown <= 0

    def animate(self, delta_time: float) -> None:
        """Update ship position, moving toward target at constant speed.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        delta_x = SHIP_SPEED * delta_time
        if self.x < self.target_x:
            self.x = min(self.x + delta_x, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - delta_x, self.target_x)

        # Decrement shoot cooldown (scaled by delta_time)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= delta_time

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw a simple Galaga-style ship."""
        x, y = context.get_cell_position(self.x, SHIP_POSITION_Y)

        # Calculate ship dimensions
        center_x = x + context.cell_size // 2
        height = context.cell_size
        wing_width = 8

        # Draw left wing
        draw.polygon(
            [
                (center_x - 2, y + height * 0.5),
                (center_x - wing_width, y + height * 0.8),
                (center_x - wing_width, y + height * 1),
                (center_x - 2, y + height * 0.7),
            ],
            fill=(*context.ship_color, 128)
        )
        draw.rectangle(
            [
                center_x - wing_width - 1, y + height * 0.5,
                center_x - wing_width, y + height * 1, 
            ],
            fill=context.ship_color
        )

        # Draw right wing
        draw.polygon(
            [
                (center_x + 2, y + height * 0.5),
                (center_x + wing_width, y + height * 0.8),
                (center_x + wing_width, y + height * 1),
                (center_x + 2, y + height * 0.7),
            ],
            fill=(*context.ship_color, 128)
        )
        draw.rectangle(
            [
                center_x + wing_width, y + height * 0.5, 
                center_x + wing_width + 1, y + height * 1
            ],
            fill=context.ship_color
        )


        draw.polygon(
            [
                (center_x, y),
                (center_x - 3, y + height * 0.7),
                (center_x, y + height),
                (center_x + 3, y + height * 0.7),
            ],
            fill=context.ship_color
        )
