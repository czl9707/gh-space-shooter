"""Animator for generating animations from game strategies."""

from typing import Callable, Iterator

from ..github_client import ContributionData
from .game_state import GameState
from .strategies.base_strategy import BaseStrategy
from .simulation_runtime import create_seeded_game_state, derive_simulation_seed


class Animator:
    """Generates animations from game strategies."""

    def __init__(
        self,
        contribution_data: ContributionData,
        strategy: BaseStrategy,
        fps: int,
        watermark: bool = False,
        seed: int | None = None,
        seed_factory: Callable[[ContributionData, BaseStrategy, int], int] = derive_simulation_seed,
        game_state_factory: Callable[[ContributionData, BaseStrategy, int], GameState] = create_seeded_game_state,
    ):
        """
        Initialize animator.

        Args:
            contribution_data: The GitHub contribution data
            strategy: The strategy to use for clearing enemies
            fps: Frames per second for the animation
            watermark: Whether to add watermark to output frames
            seed: Optional deterministic seed for random-driven behavior
            seed_factory: Seed policy callable used when seed is not provided
            game_state_factory: Runtime factory for deterministic GameState setup
        """
        self.contribution_data = contribution_data
        self.strategy = strategy
        self.fps = fps
        self.watermark = watermark
        self.seed_factory = seed_factory
        self.game_state_factory = game_state_factory
        self.seed = seed if seed is not None else self.seed_factory(
            self.contribution_data, self.strategy, self.fps
        )
        self.frame_duration = 1000 // fps
        # Delta time in seconds per frame
        # Used to scale all speeds (cells/second) to per-frame movement
        self.delta_time = 1.0 / fps

    def _create_game_state(self) -> GameState:
        return self.game_state_factory(self.contribution_data, self.strategy, self.seed)

    def iter_state_timeline(
        self, max_frames: int | None = None
    ) -> Iterator[tuple[GameState, int]]:
        """Yield mutable game-state frames with elapsed time in milliseconds."""
        game_state = self._create_game_state()
        yield from self._iter_state_timeline(game_state, max_frames=max_frames)

    def _iter_state_timeline(
        self, game_state: GameState, max_frames: int | None = None
    ) -> Iterator[tuple[GameState, int]]:
        """Yield mutable game-state frames with elapsed time in milliseconds."""
        rendered = 0
        elapsed_ms = 0
        for _ in self._frame_steps(game_state):
            if max_frames is not None and rendered >= max_frames:
                break
            yield game_state, elapsed_ms
            rendered += 1
            elapsed_ms += self.frame_duration

    def _frame_steps(self, game_state: GameState) -> Iterator[None]:
        """
        Generate frame ticks by mutating game state over time.

        Args:
            game_state: The game state
        """
        # Initial frame showing starting state
        yield None

        # Process each action from the strategy
        for action in self.strategy.generate_actions(game_state):
            game_state.ship.move_to(action.x)
            while game_state.can_take_action() is False:
                game_state.animate(self.delta_time)
                yield None

            if action.shoot:
                game_state.shoot()
                game_state.animate(self.delta_time)
                yield None

        force_kill_countdown = 100
        # Final frames showing completion
        while not game_state.is_complete():
            game_state.animate(self.delta_time)
            yield None

            force_kill_countdown -= 1
            if force_kill_countdown <= 0:
                break

        for _ in range(5):
            yield None
