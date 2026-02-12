"""Strategy implementations for enemy clearing."""

from .base_strategy import Action, BaseStrategy
from .column_strategy import ColumnStrategy
from .random_strategy import RandomStrategy
from .row_strategy import RowStrategy

DEFAULT_STRATEGY_NAME = "random"
STRATEGY_TYPES: dict[str, type[BaseStrategy]] = {
    "column": ColumnStrategy,
    "row": RowStrategy,
    "random": RandomStrategy,
}


def supported_strategy_names() -> tuple[str, ...]:
    """Return supported strategy names in deterministic order."""
    return tuple(STRATEGY_TYPES.keys())


def create_strategy(name: str, default: str | None = None) -> BaseStrategy:
    """Create a strategy instance by name."""
    strategy_name = name if name in STRATEGY_TYPES else default
    if strategy_name is None:
        available = ", ".join(supported_strategy_names())
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")

    strategy_class = STRATEGY_TYPES[strategy_name]
    return strategy_class()


__all__ = [
    "BaseStrategy",
    "Action",
    "ColumnStrategy",
    "RowStrategy",
    "RandomStrategy",
    "DEFAULT_STRATEGY_NAME",
    "STRATEGY_TYPES",
    "supported_strategy_names",
    "create_strategy",
]
