"""Tests for Animator."""

from gh_space_shooter.game import Animator, ColumnStrategy, RandomStrategy
from gh_space_shooter.game.raster_animation import generate_raster_frames
from gh_space_shooter.game.svg_animation import (
    generate_svg_timeline_frames,
)
from gh_space_shooter.github_client import ContributionData


# Sample contribution data for testing
SAMPLE_DATA: ContributionData = {
    "username": "testuser",
    "total_contributions": 9,
    "weeks": [
        {
            "days": [
                {"level": 1, "date": "2024-01-01", "count": 1},
                {"level": 0, "date": "2024-01-02", "count": 0},
                {"level": 2, "date": "2024-01-03", "count": 3},
                {"level": 0, "date": "2024-01-04", "count": 0},
                {"level": 0, "date": "2024-01-05", "count": 0},
                {"level": 3, "date": "2024-01-06", "count": 5},
                {"level": 0, "date": "2024-01-07", "count": 0},
            ]
        }
    ],
}


def test_generate_frames_returns_iterator():
    """Raster adapter should return an iterator of PIL Images."""
    strategy = ColumnStrategy()
    animator = Animator(SAMPLE_DATA, strategy, fps=30)

    frames = list(generate_raster_frames(animator))

    assert len(frames) > 0
    assert all(hasattr(f, "save") for f in frames)  # PIL Images have save method


def test_generate_svg_timeline_frames_returns_iterator():
    """generate_svg_timeline_frames should return timeline state snapshots."""
    strategy = ColumnStrategy()
    animator = Animator(SAMPLE_DATA, strategy, fps=30)

    frames = list(generate_svg_timeline_frames(animator))

    assert len(frames) > 0
    assert all(hasattr(f, "ship_x") for f in frames)
    assert all(hasattr(f, "stars") for f in frames)


def test_random_strategy_deterministic_break_sequence():
    """Random strategy should produce stable enemy break sequence for same input."""
    frames_a = list(
        generate_svg_timeline_frames(
            Animator(SAMPLE_DATA, RandomStrategy(), fps=30),
            max_frames=200,
        )
    )
    frames_b = list(
        generate_svg_timeline_frames(
            Animator(SAMPLE_DATA, RandomStrategy(), fps=30),
            max_frames=200,
        )
    )

    signature_a = [
        tuple(sorted((enemy.id, enemy.health) for enemy in frame.enemies)) for frame in frames_a
    ]
    signature_b = [
        tuple(sorted((enemy.id, enemy.health) for enemy in frame.enemies)) for frame in frames_b
    ]

    assert signature_a == signature_b
