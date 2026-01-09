"""Game state management for tracking enemies, ship, and bullets."""

from typing import TYPE_CHECKING, List

from PIL import ImageDraw

from ..constants import SHIP_SHOOT_COOLDOWN
from ..github_client import ContributionData
from .drawables import Bullet, Drawable, Enemy, Explosion, Ship, Starfield

if TYPE_CHECKING:
    from .render_context import RenderContext


class GameState(Drawable):
    """Manages the current state of the game."""

    def __init__(self, contribution_data: ContributionData):
        """
        Initialize game state from contribution data.

        Args:
            contribution_data: The GitHub contribution data
        """
        self.starfield = Starfield()
        self.ship = Ship(self)
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.explosions: List[Explosion] = []

        self._initialize_enemies(contribution_data)

    def _initialize_enemies(self, contribution_data: ContributionData):
        """Create enemies based on contribution levels."""
        weeks = contribution_data["weeks"]
        for week_idx, week in enumerate(weeks):
            for day_idx, day in enumerate(week["days"]):
                level = day["level"]
                if level <= 0:
                    continue
                enemy = Enemy(x=week_idx, y=day_idx, health=level, game_state=self)
                self.enemies.append(enemy)

    def shoot(self) -> None:
        """
        Ship shoots a bullet and starts cooldown timer.
        """
        bullet = Bullet(int(self.ship.x), game_state=self)
        self.bullets.append(bullet)
        self.ship.shoot_cooldown = SHIP_SHOOT_COOLDOWN

    def is_complete(self) -> bool:
        """Check if game is complete (all enemies destroyed)."""
        return len(self.enemies) == 0

    def can_take_action(self) -> bool:
        """Check if ship can take an action (not moving and can shoot)."""
        return not self.ship.is_moving() and self.ship.can_shoot()

    def animate(self, delta_time: float) -> None:
        """Update all game objects for next frame.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        self.starfield.animate(delta_time)
        self.ship.animate(delta_time)
        for enemy in self.enemies:
            enemy.animate(delta_time)
        for bullet in self.bullets:
            bullet.animate(delta_time)
        for explosion in self.explosions:
            explosion.animate(delta_time)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw all game objects including the grid."""
        self.starfield.draw(draw, context)
        for enemy in self.enemies:
            enemy.draw(draw, context)
        for explosion in self.explosions:
            explosion.draw(draw, context)
        for bullet in self.bullets:
            bullet.draw(draw, context)
        self.ship.draw(draw, context)
