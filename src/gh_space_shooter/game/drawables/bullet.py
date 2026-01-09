"""Bullet objects fired by the ship."""

from typing import TYPE_CHECKING

from PIL import ImageDraw

from ...constants import BULLET_SPEED, BULLET_TRAILING_LENGTH, BULLET_TRAIL_SPACING, SHIP_POSITION_Y
from .drawable import Drawable
from .explosion import Explosion

if TYPE_CHECKING:
    from .enemy import Enemy
    from ..game_state import GameState
    from ..render_context import RenderContext


class Bullet(Drawable):
    """Represents a bullet fired by the ship."""

    def __init__(self, x: int, game_state: "GameState"):
        """
        Initialize a bullet at ship's firing position.

        Args:
            x: Week position where bullet is fired (0-51)
            game_state: Reference to game state for collision detection and self-removal
        """
        self.x = x
        self.y: float = SHIP_POSITION_Y - 1
        self.game_state = game_state


    def _check_collision(self) -> "Enemy | None":
        """Check if bullet has hit an enemy at its current position."""
        for enemy in self.game_state.enemies:
            if enemy.x == self.x and enemy.y >= self.y:
                return enemy
        return None

    def animate(self, delta_time: float) -> None:
        """Update bullet position, check for collisions, and remove on hit.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        self.y -= BULLET_SPEED * delta_time
        hit_enemy = self._check_collision()
        if hit_enemy:
            explosion = Explosion(self.x, self.y, "small", self.game_state)
            self.game_state.explosions.append(explosion)
            hit_enemy.take_damage()
            self.game_state.bullets.remove(self)
        if self.y < -10:  # magic number to remove off-screen bullets
            self.game_state.bullets.remove(self)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the bullet with trailing tail effect."""

        for i in range(BULLET_TRAILING_LENGTH):
            trail_y = self.y + (i + 1) * BULLET_TRAIL_SPACING
            fade_factor = (i + 1) / BULLET_TRAILING_LENGTH / 2
            self._draw_bullet(draw, context, (self.x, trail_y), fade_factor=fade_factor)

        self._draw_bullet(draw, context, (self.x, self.y), fade_factor=0.3, offset=.6)
        self._draw_bullet(draw, context, (self.x, self.y), fade_factor=0.4, offset=.4)
        self._draw_bullet(draw, context, (self.x, self.y), fade_factor=0.5, offset=.2)
        self._draw_bullet(draw, context, (self.x, self.y))

    def _draw_bullet(
        self,
        draw: ImageDraw.ImageDraw,
        context: "RenderContext",
        position: tuple[float, float],
        fade_factor: float = 1,
        offset: float = 0
    ) -> None:
        x, y = context.get_cell_position(position[0], position[1])
        x += context.cell_size // 2
        y += context.cell_size // 2

        r_x = 0.5 + offset
        r_y = 4 + offset
        draw.rectangle(
            [x - r_x, y - r_y, x + r_x, y + r_y],
            fill=(*context.bullet_color, int(fade_factor * 255)),
        )
