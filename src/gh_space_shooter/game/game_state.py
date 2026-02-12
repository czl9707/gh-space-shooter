"""Game state management for tracking enemies, ship, and bullets."""

import random
from typing import List, Literal, Sequence

from ..constants import SHIP_SHOOT_COOLDOWN
from ..github_client import ContributionData
from .drawables import Bullet, Drawable, Enemy, Explosion, Ship, Starfield


class GameState:
    """Manages the current state of the game."""

    def __init__(self, contribution_data: ContributionData, rng: random.Random | None = None):
        """
        Initialize game state from contribution data.

        Args:
            contribution_data: The GitHub contribution data
        """
        self.rng = rng or random.Random()
        self.starfield = Starfield(rng=self.rng)
        self.ship = Ship(self)
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.explosions: List[Explosion] = []
        self._next_bullet_id = 0
        self._next_explosion_id = 0

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
        bullet = Bullet(
            int(self.ship.x),
            game_state=self,
            bullet_id=self._next_bullet_id,
        )
        self._next_bullet_id += 1
        self.bullets.append(bullet)
        self.ship.shoot_cooldown = SHIP_SHOOT_COOLDOWN

    def create_explosion(self, x: float, y: float, size: Literal["small", "large"]) -> None:
        """Create and register an explosion with a stable ID for timeline encoding."""
        explosion = Explosion(
            x=x,
            y=y,
            size=size,
            game_state=self,
            explosion_id=self._next_explosion_id,
            rng=self.rng,
        )
        self._next_explosion_id += 1
        self.explosions.append(explosion)

    def remove_bullet(self, bullet: Bullet) -> None:
        """Remove bullet if still active in the scene."""
        if bullet in self.bullets:
            self.bullets.remove(bullet)

    def remove_enemy(self, enemy: Enemy) -> None:
        """Remove enemy if still active in the scene."""
        if enemy in self.enemies:
            self.enemies.remove(enemy)

    def remove_explosion(self, explosion: Explosion) -> None:
        """Remove explosion if still active in the scene."""
        if explosion in self.explosions:
            self.explosions.remove(explosion)

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
        self._animate_entities(self.enemies, delta_time)
        self._animate_entities(self.bullets, delta_time)
        self._animate_entities(self.explosions, delta_time)

    def _animate_entities(self, entities: Sequence[Drawable], delta_time: float) -> None:
        """Animate against a stable snapshot to tolerate self-removal during updates."""
        for entity in list(entities):
            entity.animate(delta_time)
