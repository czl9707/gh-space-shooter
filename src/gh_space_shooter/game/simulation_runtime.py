"""Simulation runtime helpers used by Animator."""

import hashlib
import json
import random

from ..github_client import ContributionData
from .game_state import GameState
from .strategies.base_strategy import BaseStrategy


def derive_simulation_seed(
    contribution_data: ContributionData,
    strategy: BaseStrategy,
    fps: int,
) -> int:
    """Create a stable seed based on simulation inputs."""
    payload = {
        "fps": fps,
        "strategy": strategy.__class__.__name__,
        "data": contribution_data,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).digest()
    return int.from_bytes(digest[:8], "big")


def create_seeded_game_state(
    contribution_data: ContributionData,
    strategy: BaseStrategy,
    seed: int,
) -> GameState:
    """Create a game state with deterministic RNG streams for strategy and world state."""
    master_rng = random.Random(seed)
    strategy_rng = random.Random(master_rng.getrandbits(64))
    game_rng = random.Random(master_rng.getrandbits(64))
    strategy.set_rng(strategy_rng)
    return GameState(contribution_data, rng=game_rng)
