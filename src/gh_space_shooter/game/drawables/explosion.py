"""Explosion effects for bullet hits and enemy destruction."""

import math
import random
from typing import TYPE_CHECKING, Literal

from PIL import ImageDraw

from ...constants import (
    EXPLOSION_DURATION_LARGE,
    EXPLOSION_DURATION_SMALL,
    EXPLOSION_MAX_RADIUS_LARGE,
    EXPLOSION_MAX_RADIUS_SMALL,
    EXPLOSION_PARTICLE_COUNT_LARGE,
    EXPLOSION_PARTICLE_COUNT_SMALL,
)
from .drawable import Drawable

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..render_context import RenderContext


class Explosion(Drawable):
    """Particle explosion effect that expands and fades out."""

    def __init__(self, x: float, y: float, size: Literal["small", "large"], game_state: "GameState"):
        """
        Initialize an explosion.

        Args:
            x: X position (week, 0-51)
            y: Y position (day, 0-6)
            size: "small" for bullet hits, "large" for enemy destruction
            game_state: Reference to game state for self-removal
        """
        self.x = x
        self.y = y
        self.game_state = game_state
        self.elapsed_time = 0.0  # Seconds elapsed since explosion started
        self.duration = EXPLOSION_DURATION_SMALL if size == "small" else EXPLOSION_DURATION_LARGE
        self.max_radius = EXPLOSION_MAX_RADIUS_SMALL if size == "small" else EXPLOSION_MAX_RADIUS_LARGE
        self.particle_count = EXPLOSION_PARTICLE_COUNT_SMALL if size == "small" else EXPLOSION_PARTICLE_COUNT_LARGE
        self.particle_angles = [random.uniform(0, 2 * math.pi) for _ in range(self.particle_count)]

    def animate(self, delta_time: float) -> None:
        """Progress the explosion animation and remove when complete.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        self.elapsed_time += delta_time
        if self.elapsed_time >= self.duration:
            self.game_state.explosions.remove(self)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw expanding particle explosion with fade effect."""

        progress = self.elapsed_time / self.duration
        fade = 1 - progress  # Fade out as animation progresses

        center_x, center_y = context.get_cell_position(self.x, self.y)
        center_x += context.cell_size // 2
        center_y += context.cell_size // 2

        for i in range(self.particle_count):
            distance = progress * self.max_radius
            angle = self.particle_angles[i]

            px = int(center_x + distance * math.cos(angle))
            py = int(center_y + distance * math.sin(angle))

            # Particle size decreases as it expands
            particle_size = int((1 - progress * 0.5) * 3) + 1

            draw.rectangle(
                [px - particle_size, py - particle_size,
                 px + particle_size, py + particle_size],
                fill=(*context.bullet_color, int(255 * fade))
            )
