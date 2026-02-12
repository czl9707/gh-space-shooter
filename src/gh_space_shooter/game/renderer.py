"""Renderer for drawing game frames using Pillow."""

from PIL import Image, ImageDraw, ImageFont

from ..constants import NUM_WEEKS, SHIP_POSITION_Y
from .game_state import GameState
from .render_context import RenderContext
from .scene import draw_scene

WATERMARK_TEXT = "by czl9707/gh-space-shooter"


class Renderer:
    """Renders game state as PIL Images."""
    def __init__(self, game_state: GameState, render_context: RenderContext, watermark: bool = False):
        """
        Initialize renderer.

        Args:
            game_state: The game state to render
            render_context: Rendering configuration and theming
            watermark: Whether to add watermark to frames
        """
        self.game_state = game_state
        self.context = render_context
        self.watermark = watermark

        self.grid_width = NUM_WEEKS * (self.context.cell_size + self.context.cell_spacing)
        self.grid_height = SHIP_POSITION_Y * (self.context.cell_size + self.context.cell_spacing)
        self.width = self.grid_width + 2 * self.context.padding
        self.height = self.grid_height + 2 * self.context.padding

    def render_frame(self) -> Image.Image:
        """
        Render the current game state as an image.

        Returns:
            PIL Image of the current frame
        """
        # Create image with background color
        img = Image.new("RGB", (self.width, self.height), self.context.background_color)

        # Draw game state
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        draw_scene(self.game_state, draw, self.context)

        # Draw watermark if enabled
        if self.watermark:
            self._draw_watermark(draw)

        combined = Image.alpha_composite(img.convert("RGBA"), overlay)

        return combined.convert("RGB")

    def _draw_watermark(self, draw: ImageDraw.ImageDraw) -> None:
        """Draw watermark text in the bottom-right corner."""
        font = ImageFont.load_default()
        color = (100, 100, 100, 128)  # Semi-transparent gray
        margin = 5

        # Get text bounding box
        bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position in bottom-right corner
        x = self.width - text_width - margin
        y = self.height - text_height - margin

        draw.text((x, y), WATERMARK_TEXT, font=font, fill=color)
