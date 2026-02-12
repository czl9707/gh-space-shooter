"""Game animation module for GitHub contribution visualization."""

from .animator import Animator
from .drawables import Bullet, Drawable, Enemy, Explosion, Ship, Starfield
from .game_state import GameState
from .raster_animation import generate_raster_frames
from .renderer import Renderer
from .svg_animation import generate_svg_timeline_frames
from .svg_renderer import SvgRenderer
from .svg_timeline import (
    BulletFrameState,
    EnemyFrameState,
    ExplosionFrameState,
    StarFrameState,
    SvgTimelineFrame,
)
from .strategies.base_strategy import Action, BaseStrategy
from .strategies.column_strategy import ColumnStrategy
from .strategies.random_strategy import RandomStrategy
from .strategies.row_strategy import RowStrategy

__all__ = [
    "Animator",
    "Bullet",
    "Drawable",
    "Enemy",
    "Explosion",
    "GameState",
    "generate_raster_frames",
    "Renderer",
    "generate_svg_timeline_frames",
    "SvgRenderer",
    "SvgTimelineFrame",
    "StarFrameState",
    "EnemyFrameState",
    "BulletFrameState",
    "ExplosionFrameState",
    "Ship",
    "Starfield",
    "BaseStrategy",
    "Action",
    "ColumnStrategy",
    "RowStrategy",
    "RandomStrategy",
]
