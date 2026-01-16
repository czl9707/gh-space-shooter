"""Boss enemy objects."""

from typing import TYPE_CHECKING
from PIL import ImageDraw # Import ImageDraw

from .enemy import Enemy
from .boss_bullet import BossBullet
from .power_up import RapidFirePowerUp # Import RapidFirePowerUp
from ...constants import BOSS_MOVE_SPEED, GAME_GRID_WIDTH, BOSS_SHOOT_INTERVAL


if TYPE_CHECKING:
    from ..game_state import GameState
    from ..render_context import RenderContext


class Boss(Enemy):
    """Represents a boss enemy with unique properties and behaviors."""

    def __init__(self, x: int, y: int, health: int, game_state: "GameState"):
        super().__init__(x, y, health, game_state)
        self.move_speed = BOSS_MOVE_SPEED
        self.direction = 1  # 1 for right, -1 for left
        self.shoot_cooldown = BOSS_SHOOT_INTERVAL
        self.shoot_interval = BOSS_SHOOT_INTERVAL
        self.width_cells = 3 # Boss is 3 cells wide
        self.height_cells = 2 # Boss is 2 cells tall


    def animate(self, delta_time: float) -> None:
        """Update boss state for next frame, including movement and shooting."""
        # Horizontal movement
        self.x += self.move_speed * self.direction * delta_time

        # Boundary checks
        if self.x <= 0:
            self.x = 0
            self.direction = 1  # Move right
        elif self.x >= GAME_GRID_WIDTH - self.width_cells: # Adjust boundary for boss width
            self.x = GAME_GRID_WIDTH - self.width_cells
            self.direction = -1  # Move left
        
        # Shooting logic
        self.shoot_cooldown -= delta_time
        if self.shoot_cooldown <= 0:
            self._shoot()
            self.shoot_cooldown = self.shoot_interval
    
    def _shoot(self) -> None:
        """Boss shoots a spread of bullets."""
        # Create three bullets for a spread shot
        bullet_left = BossBullet(x=self.x + 0.5, y=self.y + self.height_cells - 1, game_state=self.game_state)
        bullet_center = BossBullet(x=self.x + 1.0, y=self.y + self.height_cells - 1, game_state=self.game_state)
        bullet_right = BossBullet(x=self.x + 1.5, y=self.y + self.height_cells - 1, game_state=self.game_state)
        
        self.game_state.bullets.extend([bullet_left, bullet_center, bullet_right])

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the boss at its position with larger size and rounded corners."""
        # Get top-left position of the boss
        x_pixel, y_pixel = context.get_cell_position(self.x, self.y)
        
        # Calculate dimensions for a larger boss (e.g., 3 cells wide, 2 cells tall)
        width_pixel = self.width_cells * context.cell_size
        height_pixel = self.height_cells * context.cell_size
        
        color = context.enemy_colors.get(self.health, context.enemy_colors[1]) # Use health-based color
        
        draw.rounded_rectangle(
            [x_pixel, y_pixel, x_pixel + width_pixel, y_pixel + height_pixel],
            radius=4, # Slightly larger radius for a bigger enemy
            fill=color,
        )

    def take_damage(self) -> None:
        """Boss takes 1 damage and removes itself from game if destroyed, incrementing score."""
        super().take_damage() # Call parent Enemy's take_damage logic
        if self.health <= 0:
            self.game_state.score += 1000 # Increment score for destroyed boss
            # Always drop a power-up when boss is destroyed
            power_up = RapidFirePowerUp(self.x, self.y, self.game_state)
            self.game_state.power_ups.append(power_up)


