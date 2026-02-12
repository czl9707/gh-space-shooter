"""SVG canvas metadata for timeline generation."""

from ..constants import NUM_WEEKS, SHIP_POSITION_Y
from .game_state import GameState
from .render_context import RenderContext


class SvgRenderer:
    """Provide SVG canvas dimensions derived from render context."""

    def __init__(
        self, game_state: GameState, render_context: RenderContext, watermark: bool = False
    ) -> None:
        self.game_state = game_state
        self.context = render_context
        self.watermark = watermark

        self.grid_width = NUM_WEEKS * (self.context.cell_size + self.context.cell_spacing)
        self.grid_height = SHIP_POSITION_Y * (self.context.cell_size + self.context.cell_spacing)
        self.width = self.grid_width + 2 * self.context.padding
        self.height = self.grid_height + 2 * self.context.padding
