"""Base strategy interface for enemy clearing strategies."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from ..game_state import GameState


@dataclass(frozen=True, slots=True)
class Action:
    """Represents a single action in the game."""
    x: int
    shoot: bool = False

    def __repr__(self) -> str:
        action_type = "SHOOT" if self.shoot else "MOVE"
        return f"Action({action_type} x={self.x})"


class BaseStrategy(ABC):
    """Abstract base class for enemy clearing strategies."""

    def set_rng(self, rng: random.Random) -> None:
        """Inject RNG source for deterministic simulations."""
        del rng

    @abstractmethod
    def generate_actions(self, game_state: "GameState") -> Iterator[Action]:
        """
        Generate sequence of actions for the ship to clear enemies.

        Args:
            game_state: The current game state with enemies, ship, and bullets

        Yields:
            Action objects representing ship movements and shots
        """
        raise NotImplementedError
