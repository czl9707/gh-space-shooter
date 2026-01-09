"""Animator for generating GIF animations from game strategies."""

from typing import Iterator

from PIL import Image


from ..github_client import ContributionData
from .game_state import GameState
from .renderer import Renderer
from .strategies.base_strategy import BaseStrategy
from .render_context import RenderContext


class Animator:
    """Generates animated GIFs from game strategies."""

    def __init__(
        self,
        contribution_data: ContributionData,
        strategy: BaseStrategy,
        fps: int,
    ):
        """
        Initialize animator.

        Args:
            contribution_data: The GitHub contribution data
            strategy: The strategy to use for clearing enemies
            fps: Frames per second for the animation
        """
        self.contribution_data = contribution_data
        self.strategy = strategy
        self.fps = fps
        self.frame_duration = 1000 // fps
        # Delta time in seconds per frame
        # Used to scale all speeds (cells/second) to per-frame movement
        self.delta_time = 1.0 / fps

    def generate_gif(self, output_path: str) -> None:
        """
        Generate animated GIF and save to file.

        Args:
            output_path: Path where GIF should be saved
        """
        # Initialize game state
        game_state = GameState(self.contribution_data)
        renderer = Renderer(game_state, RenderContext.darkmode())

        frames = self._generate_frames(game_state, renderer)

        # Save as GIF
        if frames:
            next(frames).save(
                output_path,
                save_all=True,
                append_images=list(frames),
                duration=self.frame_duration,
                loop=0,  # Loop forever
                optimize=False,
            )

    def _generate_frames(
        self, game_state: GameState, renderer: Renderer
    ) -> Iterator[Image.Image]:
        """
        Generate all animation frames.

        Args:
            game_state: The game state
            renderer: The renderer

        Returns:
            List of PIL Images representing animation frames
        """

        # Add initial frame showing starting state
        yield renderer.render_frame()

        # Process each action from the strategy
        for action in self.strategy.generate_actions(game_state):
            game_state.ship.move_to(action.x)
            while game_state.can_take_action() is False:
                game_state.animate(self.delta_time)
                yield renderer.render_frame()

            if action.shoot:
                game_state.shoot()
                game_state.animate(self.delta_time)
                yield renderer.render_frame()

        force_kill_countdown = 100
        # Add final frames showing completion
        while not game_state.is_complete():
            game_state.animate(self.delta_time)
            yield renderer.render_frame()
            
            force_kill_countdown -= 1
            if force_kill_countdown <= 0:
                break
            
        for _ in range(5):
            yield renderer.render_frame()
