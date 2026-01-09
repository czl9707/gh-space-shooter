"""Enemy objects representing contribution graph data."""

from typing import TYPE_CHECKING

from PIL import ImageDraw

from .drawable import Drawable
from .explosion import Explosion

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..render_context import RenderContext


class Enemy(Drawable):
    """Represents an enemy at a specific position."""

    def __init__(self, x: int, y: int, health: int, game_state: "GameState"):
        """
        Initialize an enemy.

        Args:
            x: Week position in contribution grid (0-51)
            y: Day position in contribution grid (0-6, Sun-Sat)
            health: Initial health/lives (1-4)
            game_state: Reference to game state for self-removal when destroyed
        """
        self.x = x
        self.y = y
        self.health = health
        self.game_state = game_state

    def take_damage(self) -> None:
        """
        Enemy takes 1 damage and removes itself from game if destroyed.
        Creates a large explosion when destroyed.
        """
        self.health -= 1
        if self.health <= 0:
            # Create large explosion with green color (enemy color)
            explosion = Explosion(self.x, self.y, "large", self.game_state)
            self.game_state.explosions.append(explosion)
            self.game_state.enemies.remove(self)

    def animate(self, delta_time: float) -> None:
        """Update enemy state for next frame (enemies don't animate currently)."""
        pass

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the enemy at its position with rounded corners."""
        x, y = context.get_cell_position(self.x, self.y)
        color = context.enemy_colors.get(self.health, context.enemy_colors[1])

        draw.rounded_rectangle(
            [x, y, x + context.cell_size, y + context.cell_size],
            radius=2,
            fill=color,
        )
