"""Player ship object."""

from typing import TYPE_CHECKING, List # Import List

from PIL import ImageDraw

from ...constants import SHIP_POSITION_Y, SHIP_SPEED, SHIP_MAX_HEALTH, RAPID_FIRE_DURATION # Import RAPID_FIRE_DURATION
from .drawable import Drawable
from .explosion import Explosion # Import Explosion
from .power_up import PowerUp # Import PowerUp


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
        self.health = SHIP_MAX_HEALTH # Ship's health
        self.is_destroyed = False # Flag if ship is destroyed
        self.is_rapid_fire_active = False # Rapid fire power-up status
        self.rapid_fire_duration_remaining = 0.0 # Time left for rapid fire

    def take_damage(self) -> None:
        """Ship takes 1 damage."""
        if not self.is_destroyed:
            self.health -= 1
            if self.health <= 0:
                self.is_destroyed = True
                # Create large explosion when ship is destroyed
                explosion = Explosion(self.x, SHIP_POSITION_Y, "large", self.game_state)
                self.game_state.explosions.append(explosion)

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
        """Check if ship can shoot (cooldown has finished or rapid fire active)."""
        if self.is_rapid_fire_active:
            return True # Always can shoot if rapid fire is active
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
        
        # Decrement rapid fire duration
        if self.is_rapid_fire_active:
            self.rapid_fire_duration_remaining -= delta_time
            if self.rapid_fire_duration_remaining <= 0:
                self.is_rapid_fire_active = False # Deactivate rapid fire
        
        # Check for power-up collisions
        collected_power_up = self._check_power_up_collision()
        if collected_power_up:
            collected_power_up.activate_effect(self) # PowerUp activates its effect on the ship

    def _check_power_up_collision(self) -> "PowerUp | None":
        """Check if ship has collided with a power-up."""
        for power_up in self.game_state.power_ups:
            # Simple collision: if ship and power-up are in the same (integer) x cell
            # and power-up is at or below ship's y position
            if int(self.x) == int(power_up.x) and power_up.y >= SHIP_POSITION_Y:
                self.game_state.power_ups.remove(power_up)
                return power_up
        return None

    def _check_power_up_collision(self) -> "PowerUp | None":
        """Check if ship has collided with a power-up."""
        for power_up in self.game_state.power_ups:
            # Simple collision: if ship and power-up are in the same (integer) x cell
            # and power-up is at or below ship's y position
            if int(self.x) == int(power_up.x) and power_up.y >= SHIP_POSITION_Y:
                self.game_state.power_ups.remove(power_up)
                return power_up
        return None

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
