"""Scene composition helpers for rendering game state."""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from .drawables import Drawable
from .game_state import GameState

if TYPE_CHECKING:
    from .render_context import RenderContext


def iter_scene_drawables(game_state: GameState) -> Iterator[Drawable]:
    """Yield drawables in painter order from back to front."""
    yield game_state.starfield
    yield from game_state.enemies
    yield from game_state.explosions
    yield from game_state.bullets
    yield game_state.ship


def draw_scene(game_state: GameState, draw: Any, context: "RenderContext") -> None:
    """Render the game state using the provided draw target/context."""
    for drawable in iter_scene_drawables(game_state):
        drawable.draw(draw, context)
