"""Power-up objects."""

from abc import ABC, abstractmethod # Import ABC and abstractmethod
from typing import TYPE_CHECKING

from PIL import ImageDraw

from .drawable import Drawable
from ...constants import POWER_UP_SPEED, POWER_UP_COLORS, SHIP_POSITION_Y, RAPID_FIRE_DURATION # Import RAPID_FIRE_DURATION


if TYPE_CHECKING:
    from ..game_state import GameState
    from ..render_context import RenderContext
    from .ship import Ship # Import Ship for type hinting


class PowerUp(Drawable, ABC): # Inherit from ABC
    """Base class for power-up objects."""

    def __init__(self, x: float, y: float, power_up_type: str, game_state: "GameState"):
        self.x = x
        self.y = y
        self.power_up_type = power_up_type
        self.game_state = game_state
        self.speed = POWER_UP_SPEED # Power-ups move downwards

    def animate(self, delta_time: float) -> None:
        """Update power-up position."""
        self.y += self.speed * delta_time

        # Remove if off-screen
        if self.y > SHIP_POSITION_Y + 5: # A bit below ship position
            self.game_state.power_ups.remove(self) # Assuming power_ups list in game_state

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the power-up."""
        x_pixel, y_pixel = context.get_cell_position(self.x, self.y)
        size = context.cell_size * 0.7

        color = POWER_UP_COLORS.get(self.power_up_type, (255, 255, 255)) # Default white if type not found

        draw.rectangle(
            [x_pixel, y_pixel, x_pixel + size, y_pixel + size],
            fill=color,
            outline=(255, 255, 255),
            width=1
        )
    
    @abstractmethod
    def activate_effect(self, ship: "Ship") -> None:
        """Activate the power-up's effect on the ship."""
        pass


class RapidFirePowerUp(PowerUp):
    """Rapid fire power-up."""

    def __init__(self, x: float, y: float, game_state: "GameState"):
        super().__init__(x, y, "rapid_fire", game_state)
    
    def activate_effect(self, ship: "Ship") -> None:
        """Activate rapid fire effect on the ship."""
        ship.is_rapid_fire_active = True
        ship.rapid_fire_duration_remaining = RAPID_FIRE_DURATION
