"""Game state management for tracking enemies, ship, and bullets."""

from typing import TYPE_CHECKING, List

from PIL import ImageDraw

from ..constants import SHIP_SHOOT_COOLDOWN
from ..github_client import ContributionData
from .drawables import Bullet, Drawable, Enemy, Explosion, Ship, Starfield, Boss, PowerUp # Import PowerUp

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
        self.power_ups: List[PowerUp] = [] # Initialize power_ups list
        self.score = 0 # Initialize game score

        self._initialize_enemies(contribution_data)

    def _initialize_enemies(self, contribution_data: ContributionData):
        """Create enemies based on contribution levels."""
        weeks = contribution_data["weeks"]

        # 1. Identify the boss day (highest contribution level)
        boss_week_idx = -1
        boss_day_idx = -1
        boss_health = 0

        for week_idx, week in enumerate(weeks):
            for day_idx, day in enumerate(week["days"]):
                level = day["level"]
                if level > boss_health:
                    boss_health = level
                    boss_week_idx = week_idx
                    boss_day_idx = day_idx

        # 2. Initialize enemies and the boss
        self.boss = None  # Initialize boss attribute
        for week_idx, week in enumerate(weeks):
            for day_idx, day in enumerate(week["days"]):
                level = day["level"]
                if level <= 0:
                    continue
                
                if week_idx == boss_week_idx and day_idx == boss_day_idx:
                    # This is the boss day, instantiate a Boss object
                    # For now, Boss is just an Enemy with potentially higher health
                    boss_level = max(1, boss_health * 3) # Boss has at least 3x health
                    enemy = Boss(x=week_idx, y=day_idx, health=boss_level, game_state=self)
                    self.boss = enemy # Assign the boss to a dedicated attribute
                else:
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
        for power_up in self.power_ups: # Animate power-ups
            power_up.animate(delta_time)


    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw all game objects including the grid."""
        self.starfield.draw(draw, context)
        for enemy in self.enemies:
            enemy.draw(draw, context)
        for explosion in self.explosions:
            explosion.draw(draw, context)
        for bullet in self.bullets:
            bullet.draw(draw, context)
        for power_up in self.power_ups: # Draw power-ups
            power_up.draw(draw, context)
        self.ship.draw(draw, context)

