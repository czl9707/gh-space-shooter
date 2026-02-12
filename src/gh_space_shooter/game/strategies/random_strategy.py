"""Random strategy: Pick random columns and shoot from bottom up."""

import random
from typing import TYPE_CHECKING, Iterator

from .base_strategy import Action, BaseStrategy

if TYPE_CHECKING:
    from ..drawables.enemy import Enemy
    from ..game_state import GameState


class RandomStrategy(BaseStrategy):
    """
    Ship uses weighted random selection to pick columns based on distance.

    Takes the 8 closest columns and applies distance-based weights for selection,
    creating a balanced mix of efficiency and unpredictability.
    """
    _MAX_CANDIDATE_COLUMNS = 8

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def set_rng(self, rng: random.Random) -> None:
        self._rng = rng

    def generate_actions(self, game_state: "GameState") -> Iterator[Action]:
        """
        Generate actions using weighted random selection based on distance.

        Sorts columns by distance, takes the 8 closest, and applies weights:
        - Distance 0 (same position): weight 10
        - Distance 1-3: weight 100 (highest priority)
        - Distance 4+: weight 1 (lowest priority)

        Args:
            game_state: The current game state with living enemies

        Yields:
            Action objects representing ship movements and shots
        """
        while game_state.enemies:
            candidate_columns = self._candidate_columns(game_state)
            target_column = self._choose_target_column(game_state, candidate_columns)
            target_enemy = self._lowest_enemy_in_column(game_state, target_column)
            yield from self._shoot_column(target_column, shots=target_enemy.health)

    def _candidate_columns(self, game_state: "GameState") -> list[int]:
        columns_with_enemies = {enemy.x for enemy in game_state.enemies}
        ship_x = game_state.ship.x
        columns_by_distance = sorted(columns_with_enemies, key=lambda col: abs(col - ship_x))
        return columns_by_distance[: self._MAX_CANDIDATE_COLUMNS]

    def _choose_target_column(
        self, game_state: "GameState", candidate_columns: list[int]
    ) -> int:
        ship_x = game_state.ship.x
        weights = [self._distance_weight(abs(col - ship_x)) for col in candidate_columns]
        return self._rng.choices(candidate_columns, weights=weights, k=1)[0]

    def _distance_weight(self, distance: float) -> int:
        if distance == 0:
            return 10
        if 1 <= distance <= 3:
            return 100
        return 1

    def _lowest_enemy_in_column(self, game_state: "GameState", target_column: int) -> "Enemy":
        enemies_in_column = [enemy for enemy in game_state.enemies if enemy.x == target_column]
        return max(enemies_in_column, key=lambda enemy: enemy.y)

    def _shoot_column(self, target_column: int, shots: int) -> Iterator[Action]:
        for _ in range(shots):
            yield Action(x=target_column, shoot=True)
