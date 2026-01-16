"""Tests for the scoring system."""

import pytest

from gh_space_shooter.game.game_state import GameState
from gh_space_shooter.game.drawables import Enemy, Boss, Bullet # Import Bullet
from gh_space_shooter.github_client import ContributionData # Needed for GameState init
from gh_space_shooter.constants import DEFAULT_FPS # Needed for TEST_DELTA_TIME

TEST_DELTA_TIME = 1.0 / DEFAULT_FPS


class TestScoring:
    """Tests for score initialization and incrementation."""

    @pytest.fixture
    def empty_contribution_data(self) -> ContributionData:
        """Fixture for empty contribution data."""
        return {"total_contributions": 0, "weeks": []}

    def test_score_initialization(self, empty_contribution_data: ContributionData) -> None:
        """Test that the score is initialized to 0."""
        game_state = GameState(empty_contribution_data)
        assert game_state.score == 0

    def test_score_increment_on_enemy_destruction(self, empty_contribution_data: ContributionData) -> None:
        """Test that the score increments when a regular enemy is destroyed by a bullet."""
        game_state = GameState(empty_contribution_data)
        enemy = Enemy(x=0, y=0, health=1, game_state=game_state)
        game_state.enemies.append(enemy) # Ensure enemy is in game_state

        bullet = Bullet(x=enemy.x, game_state=game_state)
        bullet.y = enemy.y + 1 # Position bullet above enemy
        game_state.bullets.append(bullet)

        # Animate bullet until it's removed (collides or goes off-screen)
        while bullet in game_state.bullets:
            bullet.animate(TEST_DELTA_TIME)

        assert game_state.score == 100
        assert enemy not in game_state.enemies # Should be removed

    def test_score_increment_on_boss_destruction(self, empty_contribution_data: ContributionData) -> None:
        """Test that the score increments when the boss is destroyed."""
        game_state = GameState(empty_contribution_data)
        boss = Boss(x=0, y=0, health=1, game_state=game_state)
        game_state.enemies.append(boss) # Ensure boss is in game_state for proper removal

        boss.take_damage()

        assert game_state.score == 1000
        assert boss not in game_state.enemies # Should be removed

    def test_score_not_incremented_if_enemy_not_destroyed(self, empty_contribution_data: ContributionData) -> None:
        """Test that the score is not incremented if an enemy is not destroyed."""
        game_state = GameState(empty_contribution_data)
        enemy = Enemy(x=0, y=0, health=2, game_state=game_state)
        game_state.enemies.append(enemy)

        enemy.take_damage() # Should reduce health to 1, but not destroy

        assert game_state.score == 0
        assert enemy in game_state.enemies # Should still be present

    def test_score_not_incremented_if_boss_not_destroyed(self, empty_contribution_data: ContributionData) -> None:
        """Test that the score is not incremented if the boss is not destroyed."""
        game_state = GameState(empty_contribution_data)
        boss = Boss(x=0, y=0, health=2, game_state=game_state)
        game_state.enemies.append(boss)

        boss.take_damage() # Should reduce health to 1, but not destroy

        assert game_state.score == 0
        assert boss in game_state.enemies # Should still be present
