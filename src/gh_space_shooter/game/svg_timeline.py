"""Timeline frame payloads for object-based SVG animation encoding."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState


@dataclass(frozen=True)
class StarFrameState:
    id: int
    x: float
    y: float
    brightness: float
    size: int


@dataclass(frozen=True)
class EnemyFrameState:
    id: str
    x: int
    y: int
    health: int


@dataclass(frozen=True)
class BulletFrameState:
    id: int
    x: int
    y: float


@dataclass(frozen=True)
class ExplosionFrameState:
    id: int
    x: float
    y: float
    elapsed_time: float
    duration: float
    max_radius: float
    particle_angles: tuple[float, ...]


@dataclass(frozen=True)
class SvgTimelineFrame:
    """A full game-state snapshot at a specific animation time."""

    width: int
    height: int
    time_ms: int
    watermark: bool
    ship_x: float
    stars: tuple[StarFrameState, ...]
    enemies: tuple[EnemyFrameState, ...]
    bullets: tuple[BulletFrameState, ...]
    explosions: tuple[ExplosionFrameState, ...]


def snapshot_svg_timeline_frame(
    game_state: "GameState",
    *,
    width: int,
    height: int,
    time_ms: int,
    watermark: bool,
) -> SvgTimelineFrame:
    """Build an immutable timeline snapshot from the current game state."""
    return SvgTimelineFrame(
        width=width,
        height=height,
        time_ms=time_ms,
        watermark=watermark,
        ship_x=game_state.ship.x,
        stars=_star_states(game_state),
        enemies=_enemy_states(game_state),
        bullets=_bullet_states(game_state),
        explosions=_explosion_states(game_state),
    )


def _star_states(game_state: "GameState") -> tuple[StarFrameState, ...]:
    return tuple(
        StarFrameState(
            id=star["id"],
            x=star["x"],
            y=star["y"],
            brightness=star["brightness"],
            size=star["size"],
        )
        for star in game_state.starfield.stars
    )


def _enemy_states(game_state: "GameState") -> tuple[EnemyFrameState, ...]:
    return tuple(
        EnemyFrameState(
            id=enemy.enemy_id,
            x=enemy.x,
            y=enemy.y,
            health=enemy.health,
        )
        for enemy in game_state.enemies
    )


def _bullet_states(game_state: "GameState") -> tuple[BulletFrameState, ...]:
    return tuple(
        BulletFrameState(
            id=bullet.bullet_id,
            x=bullet.x,
            y=bullet.y,
        )
        for bullet in game_state.bullets
    )


def _explosion_states(game_state: "GameState") -> tuple[ExplosionFrameState, ...]:
    return tuple(
        ExplosionFrameState(
            id=explosion.explosion_id,
            x=explosion.x,
            y=explosion.y,
            elapsed_time=explosion.elapsed_time,
            duration=explosion.duration,
            max_radius=explosion.max_radius,
            particle_angles=tuple(explosion.particle_angles),
        )
        for explosion in game_state.explosions
    )
