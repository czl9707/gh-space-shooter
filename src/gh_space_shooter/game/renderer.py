"""Renderer for drawing game frames using Pillow."""

from PIL import Image, ImageDraw, ImageFont

from ..constants import NUM_WEEKS, SHIP_POSITION_Y
from .game_state import GameState
from .render_context import RenderContext

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
        self.game_state.draw(draw, self.context)

        # Draw watermark if enabled
        if self.watermark:
            self._draw_watermark(draw)
        
        # Draw score
        self._draw_score(draw)

        combined = Image.alpha_composite(img.convert("RGBA"), overlay)

        return combined.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE)

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

    def _draw_score(self, draw: ImageDraw.ImageDraw) -> None:
        """Draw the current score in the top-left corner."""
        font = ImageFont.load_default()
        color = (255, 255, 255)  # White color
        margin = 5
        score_text = f"Score: {self.game_state.score}"

        # Get text bounding box
        bbox = draw.textbbox((0, 0), score_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position in top-left corner
        x = margin
        y = margin

        draw.text((x, y), score_text, font=font, fill=color)
