"""Boss bullet objects."""

from typing import TYPE_CHECKING

from PIL import ImageDraw

from .bullet import Bullet
from .explosion import Explosion # Import Explosion
from .ship import Ship # Import Ship
from ...constants import BULLET_SPEED, BOSS_BULLET_COLOR, SHIP_POSITION_Y


if TYPE_CHECKING:
    from ..game_state import GameState
    from ..render_context import RenderContext


class BossBullet(Bullet):
    """Represents a bullet fired by the boss."""

    def __init__(self, x: float, y: float, game_state: "GameState"):
        super().__init__(x=x, game_state=game_state)
        self.y = y # Boss bullets start at boss's y position
        self.speed = BULLET_SPEED # Boss bullets move downwards (positive speed means increasing Y)
    
    def _check_collision_with_ship(self) -> bool:
        """Check if boss bullet has hit the ship."""
        ship = self.game_state.ship
        # Simple collision: if bullet and ship are in the same (integer) x cell
        # and bullet is at or below ship's y position
        return int(self.x) == int(ship.x) and self.y >= SHIP_POSITION_Y

    def animate(self, delta_time: float) -> None:
        """Update bullet position, check for collisions with ship, and remove on hit."""
        self.y += self.speed * delta_time # Moves downwards

        if self._check_collision_with_ship():
            explosion = Explosion(self.x, self.y, "small", self.game_state)
            self.game_state.explosions.append(explosion)
            self.game_state.ship.take_damage() # Ship takes damage
            self.game_state.bullets.remove(self)
        
        # Remove bullet if it goes off-screen (below the ship)
        if self.y > SHIP_POSITION_Y + 5: # +5 for a larger buffer below ship
            self.game_state.bullets.remove(self)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the bullet at its position with a distinct color and size."""
        x, y = context.get_cell_position(self.x, self.y)
        
        # Draw a larger bullet for the boss
        bullet_size = context.cell_size * 0.5
        draw.rectangle(
            [x - bullet_size / 2, y - bullet_size / 2, x + bullet_size / 2, y + bullet_size / 2],
            fill=BOSS_BULLET_COLOR,
        )

